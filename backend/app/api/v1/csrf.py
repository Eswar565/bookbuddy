"""CSRF API endpoints."""
from __future__ import annotations

import secrets
from flask import Blueprint, jsonify, session

csrf_bp = Blueprint("api_csrf", __name__)

@csrf_bp.get("/csrf")
def get_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        session["csrf_token"] = token
    return jsonify({
        "ok": True,
        "data": {
            "csrf_token": token
        },
        "csrf_token": token
    })
