"""Borrow cart and lending request API endpoints."""
from __future__ import annotations

import json
from datetime import datetime
from flask import Blueprint, jsonify, request, session
from ...db import get_db
from ...services.accounts import get_active_subscription, get_active_loan_count

checkout_bp = Blueprint("api_checkout", __name__)

@checkout_bp.post("/library/checkout")
@checkout_bp.post("/checkout")
def checkout_cart():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "ok": False,
            "error": {
                "code": "AUTHENTICATION_REQUIRED",
                "message": "Please log in to submit your borrowing request."
            }
        }), 401

    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id=? AND is_active=1", (user_id,)).fetchone()
    if not u:
        session.clear()
        return jsonify({
            "ok": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "User account was not found."
            }
        }), 401

    sub = get_active_subscription(db, user_id)
    if not sub:
        return jsonify({
            "ok": False,
            "error": {
                "code": "NO_ACTIVE_PLAN",
                "message": "An active membership subscription is required to borrow books."
            }
        }), 403

    sub_dict = dict(sub)
    plan_limit = int(sub_dict.get("book_limit") or 2)
    active_loans_cnt = get_active_loan_count(db, user_id)
    remaining_slots = max(0, plan_limit - active_loans_cnt)

    data = request.get_json(silent=True) or request.form.to_dict()

    raw_items = data.get("items") or data.get("book_ids") or []
    if isinstance(raw_items, str):
        try:
            raw_items = json.loads(raw_items)
        except Exception:
            raw_items = [i.strip() for i in raw_items.split(",") if i.strip()]

    book_ids = []
    for it in raw_items:
        try:
            if isinstance(it, dict):
                bid = int(it.get("id"))
            else:
                bid = int(it)
            if bid not in book_ids:
                book_ids.append(bid)
        except (ValueError, TypeError):
            continue

    if not book_ids:
        return jsonify({
            "ok": False,
            "error": {
                "code": "EMPTY_CART",
                "message": "Your borrow cart is empty. Please add books from the catalogue."
            }
        }), 400

    if len(book_ids) > remaining_slots:
        return jsonify({
            "ok": False,
            "error": {
                "code": "PLAN_LIMIT_EXCEEDED",
                "message": f"Your plan allows {plan_limit} books at a time. You currently have {active_loans_cnt} active and can borrow at most {remaining_slots} more."
            }
        }), 400

    delivery_mode = (data.get("delivery_mode") or "offline").strip().lower()
    delivery_address = (data.get("delivery_address") or data.get("address") or "").strip()
    contact_number = (data.get("contact_number") or data.get("phone") or u["phone"] or "").strip()
    full_name = (data.get("full_name") or data.get("name") or u["name"] or "").strip()
    notes = (data.get("notes") or "").strip()

    if delivery_mode == "online" and not delivery_address:
        return jsonify({
            "ok": False,
            "error": {
                "code": "MISSING_DELIVERY_ADDRESS",
                "message": "Delivery address is required for doorstep delivery."
            }
        }), 400

    # Validate book stock and avoid duplicate active loans
    placeholders = ",".join("?" for _ in book_ids)
    rows = db.execute(f"SELECT id, title, available_copies FROM books WHERE id IN ({placeholders})", tuple(book_ids)).fetchall()
    book_map = {r["id"]: r for r in rows}

    for bid in book_ids:
        b = book_map.get(bid)
        if not b:
            return jsonify({
                "ok": False,
                "error": {
                    "code": "BOOK_NOT_FOUND",
                    "message": f"Book #{bid} does not exist or has been removed."
                }
            }), 404
        if b["available_copies"] <= 0:
            return jsonify({
                "ok": False,
                "error": {
                    "code": "BOOK_UNAVAILABLE",
                    "message": f"'{b['title']}' is currently out of stock."
                }
            }), 409

    already_loaned = db.execute(
        f"SELECT book_id FROM lending_loans WHERE user_id=? AND book_id IN ({placeholders}) AND status IN ('Requested', 'Issued')",
        tuple([user_id] + book_ids)
    ).fetchall()
    if already_loaned:
        dup_id = already_loaned[0][0]
        dup_title = book_map.get(dup_id, {}).get("title", f"Book #{dup_id}")
        return jsonify({
            "ok": False,
            "error": {
                "code": "DUPLICATE_LOAN",
                "message": f"You already have an active request or loan for '{dup_title}'."
            }
        }), 409

    # Create loans
    loan_ids = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for bid in book_ids:
        cur = db.execute(
            """INSERT INTO lending_loans (user_id, book_id, requested_on, status, delivery_mode, delivery_address, notes)
               VALUES (?, ?, ?, 'Requested', ?, ?, ?)""",
            (user_id, bid, now_str, delivery_mode, delivery_address if delivery_mode == "online" else "", notes)
        )
        loan_ids.append(cur.lastrowid)

    # Record notification for admin
    try:
        db.execute(
            """INSERT INTO admin_notifications (user_id, event_type, message, created_at, is_read)
               VALUES (?, 'borrow_request', ?, ?, 0)""",
            (user_id, f"New borrow request for {len(book_ids)} book(s) by {full_name}", now_str)
        )
    except Exception:
        pass

    db.commit()

    return jsonify({
        "ok": True,
        "message": f"Successfully requested {len(book_ids)} book(s). The library team will prepare your books.",
        "data": {
            "loan_ids": loan_ids,
            "book_ids": book_ids,
            "delivery_mode": delivery_mode,
            "full_name": full_name,
            "contact_number": contact_number,
        }
    }), 201
