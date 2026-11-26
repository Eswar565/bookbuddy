"""Test suite for Phase 2 /api/v1 REST endpoints."""
from __future__ import annotations

import json
import secrets
import pytest
from backend.app import create_app, db_connection


@pytest.fixture
def app():
    _app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    return _app


@pytest.fixture
def client(app):
    return app.test_client()


def test_csrf_endpoint(client):
    res = client.get("/api/v1/csrf")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "csrf_token" in data["data"]
    assert len(data["data"]["csrf_token"]) > 10


def test_auth_me_guest(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["data"]["authenticated"] is False
    assert data["data"]["user"] is None


def test_auth_signup_login_logout_flow(client):
    import time
    unique_email = f"apitest_{int(time.time()*1000)}@example.com"
    signup_payload = {
        "name": "API Tester",
        "email": unique_email,
        "password": "Password123!",
        "phone": "9876543210"
    }

    # Signup
    res = client.post("/api/v1/auth/signup", json=signup_payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["ok"] is True
    assert data["data"]["user"]["email"] == unique_email

    # Auth me (should now be authenticated in session)
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["data"]["authenticated"] is True
    assert data["data"]["user"]["email"] == unique_email

    # Logout
    res = client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    assert res.get_json()["ok"] is True

    # Auth me again (should be unauthenticated)
    res = client.get("/api/v1/auth/me")
    assert res.get_json()["data"]["authenticated"] is False

    # Login with wrong password
    res = client.post("/api/v1/auth/login", json={"email": unique_email, "password": "WrongPassword"})
    assert res.status_code == 401
    assert res.get_json()["ok"] is False

    # Login with correct password
    res = client.post("/api/v1/auth/login", json={"email": unique_email, "password": "Password123!"})
    assert res.status_code == 200
    assert res.get_json()["ok"] is True
    assert res.get_json()["data"]["user"]["email"] == unique_email


def test_books_listing_and_filter(client):
    res = client.get("/api/v1/books?page=1&page_size=5")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "books" in data["data"]
    assert "filter_options" in data["data"]
    assert len(data["data"]["books"]) <= 5
    assert data["data"]["total_count"] >= 0

    if data["data"]["books"]:
        book_id = data["data"]["books"][0]["id"]
        detail_res = client.get(f"/api/v1/books/{book_id}")
        assert detail_res.status_code == 200
        detail_data = detail_res.get_json()
        assert detail_data["ok"] is True
        assert detail_data["data"]["book"]["id"] == book_id

    # 404 for nonexistent book
    res_404 = client.get("/api/v1/books/99999999")
    assert res_404.status_code == 404
    assert res_404.get_json()["ok"] is False


def test_books_export(client):
    res_xlsx = client.get("/api/v1/books/export/xlsx")
    assert res_xlsx.status_code == 200
    assert "spreadsheet" in res_xlsx.content_type or "octet-stream" in res_xlsx.content_type

    res_pdf = client.get("/api/v1/books/export/pdf")
    assert res_pdf.status_code == 400
    assert "PDF has been removed" in res_pdf.get_json()["error"]["message"]

    res_invalid = client.get("/api/v1/books/export/docx")
    assert res_invalid.status_code == 400


def test_checkout_validation_and_flow(client):
    # 1. Guest checkout -> 401
    res = client.post("/api/v1/checkout", json={"items": [{"id": 1, "title": "Test"}]})
    assert res.status_code == 401

    # 2. Register user without subscription
    import time
    email = f"checkout_test_{int(time.time()*1000)}@example.com"
    client.post("/api/v1/auth/signup", json={
        "name": "Checkout Tester",
        "email": email,
        "password": "Password123!"
    })

    # Checkout without active subscription -> 403
    res = client.post("/api/v1/checkout", json={"items": [{"id": 1, "title": "Test"}]})
    assert res.status_code == 403
    assert res.get_json()["error"]["code"] in ("NO_ACTIVE_PLAN", "NO_ACTIVE_SUBSCRIPTION")

    # 3. Create active subscription for this user in DB
    with db_connection() as conn:
        user_row = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        user_id = user_row[0]
        # Get or insert lending plan
        plan = conn.execute("SELECT id, book_limit FROM lending_plans LIMIT 1").fetchone()
        if not plan:
            conn.execute("INSERT INTO lending_plans (name, book_limit, duration_months, price, is_active) VALUES ('Basic', 2, 1, 300, 1)")
            conn.commit()
            plan = conn.execute("SELECT id, book_limit FROM lending_plans LIMIT 1").fetchone()

        plan_id, book_limit = plan[0], plan[1]
        conn.execute(
            "INSERT INTO lending_subscriptions (user_id, plan_id, starts_on, expires_on, status, book_limit_snapshot) "
            "VALUES (?, ?, '2026-01-01', '2030-01-01', 'Active', ?)",
            (user_id, plan_id, book_limit)
        )
        # Find 1 available book
        book = conn.execute("SELECT id, title, author, available_copies FROM books WHERE archived=0 AND available_copies > 0 LIMIT 1").fetchone()
        conn.commit()

    if book:
        book_id, b_title, b_author, copies = book[0], book[1], book[2], book[3]

        # Valid checkout
        res = client.post("/api/v1/checkout", json={
            "items": [{"id": book_id, "title": b_title, "author": b_author}],
            "delivery_mode": "pickup",
            "notes": "Testing API checkout"
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data["ok"] is True
        assert len(data["data"]["loans"]) == 1

        # Trying to checkout the same book again -> 400 ALREADY_REQUESTED
        res_dup = client.post("/api/v1/checkout", json={
            "items": [{"id": book_id, "title": b_title, "author": b_author}]
        })
        assert res_dup.status_code == 400
        assert res_dup.get_json()["error"]["code"] == "ALREADY_REQUESTED"


def test_memberships_api(client):
    res = client.get("/api/v1/memberships/plans")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "plans" in data["data"]

    # Subscribe as guest -> 401
    res_sub = client.post("/api/v1/memberships/subscribe", json={"plan_id": 1})
    assert res_sub.status_code == 401


def test_events_api(client):
    res = client.get("/api/v1/events")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "events" in data["data"]

    res_cal = client.get("/api/v1/events/calendar")
    assert res_cal.status_code == 200
    cal_data = res_cal.get_json()
    assert cal_data["ok"] is True

    # Detail of nonexistent event -> 404
    res_detail = client.get("/api/v1/events/999999")
    assert res_detail.status_code == 404


def test_gallery_api(client):
    res = client.get("/api/v1/gallery")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "categories" in data["data"]
    assert "settings" in data["data"]

    # Valid category
    res_cat = client.get("/api/v1/gallery/reading-moments")
    assert res_cat.status_code == 200
    cat_data = res_cat.get_json()
    assert cat_data["ok"] is True
    assert cat_data["data"]["category"]["slug"] == "reading-moments"

    # Nonexistent category -> 404
    res_invalid = client.get("/api/v1/gallery/does-not-exist")
    assert res_invalid.status_code == 404


def test_collaborators_api(client):
    res = client.get("/api/v1/collaborators")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "sections" in data["data"]
    assert len(data["data"]["sections"]) == 4

    # Single section
    res_sec = client.get("/api/v1/collaborators/library-partners")
    assert res_sec.status_code == 200
    sec_data = res_sec.get_json()
    assert sec_data["ok"] is True

    # Nonexistent section -> 404
    res_404 = client.get("/api/v1/collaborators/unknown-partner-category")
    assert res_404.status_code == 404


def test_media_api(client):
    res = client.get("/api/v1/media")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "newspapers" in data["data"]
    assert "magazines" in data["data"]
    assert "podcasts" in data["data"]

    # Filter by kind
    res_news = client.get("/api/v1/media?kind=news")
    assert res_news.status_code == 200
    assert res_news.get_json()["data"]["kind"] == "news"


def test_contact_and_contributions_api(client):
    # Missing fields in contact
    res_bad = client.post("/api/v1/contact", json={"name": ""})
    assert res_bad.status_code == 400

    # Valid contact submission
    res_good = client.post("/api/v1/contact", json={
        "name": "Jane Visitor",
        "email": "jane@example.com",
        "subject": "Book Inquiry",
        "message": "Do you have stories by Enid Blyton?"
    })
    assert res_good.status_code == 201
    assert res_good.get_json()["ok"] is True

    # Missing fields in contribution
    res_c_bad = client.post("/api/v1/contributions", json={"student_name": ""})
    assert res_c_bad.status_code == 400

    # Valid contribution submission
    res_c_good = client.post("/api/v1/contributions", json={
        "student_name": "Aarav Reader",
        "email": "aarav@example.com",
        "title": "My Summer Reading Journey",
        "category": "Essay",
        "body": "Reading opened my eyes to whole new worlds..."
    })
    assert res_c_good.status_code == 201
    assert res_c_good.get_json()["ok"] is True


def test_favourites_endpoints(client):
    # 1. Guest request -> ok: True, is_guest: True, empty list
    res_guest = client.get("/api/v1/library/favourites")
    assert res_guest.status_code == 200
    data_guest = res_guest.get_json()["data"]
    assert data_guest["is_guest"] is True
    assert data_guest["book_ids"] == []

    # Guest cannot POST directly without auth
    res_unauth = client.post("/api/v1/library/favourites", json={"book_id": 1})
    assert res_unauth.status_code == 401

    # 2. Register & Login a user
    email = f"fav_user_{secrets.token_hex(4)}@example.com"
    client.post("/api/v1/auth/signup", json={
        "email": email,
        "name": "Favourite Tester",
        "password": "Password123!"
    })

    # Ensure test books exist
    with client.application.app_context():
        from backend.app.db import get_db
        db = get_db()
        cur = db.execute("INSERT INTO books (title, author, archived, available_copies) VALUES ('Fav Book 1', 'Fav Author', 0, 5)")
        book_id = cur.lastrowid
        cur2 = db.execute("INSERT INTO books (title, author, archived, available_copies) VALUES ('Fav Book 2', 'Fav Author 2', 0, 5)")
        other_id = cur2.lastrowid
        db.commit()

    # 3. Add favourite
    res_add = client.post("/api/v1/library/favourites", json={"book_id": book_id})
    assert res_add.status_code == 200
    assert res_add.get_json()["data"]["is_favourite"] is True

    # 4. Check list has book_id
    res_list = client.get("/api/v1/library/favourites")
    assert res_list.status_code == 200
    assert book_id in res_list.get_json()["data"]["book_ids"]

    # 5. Sync multiple favourites
    res_sync = client.post("/api/v1/library/favourites/sync", json={"book_ids": [book_id, other_id]})
    assert res_sync.status_code == 200
    assert other_id in res_sync.get_json()["data"]["book_ids"]

    # 6. Delete favourite
    res_del = client.delete(f"/api/v1/library/favourites/{book_id}")
    assert res_del.status_code == 200
    assert res_del.get_json()["data"]["is_favourite"] is False


def test_catalogue_language_dropdown(client):
    res = client.get("/library/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    # Verify language select element exists
    assert '<select id="top-filter-lang"' in html or 'name="language"' in html
    # Verify no PDF download button
    assert "Download as PDF" not in html
    assert "Download as Excel" in html
    # Verify no Discover your next read
    assert "Discover your next read" not in html
    assert "Discover your next great read" not in html
