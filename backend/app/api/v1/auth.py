"""Authentication and session API endpoints."""
from __future__ import annotations

import secrets
from datetime import date
from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from ...db import get_db
from ...services.accounts import get_active_subscription, get_active_loan_count, years_old

auth_bp = Blueprint("api_auth", __name__)

def _user_dict(row):
    if not row:
        return None
    d = dict(row)
    d.pop("password_hash", None)
    d["is_authenticated"] = True
    d["age"] = years_old(d.get("dob"))
    return d

@auth_bp.get("/auth/me")
def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "ok": True,
            "data": {
                "authenticated": False,
                "user": None,
                "active_subscription": None,
                "active_loans_count": 0
            }
        })

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id=? AND is_active=1", (user_id,)).fetchone()
    if not row:
        session.pop("user_id", None)
        return jsonify({
            "ok": True,
            "data": {
                "authenticated": False,
                "user": None,
                "active_subscription": None,
                "active_loans_count": 0
            }
        })

    sub_row = get_active_subscription(db, user_id)
    loans_count = get_active_loan_count(db, user_id)
    return jsonify({
        "ok": True,
        "data": {
            "authenticated": True,
            "user": _user_dict(row),
            "active_subscription": dict(sub_row) if sub_row else None,
            "active_loans_count": loans_count
        }
    })

@auth_bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or request.form.to_dict()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({
            "ok": False,
            "error": {
                "code": "MISSING_CREDENTIALS",
                "message": "Email and password are required."
            }
        }), 400

    db = get_db()
    u = db.execute("SELECT * FROM users WHERE email=? AND is_active=1", (email,)).fetchone()
    if not u or not check_password_hash(u["password_hash"], password):
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "Email or password not recognised."
            }
        }), 401

    session.clear()
    session["user_id"] = u["id"]
    if not session.get("csrf_token"):
        session["csrf_token"] = secrets.token_hex(32)

    sub_row = get_active_subscription(db, u["id"])
    loans_count = get_active_loan_count(db, u["id"])

    return jsonify({
        "ok": True,
        "message": "Login successful",
        "data": {
            "user": _user_dict(u),
            "active_subscription": dict(sub_row) if sub_row else None,
            "active_loans_count": loans_count
        }
    })

@auth_bp.post("/auth/signup")
def signup():
    data = request.get_json(silent=True) or request.form.to_dict()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip()
    address = (data.get("address") or "").strip()
    dob = (data.get("dob") or "").strip()
    member_role = (data.get("member_role") or "student").strip()
    education_level = (data.get("education_level") or "school").strip()
    grade = (data.get("grade_at_joining") or "").strip()
    guardian_name = (data.get("guardian_name") or "").strip()
    guardian_email = (data.get("guardian_email") or "").strip().lower()

    if not name or not email or not password:
        return jsonify({
            "ok": False,
            "error": {
                "code": "MISSING_REQUIRED_FIELDS",
                "message": "Name, email, and password are required."
            }
        }), 400

    if len(password) < 6:
        return jsonify({
            "ok": False,
            "error": {
                "code": "PASSWORD_TOO_SHORT",
                "message": "Password must be at least 6 characters long."
            }
        }), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        return jsonify({
            "ok": False,
            "error": {
                "code": "EMAIL_ALREADY_EXISTS",
                "message": "An account with this email address already exists."
            }
        }), 409

    pwd_hash = generate_password_hash(password)
    cur = db.execute(
        """INSERT INTO users (name, email, password_hash, phone, address, dob, member_role,
           education_level, grade_at_joining, guardian_name, guardian_email, is_active)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (name, email, pwd_hash, phone, address, dob, member_role, education_level, grade, guardian_name, guardian_email)
    )
    db.commit()
    new_id = cur.lastrowid

    session.clear()
    session["user_id"] = new_id
    session["csrf_token"] = secrets.token_hex(32)

    new_user = db.execute("SELECT * FROM users WHERE id=?", (new_id,)).fetchone()

    return jsonify({
        "ok": True,
        "message": "Account created successfully",
        "data": {
            "user": _user_dict(new_user),
            "active_subscription": None,
            "active_loans_count": 0
        }
    }), 201

@auth_bp.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({
        "ok": True,
        "message": "Logged out successfully"
    })

@auth_bp.post("/auth/forgot-password")
def forgot_password():
    data = request.get_json(silent=True) or request.form.to_dict()
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({
            "ok": False,
            "error": { "code": "MISSING_EMAIL", "message": "Email is required." }
        }), 400

    # In production/demo: confirm receipt without exposing account existence
    return jsonify({
        "ok": True,
        "message": "If an account exists with this email, password reset instructions have been sent."
    })
