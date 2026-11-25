"""Tests for the Borrow Cart and Checkout Flow (Library > Book Catalogue)."""

from datetime import date, timedelta
import json
import pytest
from bs4 import BeautifulSoup
from werkzeug.security import generate_password_hash


@pytest.fixture
def member_client():
    from app import app, get_db
    import secrets
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    rand = secrets.token_hex(4)
    email = f"cart-tester-{rand}@example.com"

    with app.app_context():
        db = get_db()
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=60)).isoformat()

        # Create test member
        user_id = db.execute(
            """INSERT INTO users (name, email, password_hash, phone, address, dob, guardian_verified, is_active)
               VALUES ('Cart Tester', ?, ?, '9876543210', '123 Test St, Chennai', '1995-05-15', 1, 1)""",
            (email, generate_password_hash("test-password-1234"))
        ).lastrowid

        # Create test plan (book_limit = 2)
        plan_id = db.execute(
            """INSERT INTO lending_plans (name, months, duration_days, tier, kind, book_limit, amount, is_active)
               VALUES (?, 2, 60, 'Solo Explorer', 'Regular', 2, 800.0, 1)""",
            (f"Test Solo {rand}",)
        ).lastrowid

        # Create active subscription for member
        sub_id = db.execute(
            """INSERT INTO lending_subscriptions (user_id, plan_id, status, starts_on, expires_on, payment_status, amount, book_limit_snapshot)
               VALUES (?, ?, 'Active', ?, ?, 'Paid - confirmed by staff', 800.0, 2)""",
            (user_id, plan_id, today, future)
        ).lastrowid

        # Create test books: 2 available, 1 out of stock
        b1_id = db.execute(
            """INSERT INTO books (title, author, collection, stock, price, is_active, archived)
               VALUES ('Cart Book Alpha', 'Author Alpha', 'Fiction', 3, 299, 1, 0)"""
        ).lastrowid

        b2_id = db.execute(
            """INSERT INTO books (title, author, collection, stock, price, is_active, archived)
               VALUES ('Cart Book Beta', 'Author Beta', 'Science', 2, 349, 1, 0)"""
        ).lastrowid

        b3_id = db.execute(
            """INSERT INTO books (title, author, collection, stock, price, is_active, archived)
               VALUES ('Cart Book Gamma', 'Author Gamma', 'Art', 5, 199, 1, 0)"""
        ).lastrowid

        b_unavailable_id = db.execute(
            """INSERT INTO books (title, author, collection, stock, price, is_active, archived)
               VALUES ('Cart Book Zero', 'Author Zero', 'Comics', 0, 150, 1, 0)"""
        ).lastrowid

        db.commit()

    yield {
        "user_id": user_id,
        "plan_id": plan_id,
        "sub_id": sub_id,
        "b1": b1_id,
        "b2": b2_id,
        "b3": b3_id,
        "b_zero": b_unavailable_id
    }

    # Teardown
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM notifications17 WHERE user_id=?", (user_id,))
        db.execute("DELETE FROM lending_loans WHERE user_id=?", (user_id,))
        db.execute("DELETE FROM lending_requests WHERE user_id=?", (user_id,))
        db.execute("DELETE FROM lending_subscriptions WHERE user_id=?", (user_id,))
        db.execute("DELETE FROM lending_plans WHERE id=?", (plan_id,))
        db.execute("DELETE FROM books WHERE id IN (?, ?, ?, ?)", (b1_id, b2_id, b3_id, b_unavailable_id))
        db.execute("DELETE FROM users WHERE id=?", (user_id,))
        db.commit()


def get_session_csrf_token(client):
    """Fetch CSRF token from page session."""
    resp = client.get("/library/")
    html = resp.get_data(as_text=True)
    soup = BeautifulSoup(html, "html.parser")
    cfg = soup.select_one("#borrow-cart-config")
    if cfg and cfg.get("data-csrf-token"):
        return cfg["data-csrf-token"]
    hidden = soup.select_one("input[name=csrf_token]")
    if hidden and hidden.get("value"):
        return hidden["value"]
    return client.session_transaction().__enter__().get("csrf_token", "")


