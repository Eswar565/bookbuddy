"""Collaborators and Partners API endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from ...db import get_db

collaborators_bp = Blueprint("api_collaborators", __name__)

CATEGORY_DEFINITIONS = [
    {
        "slug": "library-partners",
        "title": "Library Partners",
        "description": "Other libraries and book communities collaborating to share the joy of reading.",
    },
    {
        "slug": "storytellers-authors",
        "title": "Storytellers & Authors",
        "description": "Authors, narrators, writers, and educators who bring stories to life.",
    },
    {
        "slug": "community-partners",
        "title": "Community Partners",
        "description": "Organisations, schools, and local initiatives building community connections.",
    },
    {
        "slug": "creative-partners",
        "title": "Creative Partners",
        "description": "Artists, illustrators, and workshop facilitators sparking creative curiosity.",
    },
]


@collaborators_bp.get("/collaborators")
def get_collaborators():
    """Retrieve all collaborator categories with their active partners."""
    db = get_db()
    sections = []

    for cd in CATEGORY_DEFINITIONS:
        rows = db.execute(
            "SELECT id, name, category, brief, image, link, sort_order, is_active "
            "FROM collaborators WHERE is_active = 1 AND category = ? "
            "ORDER BY sort_order ASC, id ASC",
            (cd["slug"],),
        ).fetchall()

        partners = [dict(r) for r in rows]
        sections.append({
            "slug": cd["slug"],
            "title": cd["title"],
            "description": cd["description"],
            "count": len(partners),
            "partners": partners,
        })

    return jsonify({
        "ok": True,
        "data": {
            "sections": sections,
        }
    })


@collaborators_bp.get("/collaborators/<category_slug>")
def get_collaborator_category(category_slug: str):
    """Retrieve partners for a single category."""
    cd = next((c for c in CATEGORY_DEFINITIONS if c["slug"] == category_slug), None)
    if not cd:
        return jsonify({
            "ok": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"Category '{category_slug}' not found"
            }
        }), 404

    db = get_db()
    rows = db.execute(
        "SELECT id, name, category, brief, image, link, sort_order, is_active "
        "FROM collaborators WHERE is_active = 1 AND category = ? "
        "ORDER BY sort_order ASC, id ASC",
        (category_slug,),
    ).fetchall()

    partners = [dict(r) for r in rows]
    return jsonify({
        "ok": True,
        "data": {
            "category": cd,
            "count": len(partners),
            "partners": partners,
        }
    })


@collaborators_bp.post("/partners")
def submit_partner_proposal():
    data = request.get_json(silent=True) or request.form.to_dict()
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    organisation = (data.get("organisation") or "").strip()
    proposal_type = (data.get("proposal_type") or "Other").strip()
    message = (data.get("message") or "").strip()

    if not full_name or not email or not message:
        return jsonify({
            "ok": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Full name, email, and message are required."
            }
        }), 400

    db = get_db()
    db.execute(
        "INSERT INTO partner_submissions (full_name, email, phone, organisation, proposal_type, message, status) VALUES (?, ?, ?, ?, ?, ?, 'New')",
        (full_name, email, phone, organisation, proposal_type, message)
    )
    db.commit()

    return jsonify({
        "ok": True,
        "data": {
            "message": "Partnership proposal submitted successfully."
        }
    }), 201
