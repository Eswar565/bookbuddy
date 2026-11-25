"""Contact inquiries and Reader Contributions API endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from ...db import get_db

contact_bp = Blueprint("api_contact", __name__)


def _get_payload() -> dict:
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()


@contact_bp.post("/contact")
def submit_contact():
    """Submit a general inquiry or contact message."""
    data = _get_payload()
    name = (data.get("name") or data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()
    subject = (data.get("subject") or "Website enquiry").strip()
    phone = (data.get("phone") or "").strip()
    message = (data.get("message") or "").strip()

    if not name:
        return jsonify({
            "ok": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Please provide your name."}
        }), 400

    if not email or "@" not in email:
        return jsonify({
            "ok": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Please provide a valid email address."}
        }), 400

    if not message:
        return jsonify({
            "ok": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Please provide your message."}
        }), 400

    db = get_db()
    db.execute(
        "INSERT INTO contact_submissions (full_name, email, subject, phone, message) VALUES (?, ?, ?, ?, ?)",
        (name, email, subject, phone, message)
    )
    db.commit()

    # Create admin notification if helper exists
    try:
        from ...services.notifications import notify
        notify(
            "New contact enquiry received",
            f"From {name} ({email}) regarding '{subject}'",
            "contact",
            link="/admin/contact/"
        )
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "message": "Your enquiry has been received. Our team will get back to you shortly."
    }), 201


@contact_bp.post("/contributions")
def submit_contribution():
    """Submit a community reader contribution (story, article, review)."""
    data = _get_payload()
    student_name = (data.get("student_name") or data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    title = (data.get("title") or "").strip()
    category = (data.get("category") or "General").strip()
    body = (data.get("body") or data.get("content") or "").strip()

    if not student_name:
        return jsonify({
            "ok": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Please provide author/student name."}
        }), 400

    if not email or "@" not in email:
        return jsonify({
            "ok": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Please provide a valid email address."}
        }), 400

    if not title:
        return jsonify({
            "ok": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Please provide a title for your submission."}
        }), 400

    if not body:
        return jsonify({
            "ok": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Please provide the content of your submission."}
        }), 400

    db = get_db()
    db.execute(
        "INSERT INTO reader_contributions (student_name, email, title, category, body) VALUES (?, ?, ?, ?, ?)",
        (student_name, email, title, category, body)
    )
    db.commit()

    try:
        from ...services.notifications import notify
        notify(
            "New reader contribution submitted",
            f"'{title}' by {student_name} ({category})",
            "publication",
            link="/admin/contributions/"
        )
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "message": "Your contribution has been received for editorial review."
    }), 201