def test_checkout_csrf_protection(member_client):
    """POST /library/checkout/ without CSRF token must fail with HTTP 400."""
    from app import app
    with app.test_client() as client:
        with client.session_transaction() as s:
            s["user_id"] = member_client["user_id"]

        resp = client.post(
            "/library/checkout/",
            data=json.dumps({"book_ids": [member_client["b1"]]}),
            content_type="application/json"
        )
        assert resp.status_code == 400


def test_checkout_requires_active_plan(member_client):
    """Users without active subscription or unauthenticated users cannot checkout."""
    from app import app, get_db
    with app.test_client() as client:
        # 1. Unauthenticated request
        resp = client.get("/library/")
        csrf = get_session_csrf_token(client)
        resp = client.post(
            "/library/checkout/",
            data=json.dumps({"book_ids": [member_client["b1"]], "csrf_token": csrf}),
            headers={"X-CSRFToken": csrf},
            content_type="application/json"
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["ok"] is False

        # 2. Authenticated user without active subscription
        with app.app_context():
            db = get_db()
            no_sub_uid = db.execute(
                """INSERT INTO users (name, email, password_hash, dob, is_active)
                   VALUES ('No Sub', 'nosub@test.test', 'pwd', '1990-01-01', 1)"""
            ).lastrowid
            db.commit()

        with client.session_transaction() as s:
            s["user_id"] = no_sub_uid

        resp = client.post(
            "/library/checkout/",
            data=json.dumps({"book_ids": [member_client["b1"]], "csrf_token": csrf}),
            headers={"X-CSRFToken": csrf},
            content_type="application/json"
        )
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["ok"] is False

        with app.app_context():
            db = get_db()
            db.execute("DELETE FROM users WHERE id=?", (no_sub_uid,))
            db.commit()


def test_checkout_enforces_plan_limit(member_client):
    """Borrow cart blocks requesting books beyond remaining plan allowance."""
    from app import app, get_db
    with app.test_client() as client:
        with client.session_transaction() as s:
            s["user_id"] = member_client["user_id"]

        csrf = get_session_csrf_token(client)

        # Plan limit is 2 books. Requesting 3 books must fail with 400.
        payload = {
            "book_ids": [member_client["b1"], member_client["b2"], member_client["b3"]],
            "delivery_mode": "offline",
            "name": "Cart Tester",
            "phone": "9876543210",
            "csrf_token": csrf
        }
        resp = client.post(
            "/library/checkout/",
            data=json.dumps(payload),
            headers={"X-CSRFToken": csrf},
            content_type="application/json"
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert any("allows 2 book" in err for err in data["errors"])

        # Insert 1 active loan already
        with app.app_context():
            db = get_db()
            loan_id = db.execute(
                """INSERT INTO lending_loans (user_id, book_id, subscription_id, status)
                   VALUES (?, ?, ?, 'Requested')""",
                (member_client["user_id"], member_client["b1"], member_client["sub_id"])
            ).lastrowid
            db.commit()

        # Now only 1 slot remains. Trying to request 2 books must fail.
        payload2 = {
            "book_ids": [member_client["b2"], member_client["b3"]],
            "delivery_mode": "offline",
            "name": "Cart Tester",
            "phone": "9876543210",
            "csrf_token": csrf
        }
        resp2 = client.post(
            "/library/checkout/",
            data=json.dumps(payload2),
            headers={"X-CSRFToken": csrf},
            content_type="application/json"
        )
        assert resp2.status_code == 400
        data2 = resp2.get_json()
        assert data2["ok"] is False
        assert any("leaving 1 slot" in err for err in data2["errors"])

        with app.app_context():
            db = get_db()
            db.execute("DELETE FROM lending_loans WHERE id=?", (loan_id,))
            db.commit()


def test_checkout_unavailable_book(member_client):
    """Requesting an out-of-stock / zero copies book fails."""
    from app import app
    with app.test_client() as client:
        with client.session_transaction() as s:
            s["user_id"] = member_client["user_id"]

        csrf = get_session_csrf_token(client)
        payload = {
            "book_ids": [member_client["b_zero"]],
            "delivery_mode": "offline",
            "name": "Cart Tester",
            "phone": "9876543210",
            "csrf_token": csrf
        }
        resp = client.post(
            "/library/checkout/",
            data=json.dumps(payload),
            headers={"X-CSRFToken": csrf},
            content_type="application/json"
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert any("no copies available" in err for err in data["errors"])


def test_checkout_offline_vs_online_delivery_validation(member_client):
    """Offline delivery succeeds without address; Online delivery requires an address."""
    from app import app, get_db
    with app.test_client() as client:
        with client.session_transaction() as s:
            s["user_id"] = member_client["user_id"]

        csrf = get_session_csrf_token(client)

        # 1. Online delivery with empty address fails
        payload_online_invalid = {
            "book_ids": [member_client["b1"]],
            "delivery_mode": "online",
            "address": "",
            "name": "Cart Tester",
            "phone": "9876543210",
            "csrf_token": csrf
        }
        resp = client.post(
            "/library/checkout/",
            data=json.dumps(payload_online_invalid),
            headers={"X-CSRFToken": csrf},
            content_type="application/json"
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["ok"] is False
        assert any("address is required" in err.lower() for err in data["errors"])

        # 2. Offline delivery succeeds without address
        payload_offline = {
            "book_ids": [member_client["b1"]],
            "delivery_mode": "offline",
            "address": "",
            "name": "Cart Tester",
            "phone": "9876543210",
            "csrf_token": csrf
        }
        resp2 = client.post(
            "/library/checkout/",
            data=json.dumps(payload_offline),
            headers={"X-CSRFToken": csrf},
            content_type="application/json"
        )
        assert resp2.status_code == 200
        data2 = resp2.get_json()
        assert data2["ok"] is True
        assert data2["request_id"] > 0

        # Clean up created loan/request
        with app.app_context():
            db = get_db()
            db.execute("DELETE FROM lending_loans WHERE user_id=?", (member_client["user_id"],))
            db.execute("DELETE FROM lending_requests WHERE user_id=?", (member_client["user_id"],))
            db.commit()


def test_checkout_successful_flow_and_duplicate_prevention(member_client):
    """Successful checkout creates request, loans, notification, audit, and prevents duplicates."""
    from app import app, get_db
    with app.test_client() as client:
        with client.session_transaction() as s:
            s["user_id"] = member_client["user_id"]

        csrf = get_session_csrf_token(client)

        # 1. Submitting duplicate book IDs in cart fails
        payload_dup = {
            "book_ids": [member_client["b1"], member_client["b1"]],
            "delivery_mode": "offline",
            "name": "Cart Tester",
            "phone": "9876543210",
            "csrf_token": csrf
        }
        resp_dup = client.post(
            "/library/checkout/",
            data=json.dumps(payload_dup),
            headers={"X-CSRFToken": csrf},
            content_type="application/json"
        )
        assert resp_dup.status_code == 400
        assert resp_dup.get_json()["ok"] is False

        # 2. Valid checkout for 2 books with Online delivery
        payload = {
            "book_ids": [member_client["b1"], member_client["b2"]],
            "delivery_mode": "online",
            "address": "Flat 4B, Lotus Apartments, Saligramam, Chennai",
            "name": "Cart Tester",
            "phone": "9876543210",
            "csrf_token": csrf
        }
        resp = client.post(
            "/library/checkout/",
            data=json.dumps(payload),
            headers={"X-CSRFToken": csrf},
            content_type="application/json"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        request_id = data["request_id"]
        assert "received, we will contact you" in data["message"]

        # Verify DB records
        with app.app_context():
            db = get_db()
            # lending_requests row
            req = db.execute("SELECT * FROM lending_requests WHERE id=?", (request_id,)).fetchone()
            assert req is not None
            assert req["user_id"] == member_client["user_id"]
            assert req["delivery_mode"] == "online"
            assert "Saligramam" in req["delivery_address"]
            assert req["status"] == "Requested"

            # lending_loans rows
            loans = db.execute("SELECT * FROM lending_loans WHERE request_id=?", (request_id,)).fetchall()
            assert len(loans) == 2
            for loan in loans:
                assert loan["status"] == "Requested"
                assert loan["delivery_mode"] == "online"

            # Notifications
            notif = db.execute("SELECT * FROM notifications17 WHERE user_id=? AND dedupe=?", (member_client["user_id"], f"req:{request_id}")).fetchone()
            assert notif is not None

            # Admin notifications
            admin_notif = db.execute("SELECT * FROM admin_notifications WHERE title LIKE ?", (f"%{request_id}%",)).fetchone()
            assert admin_notif is not None

        # 3. Requesting the same book again while active fails
        resp_again = client.post(
            "/library/checkout/",
            data=json.dumps({
                "book_ids": [member_client["b1"]],
                "delivery_mode": "offline",
                "name": "Cart Tester",
                "phone": "9876543210",
                "csrf_token": csrf
            }),
            headers={"X-CSRFToken": csrf},
            content_type="application/json"
        )
        assert resp_again.status_code in (400, 409)
        assert resp_again.get_json()["ok"] is False

        # Clean up
        with app.app_context():
            db = get_db()
            db.execute("DELETE FROM lending_loans WHERE user_id=?", (member_client["user_id"],))
            db.execute("DELETE FROM lending_requests WHERE user_id=?", (member_client["user_id"],))
            db.commit()


def test_catalogue_renders_cart_buttons_and_modal(member_client):
    """Catalogue page contains Add buttons, floating checkout button, modal and config."""
    from app import app
    with app.test_client() as client:
        with client.session_transaction() as s:
            s["user_id"] = member_client["user_id"]

        resp = client.get("/library/")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)

        # Check Add buttons on book cards
        assert "js-cart-btn" in html
        assert "Unavailable" in html  # For book_zero with 0 stock
        # Check floating checkout button
        assert "bb-floating-checkout" in html
        assert "bb-checkout-trigger" in html
        # Check modal
        assert "bb-checkout-modal" in html
        assert "Confirm your request" in html
        assert "bb-modal-items-list" in html
        assert "req-delivery-mode" in html
        assert "delivery-address-group" in html
        assert "borrow-cart-config" in html


def test_admin_grouped_requests_and_batch_actions(member_client):
    """Admin lending desk displays grouped request batches and supports batch actions."""
    from app import app, get_db
    with app.app_context():
        db = get_db()
        admin_id = db.execute(
            "INSERT INTO admin_users (email, name, password_hash, role, is_active) VALUES ('admin_cart@test.test', 'Admin Cart', 'hash', 'super_admin', 1)"
        ).lastrowid
        # Create a batch request with 1 loan
        req_id = db.execute(
            """INSERT INTO lending_requests (user_id, subscription_id, delivery_mode, delivery_address, contact_phone, contact_name, status)
               VALUES (?, ?, 'online', 'Doorstep 123', '9876543210', 'Cart Tester', 'Requested')""",
            (member_client["user_id"], member_client["sub_id"])
        ).lastrowid

        l1 = db.execute(
            """INSERT INTO lending_loans (user_id, book_id, subscription_id, status, request_id, delivery_mode, delivery_address, contact_phone)
               VALUES (?, ?, ?, 'Requested', ?, 'online', 'Doorstep 123', '9876543210')""",
            (member_client["user_id"], member_client["b1"], member_client["sub_id"], req_id)
        ).lastrowid
        db.commit()

    with app.test_client() as client:
        with client.session_transaction() as s:
            s["admin_id"] = admin_id

        resp = client.get("/admin/lending/?status=Requested")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert f"Batch Request #{req_id}" in html
        assert "Doorstep Delivery" in html
        assert "Cart Book Alpha" in html

        # Test batch cancel action
        csrf = get_session_csrf_token(client)
        resp_act = client.post(
            f"/admin/lending/batch-request/{req_id}/",
            data={"action": "cancel", "admin_note": "Test batch cancel", "csrf_token": csrf},
            follow_redirects=True
        )
        assert resp_act.status_code == 200

        with app.app_context():
            db = get_db()
            req = db.execute("SELECT status FROM lending_requests WHERE id=?", (req_id,)).fetchone()
            assert req["status"] == "Cancelled"
            loan = db.execute("SELECT status FROM lending_loans WHERE id=?", (l1,)).fetchone()
            assert loan["status"] == "Cancelled"
            db.execute("DELETE FROM lending_loans WHERE id=?", (l1,))
            db.execute("DELETE FROM lending_requests WHERE id=?", (req_id,))
            db.execute("DELETE FROM admin_users WHERE id=?", (admin_id,))
            db.commit()
