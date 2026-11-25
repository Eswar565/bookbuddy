"""Gallery API endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify
from ...db import get_db
from ...services import gallery_service

gallery_bp = Blueprint("api_gallery", __name__)


@gallery_bp.get("/gallery")
def get_gallery():
    """Retrieve gallery categories, preview images, and settings."""
    db = get_db
    settings, all_items = gallery_service.get_public_gallery(db)
    categories = list(gallery_service.GALLERY_CATEGORIES.values())

    # Attach preview count or photos to each category
    categories_data = []
    for cat in categories:
        slug = cat["slug"]
        cat_photos = [item for item in all_items if item.get("category") == slug]
        if not cat_photos and slug in gallery_service.DEFAULT_CATEGORY_PHOTOS:
            cat_photos = gallery_service.DEFAULT_CATEGORY_PHOTOS[slug]
        categories_data.append({
            **cat,
            "photo_count": len(cat_photos),
            "preview_photos": cat_photos[:3],
        })

    return jsonify({
        "ok": True,
        "data": {
            "settings": settings,
            "categories": categories_data,
        }
    })


@gallery_bp.get("/gallery/<slug>")
def get_gallery_category(slug: str):
    """Retrieve photos and metadata for a specific gallery category."""
    cat = gallery_service.GALLERY_CATEGORIES.get(slug)
    if not cat:
        return jsonify({
            "ok": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"Gallery category '{slug}' not found"
            }
        }), 404

    photos = gallery_service.get_category_photos(get_db, slug)
    return jsonify({
        "ok": True,
        "data": {
            "category": cat,
            "photos": photos,
        }
    })
