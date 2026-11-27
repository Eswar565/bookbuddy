"""Visit Us page and admin editor for Book Buddy."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from flask import (
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

# Canonical Defaults
DEFAULT_EYEBROW = "GET IN TOUCH"
DEFAULT_HEADING = "Plan Your Visit"
DEFAULT_SUBTITLE = "Step into our library and explore a world of books, learning, and community. We can't wait to welcome you."
DEFAULT_CONTACT_HEADING = "Contact Details"
DEFAULT_CARD_LIBRARY_TITLE = "Our Library"
DEFAULT_CARD_PHONE_TITLE = "Phone / WhatsApp"
DEFAULT_CARD_EMAIL_TITLE = "Email Us"
DEFAULT_CARD_DIRECTIONS_TITLE = "Get Directions"
DEFAULT_DIRECTIONS_HELPER = "Enter your starting location for exact routing."
DEFAULT_DIRECTIONS_PLACEHOLDER = "E.g., T Nagar, Chennai"
DEFAULT_DIRECTIONS_BTN = "Go"

DEFAULT_ADDRESS = "1, Thiruvalluvar St, Thiru Nagar Colony, Gandhi Nagar,\nSaligramam, Chennai, Tamil Nadu 600093"
DEFAULT_LAT = "13.0544"
DEFAULT_LNG = "80.1983"
DEFAULT_PHONE = "+91 9080759312"
DEFAULT_EMAIL = "bookbuddy.edu@gmail.com"
DEFAULT_WHATSAPP = "+91 9080759312"
DEFAULT_MAPS_URL = "https://www.google.com/maps/search/?api=1&query=1%2C+Thiruvalluvar+St%2C+Thiru+Nagar+Colony%2C+Gandhi+Nagar%2C+Saligramam%2C+Chennai%2C+Tamil+Nadu+600093"

DEFAULT_TOUR_EYEBROW = "Library Tour"
DEFAULT_TOUR_HEADING = "A Glimpse Inside Book Buddy"
DEFAULT_TOUR_SUBTITLE = "Explore our warm, engaging spaces designed to spark reading curiosity."

TOUR_PHOTOS = [
    {"src": "/static/img/gallery/kids_1.jpg", "alt": "Children browsing shelves at Book Buddy"},
    {"src": "/static/img/gallery/kids_2.jpg", "alt": "Students reading together at the study desk"},
    {"src": "/static/img/gallery/kids_3.jpg", "alt": "Storytelling and picture book section"},
    {"src": "/static/img/gallery/kids_4.jpg", "alt": "Curated novel and non-fiction collection"},
    {"src": "/static/img/gallery/kids_5.jpg", "alt": "Young readers exploring illustrated classics"},
    {"src": "/static/img/gallery/kids_6.jpg", "alt": "Weekend reading circle and workshop area"},
    {"src": "/static/img/gallery/kids_7.jpg", "alt": "Quiet reading nooks for comfortable study"},
    {"src": "/static/img/gallery/kids_8.jpg", "alt": "Library reception and circulation desk"},
]


def clean_phone_for_whatsapp(raw: str) -> str:
    """Extract digits for wa.me link."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10 and not digits.startswith("91"):
        digits = "91" + digits
    return digits


def get_visit_us_data(db_conn) -> dict[str, Any]:
    """Retrieve all Visit Us page configuration from site_content."""
    cur = db_conn.cursor()
    rows = cur.execute("SELECT content_key, content_value FROM site_content").fetchall()
    content = {r[0]: r[1] for r in rows}

    address = content.get("contact_address") or DEFAULT_ADDRESS
    phone = content.get("contact_phone") or DEFAULT_PHONE
    email = content.get("contact_email") or DEFAULT_EMAIL
    whatsapp = content.get("contact_whatsapp") or phone or DEFAULT_WHATSAPP
    whatsapp_digits = clean_phone_for_whatsapp(whatsapp)

    # Normalize and cleanly encode destination for maps
    clean_address = re.sub(r"\s+", " ", address).strip()
    encoded_dest = quote(clean_address)
    
    lat = content.get("visit_lat", "").strip() or DEFAULT_LAT
    lng = content.get("visit_lng", "").strip() or DEFAULT_LNG

    # Custom URLs if provided, otherwise auto-generate keyless embed and search URLs
    embed_url = content.get("visit_map_embed_url", "").strip()
    if not embed_url:
        if lat and lng:
            embed_url = f"https://www.google.com/maps?q={lat},{lng}&z=16&output=embed"
        else:
            embed_url = f"https://www.google.com/maps?q={encoded_dest}&z=16&output=embed"
    elif "z=" not in embed_url:
        embed_url += "&z=16" if "?" in embed_url else "?z=16"

    maps_url = content.get("visit_maps_url", "").strip()
    if not maps_url:
        maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_dest}"

    directions_dest = clean_address

    return {
        "eyebrow": content.get("visit_eyebrow") or DEFAULT_EYEBROW,
        "heading": content.get("visit_heading") or DEFAULT_HEADING,
        "subtitle": content.get("visit_subtitle") or DEFAULT_SUBTITLE,
        "contact_heading": content.get("visit_contact_heading") or DEFAULT_CONTACT_HEADING,
        "card_library_title": content.get("visit_card_library_title") or DEFAULT_CARD_LIBRARY_TITLE,
        "card_phone_title": content.get("visit_card_phone_title") or DEFAULT_CARD_PHONE_TITLE,
        "card_email_title": content.get("visit_card_email_title") or DEFAULT_CARD_EMAIL_TITLE,
        "card_directions_title": content.get("visit_card_directions_title") or DEFAULT_CARD_DIRECTIONS_TITLE,
        "directions_helper": content.get("visit_directions_helper") or DEFAULT_DIRECTIONS_HELPER,
        "directions_placeholder": content.get("visit_directions_placeholder") or DEFAULT_DIRECTIONS_PLACEHOLDER,
        "directions_btn": content.get("visit_directions_btn") or DEFAULT_DIRECTIONS_BTN,
        "address": address,
        "clean_address": clean_address,
        "phone": phone,
        "email": email,
        "whatsapp": whatsapp,
        "whatsapp_digits": whatsapp_digits,
        "embed_url": embed_url,
        "maps_url": maps_url,
        "directions_dest": directions_dest,
        "encoded_dest": encoded_dest,
        "lat": lat,
        "lng": lng,
        "tour_eyebrow": content.get("tour_eyebrow") or DEFAULT_TOUR_EYEBROW,
        "tour_heading": content.get("tour_heading") or DEFAULT_TOUR_HEADING,
        "tour_subtitle": content.get("tour_subtitle") or DEFAULT_TOUR_SUBTITLE,
        "tour_photos": TOUR_PHOTOS,
    }


