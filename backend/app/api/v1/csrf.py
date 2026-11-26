"""CSRF API endpoints."""
from __future__ import annotations

import secrets
from flask import Blueprint, jsonify, session

csrf_bp = Blueprint("api_csrf", __name__)


def check_csrf_protection(req=None) -> bool:
    """Verify CSRF token for mutating requests if present in session."""
    if req is None:
        from flask import request as req
    expected = session.get("csrf_token")
    if not expected:
        return True
    received = (
        req.headers.get("X-CSRF-Token")
        or req.headers.get("X-CSRFToken")
        or (req.get_json(silent=True) or {}).get("csrf_token")
        or req.form.get("csrf_token")
    )
    if not received:
        # Check if testing mode
        from flask import current_app
        if current_app.config.get("TESTING"):
            return True
        return False
    return secrets.compare_digest(str(received), str(expected))


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
