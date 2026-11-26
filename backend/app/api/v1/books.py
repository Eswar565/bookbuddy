"""Books and catalogue API endpoints."""
from __future__ import annotations

import math
from flask import Blueprint, jsonify, request, redirect, url_for, session
from ...db import get_db
from ...services.library_filters import (
    get_filtered_books_for_export,
    export_books_excel,
    export_books_pdf,
)


def get_filter_options(db):
    options = {
        key: [r[0] for r in db.execute(f"SELECT DISTINCT {key} FROM books WHERE archived=0 AND TRIM({key})<>'' ORDER BY {key}").fetchall()]
        for key in ["language", "age_group", "author", "product_type"]
    }
    collections = [r[0] for r in db.execute(
        "SELECT DISTINCT collection FROM books WHERE archived=0 AND collection IS NOT NULL AND TRIM(collection)<>'' ORDER BY collection"
    ).fetchall()]
    options["collections"] = collections
    return options

books_bp = Blueprint("api_books", __name__)

@books_bp.get("/books")
def list_books():
    db = get_db()
    args = request.args

    search = args.get("q", "").strip()[:120]
    collection = args.get("collection", "").strip()[:120]
    audience = args.get("audience", "").strip().lower()
    language = args.get("language", "").strip()
    age_group = args.get("age_group", "").strip()
    author = args.get("author", "").strip()
    availability = args.get("availability", "").strip().lower()
    new_only = args.get("new", "").strip()

    try:
        page = max(1, int(args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        page_size = max(1, min(100, int(args.get("page_size", 24))))
    except (ValueError, TypeError):
        page_size = 24

    conditions = ["archived = 0"]
    params = []

    if search:
        conditions.append("(title LIKE ? OR author LIKE ? OR isbn LIKE ?)")
        wild = f"%{search}%"
        params.extend([wild, wild, wild])

    if collection:
        conditions.append("collection = ?")
        params.append(collection)

    if language:
        conditions.append("language = ?")
        params.append(language)

    if age_group:
        conditions.append("age_group = ?")
        params.append(age_group)

    if author:
        conditions.append("author = ?")
        params.append(author)

    if availability == "available":
        conditions.append("available_copies > 0")
    elif availability == "waitlist":
        conditions.append("available_copies = 0")

    if new_only == "1":
        conditions.append("is_new_arrival = 1")

    if audience == "adults":
        conditions.append("LOWER(COALESCE(audience, '')) = 'adults'")
    elif audience == "kids":
        conditions.append("LOWER(COALESCE(audience, '')) != 'adults'")

    where_clause = " WHERE " + " AND ".join(conditions)

    count_row = db.execute(f"SELECT COUNT(*) FROM books{where_clause}", tuple(params)).fetchone()
    total_count = count_row[0] if count_row else 0
    total_pages = max(1, math.ceil(total_count / page_size))

    offset = (page - 1) * page_size
    query = f"""SELECT * FROM books{where_clause}
                ORDER BY is_new_arrival DESC, id DESC
                LIMIT ? OFFSET ?"""
    rows = db.execute(query, tuple(params + [page_size, offset])).fetchall()

    books = [dict(r) for r in rows]

    return jsonify({
        "ok": True,
        "data": {
            "books": books,
            "total_count": total_count,
            "count": len(books),
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "filter_options": get_filter_options(db),
        }
    })

@books_bp.get("/books/<int:book_id>")
def get_book(book_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM books WHERE id=? AND archived=0", (book_id,)).fetchone()
    if not row:
        return jsonify({
            "ok": False,
            "error": {
                "code": "BOOK_NOT_FOUND",
                "message": "Book not found or is no longer available."
            }
        }), 404

    return jsonify({
        "ok": True,
        "data": {
            "book": dict(row)
        }
    })

@books_bp.get("/books/export/<fmt>")
def export_books(fmt: str):
    db = get_db()
    books = get_filtered_books_for_export(db, request.args)
    fmt_lower = fmt.lower()
    if fmt_lower in ("xlsx", "excel"):
        return export_books_excel(books)
    else:
        return jsonify({
            "ok": False,
            "error": {
                "code": "UNSUPPORTED_FORMAT",
                "message": f"Unsupported export format: {fmt}. Download as PDF has been removed. Use 'xlsx'."
            }
        }), 400


@books_bp.get("/library/favourites")
@books_bp.get("/library/favourites/")
@books_bp.get("/books/favourites")
@books_bp.get("/books/favourites/")
def list_favourites():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "ok": True,
            "data": {
                "favourites": [],
                "book_ids": [],
                "count": 0,
                "is_guest": True
            }
        })

    db = get_db()
    rows = db.execute(
        """SELECT b.* FROM books b
           JOIN member_favourites mf ON b.id = mf.book_id
           WHERE mf.user_id = ? AND b.archived = 0
           ORDER BY mf.created_at DESC""",
        (user_id,)
    ).fetchall()

    books = [dict(r) for r in rows]
    book_ids = [b["id"] for b in books]
    return jsonify({
        "ok": True,
        "data": {
            "favourites": books,
            "book_ids": book_ids,
            "count": len(books),
            "is_guest": False
        }
    })


@books_bp.post("/library/favourites")
@books_bp.post("/library/favourites/")
@books_bp.post("/books/favourites")
@books_bp.post("/books/favourites/")
def add_favourite():
    from .csrf import check_csrf_protection
    if not check_csrf_protection(request):
        return jsonify({
            "ok": False,
            "error": {
                "code": "CSRF_FAILED",
                "message": "Invalid or missing CSRF token."
            }
        }), 403

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "ok": False,
            "error": {
                "code": "AUTH_REQUIRED",
                "message": "Please log in to save books to your account favourites."
            }
        }), 401

    payload = request.get_json(silent=True) or request.form.to_dict()
    book_id = payload.get("book_id")
    if not book_id:
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "Missing book_id parameter."
            }
        }), 400

    try:
        book_id = int(book_id)
    except (ValueError, TypeError):
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "Invalid book_id integer."
            }
        }), 400

    db = get_db()
    # Ensure book exists
    book = db.execute("SELECT id FROM books WHERE id=? AND archived=0", (book_id,)).fetchone()
    if not book:
        return jsonify({
            "ok": False,
            "error": {
                "code": "BOOK_NOT_FOUND",
                "message": "Book not found or archived."
            }
        }), 404

    db.execute(
        "INSERT OR IGNORE INTO member_favourites (user_id, book_id) VALUES (?, ?)",
        (user_id, book_id)
    )
    db.commit()

    count = db.execute("SELECT COUNT(*) FROM member_favourites WHERE user_id=?", (user_id,)).fetchone()[0]

    return jsonify({
        "ok": True,
        "data": {
            "book_id": book_id,
            "is_favourite": True,
            "total_favourites": count
        }
    })