def install_visit_us(app, get_db, current_admin, render_site):
    """Register public /visit-us/ route and admin editor."""

    # 1. Ensure schema and defaults are populated
    with app.app_context():
        db = get_db()
        defaults = {
            "contact_address": DEFAULT_ADDRESS,
            "contact_phone": DEFAULT_PHONE,
            "contact_email": DEFAULT_EMAIL,
            "contact_whatsapp": DEFAULT_WHATSAPP,
            "visit_lat": DEFAULT_LAT,
            "visit_lng": DEFAULT_LNG,
            "visit_eyebrow": DEFAULT_EYEBROW,
            "visit_heading": DEFAULT_HEADING,
            "visit_subtitle": DEFAULT_SUBTITLE,
            "visit_contact_heading": DEFAULT_CONTACT_HEADING,
            "visit_card_library_title": DEFAULT_CARD_LIBRARY_TITLE,
            "visit_card_phone_title": DEFAULT_CARD_PHONE_TITLE,
            "visit_card_email_title": DEFAULT_CARD_EMAIL_TITLE,
            "visit_card_directions_title": DEFAULT_CARD_DIRECTIONS_TITLE,
            "visit_directions_helper": DEFAULT_DIRECTIONS_HELPER,
            "visit_directions_placeholder": DEFAULT_DIRECTIONS_PLACEHOLDER,
            "visit_directions_btn": DEFAULT_DIRECTIONS_BTN,
            "tour_eyebrow": DEFAULT_TOUR_EYEBROW,
            "tour_heading": DEFAULT_TOUR_HEADING,
            "tour_subtitle": DEFAULT_TOUR_SUBTITLE,
        }
        for key, val in defaults.items():
            db.execute("INSERT OR IGNORE INTO site_content (content_key, content_value) VALUES (?, ?)", (key, val))
        
        # Ensure the user's specific address is active
        db.execute(
            "UPDATE site_content SET content_value=? WHERE content_key='contact_address' AND (content_value LIKE '%Madurai%' OR content_value LIKE '%MK Complex%' OR content_value = '')",
            (DEFAULT_ADDRESS,)
        )
        db.execute(
            "UPDATE site_content SET content_value=? WHERE content_key='visit_lat' AND (content_value = '' OR content_value IS NULL)",
            (DEFAULT_LAT,)
        )
        db.execute(
            "UPDATE site_content SET content_value=? WHERE content_key='visit_lng' AND (content_value = '' OR content_value IS NULL)",
            (DEFAULT_LNG,)
        )
        db.commit()

    # 2. Public Route (assign to existing visit_us_page endpoint)
    def visit_us_route() -> Response:
        db = get_db()
        visit_data = get_visit_us_data(db)
        return render_site(
            "visit_us",
            "library",
            visit=visit_data,
            page_title="Visit Us | Book Buddy Library",
        )

    app.view_functions["visit_us_page"] = visit_us_route

    # 3. Admin Editor Route
    @app.route("/admin/visit-us-editor/", methods=["GET", "POST"])
    def admin_visit_us_editor():
        if not current_admin():
            return redirect(url_for("admin_login", next=request.path))

        db = get_db()

        if request.method == "POST":
            # Save all fields into site_content
            fields = [
                "contact_address",
                "contact_phone",
                "contact_email",
                "contact_whatsapp",
                "visit_eyebrow",
                "visit_heading",
                "visit_subtitle",
                "visit_contact_heading",
                "visit_card_library_title",
                "visit_card_phone_title",
                "visit_card_email_title",
                "visit_card_directions_title",
                "visit_directions_helper",
                "visit_directions_placeholder",
                "visit_directions_btn",
                "visit_map_embed_url",
                "visit_maps_url",
                "visit_lat",
                "visit_lng",
                "tour_eyebrow",
                "tour_heading",
                "tour_subtitle",
            ]
            for f in fields:
                val = request.form.get(f, "").strip()
                # Address preserves line breaks as submitted
                if f == "contact_address":
                    val = request.form.get(f, "").strip()
                db.execute(
                    "INSERT INTO site_content (content_key, content_value) VALUES (?, ?) ON CONFLICT(content_key) DO UPDATE SET content_value=excluded.content_value",
                    (f, val),
                )
            db.commit()
            flash("Visit Us page settings saved successfully.", "success")
            return redirect("/admin/visit-us-editor/")

        visit_data = get_visit_us_data(db)
        return render_template(
            "workspace/visit_us_editor.html",
            visit=visit_data,
            title="Visit Us Page Editor",
            active="visit_us",
            admin=current_admin(),
        )
