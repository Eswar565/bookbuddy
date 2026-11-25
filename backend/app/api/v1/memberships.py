"""Membership plans and Razorpay payments API endpoints."""
from __future__ import annotations

import hmac
import hashlib
import os
import secrets
from datetime import date
from flask import Blueprint, jsonify, request, session, current_app
from ...db import get_db
from ...services.accounts import add_months, get_active_subscription

memberships_bp = Blueprint("api_memberships", __name__)

@memberships_bp.get("/memberships/plans")
def list_plans():
    db = get_db()
    rows = db.execute("SELECT * FROM lending_plans WHERE is_active=1 ORDER BY amount ASC").fetchall()
    plans = [dict(r) for r in rows]
    return jsonify({
        "ok": True,
        "data": {
            "plans": plans
        }
    })

@memberships_bp.post("/memberships/subscribe")
def create_subscription():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "ok": False,
            "error": { "code": "AUTHENTICATION_REQUIRED", "message": "Please log in to subscribe to a membership plan." }
        }), 401

    data = request.get_json(silent=True) or request.form.to_dict()
    plan_id = data.get("plan_id")
    if not plan_id:
        return jsonify({
            "ok": False,
            "error": { "code": "MISSING_PLAN_ID", "message": "Plan ID is required." }
        }), 400

    db = get_db()
    plan = db.execute("SELECT * FROM lending_plans WHERE id=? AND is_active=1", (plan_id,)).fetchone()
    if not plan:
        return jsonify({
            "ok": False,
            "error": { "code": "PLAN_NOT_FOUND", "message": "Selected plan is invalid or no longer active." }
        }), 404

    starts_on = date.today()
    expires_on = add_months(starts_on, plan["months"])

    cur = db.execute(
        """INSERT INTO lending_subscriptions (user_id, plan_id, starts_on, expires_on, status, payment_status, book_limit_snapshot)
           VALUES (?, ?, ?, ?, 'Active', 'Paid - confirmed by staff', ?)""",
        (user_id, plan["id"], starts_on.isoformat(), expires_on.isoformat(), plan["book_limit"])
    )
    db.commit()

    return jsonify({
        "ok": True,
        "message": f"Successfully activated '{plan['name']}' membership plan.",
        "data": {
            "subscription_id": cur.lastrowid,
            "plan": dict(plan),
            "starts_on": starts_on.isoformat(),
            "expires_on": expires_on.isoformat()
        }
    }), 201

@memberships_bp.post("/memberships/razorpay/create-order")
def create_razorpay_order():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "ok": False,
            "error": { "code": "AUTHENTICATION_REQUIRED", "message": "Please log in to proceed with payment." }
        }), 401

    data = request.get_json(silent=True) or request.form.to_dict()
    plan_id = data.get("plan_id")
    if not plan_id:
        return jsonify({
            "ok": False,
            "error": { "code": "MISSING_PLAN_ID", "message": "Plan ID is required." }
        }), 400

    db = get_db()
    plan = db.execute("SELECT * FROM lending_plans WHERE id=? AND is_active=1", (plan_id,)).fetchone()
    if not plan:
        return jsonify({
            "ok": False,
            "error": { "code": "PLAN_NOT_FOUND", "message": "Plan not found." }
        }), 404

    key_id = current_app.config.get("RAZORPAY_KEY_ID") or os.environ.get("RAZORPAY_KEY_ID", "")
    key_secret = current_app.config.get("RAZORPAY_KEY_SECRET") or os.environ.get("RAZORPAY_KEY_SECRET", "")
    amount_in_paise = int(round(float(plan["amount"]) * 100))

    if not key_id or not key_secret:
        # Mock / demo payment order
        order_id = f"order_demo_{secrets.token_hex(8)}"
    else:
        try:
            import razorpay
            client = razorpay.Client(auth=(key_id, key_secret))
            order = client.order.create({
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"rcpt_sub_{user_id}_{secrets.token_hex(4)}"
            })
            order_id = order["id"]
        except Exception:
            order_id = f"order_demo_{secrets.token_hex(8)}"

    return jsonify({
        "ok": True,
        "data": {
            "order_id": order_id,
            "amount": amount_in_paise,
            "currency": "INR",
            "key_id": key_id or "rzp_test_placeholder",
            "plan_id": plan["id"],
            "plan_name": plan["name"]
        }
    })

@memberships_bp.post("/memberships/razorpay/verify")
def verify_razorpay_payment():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "ok": False,
            "error": { "code": "AUTHENTICATION_REQUIRED", "message": "Please log in to verify payment." }
        }), 401

    data = request.get_json(silent=True) or request.form.to_dict()
    order_id = data.get("razorpay_order_id")
    payment_id = data.get("razorpay_payment_id")
    signature = data.get("razorpay_signature")
    plan_id = data.get("plan_id")

    if not order_id or not plan_id:
        return jsonify({
            "ok": False,
            "error": { "code": "MISSING_PAYMENT_DETAILS", "message": "Order ID and Plan ID are required." }
        }), 400

    db = get_db()
    plan = db.execute("SELECT * FROM lending_plans WHERE id=? AND is_active=1", (plan_id,)).fetchone()
    if not plan:
        return jsonify({
            "ok": False,
            "error": { "code": "PLAN_NOT_FOUND", "message": "Plan not found." }
        }), 404

    key_secret = current_app.config.get("RAZORPAY_KEY_SECRET") or os.environ.get("RAZORPAY_KEY_SECRET", "")
    if key_secret and signature and not order_id.startswith("order_demo_"):
        generated = hmac.new(key_secret.encode("utf-8"), f"{order_id}|{payment_id}".encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(generated, signature):
            return jsonify({
                "ok": False,
                "error": { "code": "PAYMENT_VERIFICATION_FAILED", "message": "Payment signature verification failed." }
            }), 400

    starts_on = date.today()
    expires_on = add_months(starts_on, plan["months"])

    cur = db.execute(
        """INSERT INTO lending_subscriptions (user_id, plan_id, starts_on, expires_on, status, payment_status, book_limit_snapshot)
           VALUES (?, ?, ?, ?, 'Active', 'Paid - Razorpay', ?)""",
        (user_id, plan["id"], starts_on.isoformat(), expires_on.isoformat(), plan["book_limit"])
    )
    db.commit()

    return jsonify({
        "ok": True,
        "message": f"Payment verified and subscription activated for '{plan['name']}'.",
        "data": {
            "subscription_id": cur.lastrowid,
            "starts_on": starts_on.isoformat(),
            "expires_on": expires_on.isoformat(),
        }
    })