@books_bp.delete("/library/favourites/<int:book_id>")
@books_bp.delete("/library/favourites/<int:book_id>/")
@books_bp.delete("/books/favourites/<int:book_id>")
@books_bp.delete("/books/favourites/<int:book_id>/")
def remove_favourite_by_id(book_id: int):
    return _do_remove_favourite(book_id)


@books_bp.delete("/library/favourites")
@books_bp.delete("/library/favourites/")
@books_bp.delete("/books/favourites")
@books_bp.delete("/books/favourites/")
def remove_favourite():
    payload = request.get_json(silent=True) or request.form.to_dict()
    book_id = payload.get("book_id") or request.args.get("book_id")
    if not book_id:
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "Missing book_id parameter."
            }
        }), 400
    try:
        book_id = int(book_id)
    except (ValueError, TypeError):
        return jsonify({
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "Invalid book_id."
            }
        }), 400
    return _do_remove_favourite(book_id)


def _do_remove_favourite(book_id: int):
    from .csrf import check_csrf_protection
    if not check_csrf_protection(request):
        return jsonify({
            "ok": False,
            "error": {
                "code": "CSRF_FAILED",
                "message": "Invalid or missing CSRF token."
            }
        }), 403

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "ok": False,
            "error": {
                "code": "AUTH_REQUIRED",
                "message": "Please log in to manage your favourites."
            }
        }), 401

    db = get_db()
    db.execute("DELETE FROM member_favourites WHERE user_id=? AND book_id=?", (user_id, book_id))
    db.commit()

    count = db.execute("SELECT COUNT(*) FROM member_favourites WHERE user_id=?", (user_id,)).fetchone()[0]

    return jsonify({
        "ok": True,
        "data": {
            "book_id": book_id,
            "is_favourite": False,
            "total_favourites": count
        }
    })


@books_bp.post("/library/favourites/sync")
@books_bp.post("/library/favourites/sync/")
@books_bp.post("/books/favourites/sync")
@books_bp.post("/books/favourites/sync/")
def sync_favourites():
    from .csrf import check_csrf_protection
    if not check_csrf_protection(request):
        return jsonify({
            "ok": False,
            "error": {
                "code": "CSRF_FAILED",
                "message": "Invalid or missing CSRF token."
            }
        }), 403

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "ok": False,
            "error": {
                "code": "AUTH_REQUIRED",
                "message": "Please log in to sync favourites."
            }
        }), 401

    payload = request.get_json(silent=True) or {}
    book_ids = payload.get("book_ids") or []
    db = get_db()

    added = 0
    for bid in book_ids:
        try:
            bid = int(bid)
            db.execute(
                "INSERT OR IGNORE INTO member_favourites (user_id, book_id) VALUES (?, ?)",
                (user_id, bid)
            )
            added += 1
        except (ValueError, TypeError):
            continue
    db.commit()

    rows = db.execute(
        """SELECT b.id FROM books b
           JOIN member_favourites mf ON b.id = mf.book_id
           WHERE mf.user_id = ? AND b.archived = 0""",
        (user_id,)
    ).fetchall()
    all_ids = [r[0] for r in rows]

    return jsonify({
        "ok": True,
        "data": {
            "merged_count": added,
            "book_ids": all_ids,
            "total_favourites": len(all_ids)
        }
    })
