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
        for key in ["age_group", "author", "product_type"]
    }
    from ...services.languages import get_distinct_languages
    distinct_langs = get_distinct_languages(db)
    options["language"] = distinct_langs
    options["languages"] = distinct_langs
    collections = [r[0] for r in db.execute(
        "SELECT DISTINCT collection FROM books WHERE archived=0 AND collection IS NOT NULL AND TRIM(collection)<>'' ORDER BY collection"
    ).fetchall()]
    options["collections"] = collections
    options["categories"] = [
        "Baby", "Toddler", "Junior", "Middle Grade", "Young Adults", "Adults", "Fiction", "Non Fiction", "Languages"
    ]
    options["sort_options"] = [
        {"value": "newest", "label": "Newest"},
        {"value": "az", "label": "A–Z"},
        {"value": "za", "label": "Z–A"}
    ]
    return options

books_bp = Blueprint("api_books", __name__)

@books_bp.get("/books")
def list_books():
    db = get_db()
    args = request.args

    search = args.get("q", "").strip()[:120]
    category = args.get("category", "").strip()[:120]
    collection = args.get("collection", "").strip()[:120]
    audience = args.get("audience", "").strip().lower()
    lang = args.get("lang", "").strip()[:120] or args.get("language", "").strip()[:120]
    if lang.lower() == "all":
        lang = ""
    age_group = args.get("age_group", "").strip()
    author = args.get("author", "").strip()
    availability = args.get("availability", "").strip().lower()
    new_only = args.get("new", "").strip()
    sort = args.get("sort", "newest").strip().lower()

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
        conditions.append("(title LIKE ? OR author LIKE ? OR isbn LIKE ? OR description LIKE ?)")
        wild = f"%{search}%"
        params.extend([wild, wild, wild, wild])

    if category and category.lower() != "all":
        cat_lower = category.lower()
        if cat_lower == "baby":
            conditions.append("(LOWER(category) LIKE '%baby%' OR age_group IN ('0-2', '0-3', 'Baby'))")
        elif cat_lower == "toddler":
            conditions.append("(LOWER(category) LIKE '%toddler%' OR age_group IN ('3-5', '2-4', 'Toddler'))")
        elif cat_lower == "junior":
            conditions.append("(LOWER(category) LIKE '%junior%' OR age_group IN ('5', '6-8', 'Junior'))")
        elif cat_lower == "middle grade":
            conditions.append("(LOWER(category) LIKE '%middle grade%' OR LOWER(category) LIKE '%middle-grade%' OR age_group IN ('9-12', 'Middle Grade'))")
        elif cat_lower == "young adults":
            conditions.append("(LOWER(category) LIKE '%young adult%' OR age_group IN ('12+', '13-18', 'Young Adults'))")
        elif cat_lower == "adults":
            conditions.append("(LOWER(category) LIKE '%adult%' OR LOWER(audience) IN ('adult', 'adults'))")
        elif cat_lower == "fiction":
            conditions.append("(LOWER(category) LIKE '%fiction%' AND LOWER(category) NOT LIKE '%non-fiction%' AND LOWER(category) NOT LIKE '%non fiction%' OR collection IN ('Picture Books', 'Chapter Books', 'Adventure', 'Classics', 'Sci-Fi', 'Fantasy', 'Folktales', 'Story') OR product_type = 'fiction')")
        elif cat_lower in ("non fiction", "non-fiction"):
            conditions.append("(LOWER(category) LIKE '%non fiction%' OR LOWER(category) LIKE '%non-fiction%' OR collection IN ('Non-Fiction', 'Non Fiction', 'AI') OR product_type = 'non-fiction')")
        elif cat_lower == "languages":
            if not lang:
                conditions.append("books.id IN (SELECT book_id FROM book_languages WHERE language IS NOT NULL AND TRIM(language) <> '')")
        else:
            conditions.append("(LOWER(category) LIKE ? OR LOWER(collection) LIKE ?)")
            params.extend([f"%{cat_lower}%", f"%{cat_lower}%"])

    if lang:
        conditions.append("books.id IN (SELECT book_id FROM book_languages WHERE LOWER(language) = LOWER(?))")
        params.append(lang)

    if collection:
        conditions.append("collection = ?")
        params.append(collection)

    if age_group:
        conditions.append("age_group = ?")
        params.append(age_group)

    if author:
        conditions.append("author = ?")
        params.append(author)

    try:
        from book_availability import get_availability_sql_filter
    except ImportError:
        from app.services.book_availability import get_availability_sql_filter

    avail_filter = get_availability_sql_filter(availability)
    if avail_filter:
        conditions.append(avail_filter)

    if new_only == "1":
        conditions.append("is_new_arrival = 1")

    if audience in ("adult", "adults"):
        conditions.append("LOWER(COALESCE(audience, '')) IN ('adult', 'adults', 'all')")
    elif audience == "kids":
        conditions.append("LOWER(COALESCE(audience, '')) IN ('kids', 'all')")

    if sort in ('az', 'title'):
        order_by = "title COLLATE NOCASE ASC, id ASC"
    elif sort == 'za':
        order_by = "title COLLATE NOCASE DESC, id DESC"
    else:
        order_by = "is_new_arrival DESC, id DESC"

    where_clause = " WHERE " + " AND ".join(conditions)

    count_row = db.execute(f"SELECT COUNT(*) FROM books{where_clause}", tuple(params)).fetchone()
    total_count = count_row[0] if count_row else 0
    total_pages = max(1, math.ceil(total_count / page_size))

    offset = (page - 1) * page_size
    query = f"""SELECT * FROM books{where_clause}
                ORDER BY {order_by}
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
    db = get_db()

    # If ids parameter is provided (e.g. from guest's localStorage), query those books directly
    ids_param = request.args.get("ids", "").strip() or request.args.get("book_ids", "").strip()
    if ids_param:
        try:
            ids = [int(x.strip()) for x in ids_param.split(",") if x.strip()]
        except (ValueError, TypeError):
            ids = []
        if ids:
            placeholders = ",".join(["?"] * len(ids))
            rows = db.execute(
                f"SELECT * FROM books WHERE id IN ({placeholders}) AND archived = 0",
                ids
            ).fetchall()
            books = [dict(r) for r in rows]
            fav_avail = request.args.get("availability", "").strip().lower()
            if fav_avail == "available":
                books = [b for b in books if (b.get("available_copies") if b.get("available_copies") is not None else b.get("stock") or 0) > 0]
            elif fav_avail in ("unavailable", "waitlist"):
                books = [b for b in books if (b.get("available_copies") if b.get("available_copies") is not None else b.get("stock") or 0) <= 0]
            return jsonify({
                "ok": True,
                "data": {
                    "favourites": books,
                    "book_ids": [b["id"] for b in books],
                    "count": len(books),
                    "is_guest": not bool(user_id)
                }
            })

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

    rows = db.execute(
        """SELECT b.* FROM books b
           JOIN member_favourites mf ON b.id = mf.book_id
           WHERE mf.user_id = ? AND b.archived = 0
           ORDER BY mf.created_at DESC""",
        (user_id,)
    ).fetchall()

    books = [dict(r) for r in rows]
    fav_avail = request.args.get("availability", "").strip().lower()
    if fav_avail == "available":
        books = [b for b in books if (b.get("available_copies") if b.get("available_copies") is not None else b.get("stock") or 0) > 0]
    elif fav_avail in ("unavailable", "waitlist"):
        books = [b for b in books if (b.get("available_copies") if b.get("available_copies") is not None else b.get("stock") or 0) <= 0]
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
