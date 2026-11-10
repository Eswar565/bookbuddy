import os
import uuid
import hashlib
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media")).resolve()
THUMBNAIL_DIR = os.path.join(str(MEDIA_ROOT), "thumbnails", "gallery")
UPLOAD_DIR = os.path.join(str(MEDIA_ROOT), "admin", "gallery")

os.makedirs(THUMBNAIL_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


def resolve_disk_path(image_path: str) -> str:
    """Resolve a web image path (/media/..., /static/..., etc.) to an absolute filesystem path."""
    if not image_path or image_path.startswith("http"):
        return ""
    clean = image_path.strip()
    if clean.startswith("/media/"):
        return str((MEDIA_ROOT / clean[7:]).resolve())
    elif clean.startswith("media/"):
        return str((MEDIA_ROOT / clean[6:]).resolve())
    else:
        return str((BASE_DIR / clean.lstrip("/")).resolve())


def ensure_thumbnail(image_path: str) -> str:
    """Generate and cache an optimized WebP thumbnail (~800px wide).
    Returns web path for the thumbnail (e.g. /media/thumbnails/gallery/abc.webp).
    """
    if not image_path or image_path.startswith("http"):
        return image_path

    disk_path = resolve_disk_path(image_path)
    if not disk_path or not os.path.exists(disk_path):
        return ""

    # Generate stable filename based on source path and modification time
    try:
        mtime = os.path.getmtime(disk_path)
        h = hashlib.sha1(f"{image_path}:{mtime}".encode()).hexdigest()[:16]
        thumb_filename = f"thumb_{h}.webp"
        thumb_disk_path = os.path.join(THUMBNAIL_DIR, thumb_filename)
        thumb_web_path = f"/media/thumbnails/gallery/{thumb_filename}"

        if os.path.exists(thumb_disk_path):
            return thumb_web_path

        with Image.open(disk_path) as img:
            # Convert RGBA / P to RGB if needed for saving
            if img.mode in ("RGBA", "LA"):
                # preserve alpha if needed or save with webp transparency
                pass
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Max width 800px preserving aspect ratio
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            img.save(thumb_disk_path, "WEBP", quality=82)

        return thumb_web_path
    except Exception as e:
        print(f"Error generating thumbnail for {image_path}: {e}")
        return image_path


get_or_create_thumbnail = ensure_thumbnail


def get_gallery_settings(db) -> dict:
    rows = db().execute(
        "SELECT content_key, content_value FROM site_content WHERE content_key IN ('gallery_pill', 'gallery_heading')"
    ).fetchall()
    settings = {r[0]: r[1] for r in rows}
    return {
        "gallery_pill": (settings.get("gallery_pill") or "").strip() or "Our Gallery",
        "gallery_heading": (settings.get("gallery_heading") or "").strip() or "Capturing Moments, Creating Memories",
    }


def save_gallery_settings(db, pill: str, heading: str):
    pill = (pill or "").strip() or "Our Gallery"
    heading = (heading or "").strip() or "Capturing Moments, Creating Memories"
    c = db()
    c.execute(
        "INSERT INTO site_content (content_key, content_value) VALUES ('gallery_pill', ?) ON CONFLICT(content_key) DO UPDATE SET content_value=excluded.content_value",
        (pill,),
    )
    c.execute(
        "INSERT INTO site_content (content_key, content_value) VALUES ('gallery_heading', ?) ON CONFLICT(content_key) DO UPDATE SET content_value=excluded.content_value",
        (heading,),
    )
    c.commit()


def get_public_gallery(db) -> tuple[dict, list[dict]]:
    """Returns (settings, items) where every item has an existing file on disk and optimized thumbnail."""
    settings = get_gallery_settings(db)
    rows = db().execute(
        "SELECT id, image_path, alt_text, position, is_active FROM gallery_items WHERE (is_active=1 OR is_active IS NULL) ORDER BY position, id"
    ).fetchall()

    valid_items = []
    for r in rows:
        gid, img_path, alt_text, pos, active = r
        if not img_path:
            continue
        disk_path = resolve_disk_path(img_path)
        if not img_path.startswith("http") and (not disk_path or not os.path.exists(disk_path)):
            # Broken image file - exclude from public view!
            continue

        thumb = ensure_thumbnail(img_path)
        valid_items.append({
            "id": gid,
            "full_path": img_path if img_path.startswith(("/", "http")) else "/" + img_path,
            "thumbnail_path": thumb or img_path,
            "alt_text": alt_text or f"Book Buddy gallery photo {gid}",
            "position": pos,
        })

    return settings, valid_items


def get_admin_gallery(db) -> tuple[dict, list[dict]]:
    """Returns (settings, items) with file_exists, test_data hints, and thumbnails for admin manager."""
    settings = get_gallery_settings(db)
    rows = db().execute(
        "SELECT id, title, description, image_path, alt_text, position, is_active FROM gallery_items ORDER BY position, id"
    ).fetchall()

    items = []
    for r in rows:
        gid, title, desc, img_path, alt_text, pos, active = r
        disk_path = resolve_disk_path(img_path) if img_path else ""
        exists = os.path.exists(disk_path) if img_path and not img_path.startswith("http") else bool(img_path)
        
        test_reasons = []
        if not exists:
            test_reasons.append("Missing File")
        if (title or "").lower().strip() in ["demo", "demo1", "test"]:
            test_reasons.append(f"Title: {title}")
        
        is_test = bool(test_reasons)
        thumb = ensure_thumbnail(img_path) if exists else ""

        items.append({
            "id": gid,
            "title": title or "",
            "description": desc or "",
            "image_path": img_path,
            "thumbnail_path": thumb or img_path,
            "alt_text": alt_text or "",
            "position": pos,
            "is_active": bool(active),
            "file_exists": exists,
            "is_test_data": is_test,
            "test_hint": ", ".join(test_reasons),
        })

    return settings, items


def add_gallery_photos(db, file_storages) -> list[str]:
    """Saves multiple uploaded photos, validates them, creates thumbnails and DB records.
    Returns list of error messages (if any).
    """
    errors = []
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}
    max_size = 15 * 1024 * 1024  # 15 MB

    c = db()
    # Find current max position
    cur_pos = c.execute("SELECT COALESCE(MAX(position), 0) FROM gallery_items").fetchone()[0]

    for f in file_storages:
        if not f or not f.filename:
            continue
        name = f.filename.strip()
        _, ext = os.path.splitext(name.lower())
        if ext not in allowed_exts:
            errors.append(f"'{name}': Unsupported file format. Please upload JPG, PNG, or WebP.")
            continue

        try:
            # Check file size
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(0)
            if size > max_size:
                errors.append(f"'{name}': File is too large ({size // (1024*1024)}MB). Maximum is 15MB.")
                continue

            # Verify image integrity with Pillow
            with Image.open(f) as img:
                img.verify()
                width, height = img.size
                if width < 50 or height < 50:
                    errors.append(f"'{name}': Image dimensions are too small ({width}x{height}).")
                    continue
            f.seek(0)

            # Save file
            new_id = uuid.uuid4().hex[:16]
            saved_filename = f"{new_id}{ext}"
            saved_disk_path = os.path.join(UPLOAD_DIR, saved_filename)
            f.save(saved_disk_path)
            web_path = f"/media/admin/gallery/{saved_filename}"

            # Generate thumbnail
            thumb_path = ensure_thumbnail(web_path)

            cur_pos += 1
            # Clean title from filename for internal DB constraint
            base_title = os.path.splitext(name)[0].replace("-", " ").replace("_", " ").title()
            default_alt = f"Book Buddy gallery photo - {base_title}"

            c.execute(
                "INSERT INTO gallery_items (title, description, image_path, alt_text, page_slug, position, is_active, thumbnail_path) VALUES (?, '', ?, ?, 'all', ?, 1, ?)",
                (base_title, web_path, default_alt, cur_pos, thumb_path),
            )
        except Exception as e:
            errors.append(f"'{name}': Failed to process image ({e}).")

    c.commit()
    return errors


def reorder_gallery(db, ordered_ids: list[int]):
    c = db()
    for idx, gid in enumerate(ordered_ids):
        c.execute("UPDATE gallery_items SET position = ? WHERE id = ?", (idx, gid))
    c.commit()


def toggle_gallery_active(db, gid: int) -> bool:
    c = db()
    row = c.execute("SELECT is_active FROM gallery_items WHERE id = ?", (gid,)).fetchone()
    if not row:
        return False
    new_state = 0 if row[0] else 1
    c.execute("UPDATE gallery_items SET is_active = ? WHERE id = ?", (new_state, gid))
    c.commit()
    return True


def delete_gallery_item(db, gid: int) -> bool:
    c = db()
    c.execute("DELETE FROM gallery_items WHERE id = ?", (gid,))
    c.commit()
    return True


def update_gallery_item_alt(db, gid: int, alt_text: str):
    c = db()
    c.execute("UPDATE gallery_items SET alt_text = ? WHERE id = ?", (alt_text.strip(), gid))
    c.commit()
