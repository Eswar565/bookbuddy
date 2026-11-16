"""How to Borrow page, Book Inquiry & Request management, and admin editor for Book Buddy."""
from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import datetime
from functools import wraps
from urllib.parse import quote

from flask import (
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# Safe defaults matching user specification
DEFAULT_HEADING = "How to Borrow a Book"
DEFAULT_FORM_TITLE = "Book Inquiry & Request Form"
DEFAULT_SUCCESS_MSG = "Thank you! We received your request and will notify you."
DEFAULT_MEM_HELPER = "Valid Membership ID or registered phone/email"

DEFAULT_BLOCKS = [
    {
        "heading": "Borrowing Process",
        "body": "Our library makes it easy for members to access thousands of titles. Simply browse the catalogue, check for availability, and present your Membership ID at the circulation desk for a quick checkout.",
        "checklist": "",
        "position": 1,
        "is_active": 1,
    },
    {
        "heading": "Borrowing Rules",
        "body": "To ensure a fair experience for all readers, please keep the following guidelines in mind:",
        "checklist": "Standard borrowing period is 14 days (2 weeks).\nBooks can be renewed once if there are no pending reservations.\nMembership ID card is mandatory for every exchange.\nPlease check for any existing damages before leaving the desk.\nLate returns incur a fee as per your membership agreement.",
        "position": 2,
        "is_active": 1,
    },
    {
        "heading": "Can't Find a Book?",
        "body": "If a specific title is not available in our current catalogue, you can use the request form to the right. Our procurement team will review your request and notify you once the book is added to our shelves.",
        "checklist": "Request specific authors or new releases.\nGet notified immediately via email upon arrival.",
        "position": 3,
        "is_active": 1,
    },
]

VALID_STATUSES = ["New", "Reviewing", "Ordered", "Available", "Declined"]


def parse_checklist(raw: str) -> list[str]:
    """Parse newline-separated checklist items into a list of non-empty strings."""
    if not raw:
        return []
    lines = [line.strip() for line in raw.splitlines()]
    return [line for line in lines if line]


def get_ip_hash(ip: str | None) -> str:
    """Return anonymized IP hash for rate limiting."""
    val = (ip or "127.0.0.1").encode("utf-8")
    return hashlib.sha256(val).hexdigest()[:16]


def install_how_to_borrow(app, get_db, current_admin, render_site=None):
    """Register database tables, routes, and admin editors for How to Borrow."""

    with app.app_context():
        conn = get_db()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS how_to_borrow_page (
                id INTEGER PRIMARY KEY DEFAULT 1,
                page_heading TEXT NOT NULL DEFAULT 'How to Borrow a Book',
                form_enabled INTEGER NOT NULL DEFAULT 1,
                form_title TEXT NOT NULL DEFAULT 'Book Inquiry & Request Form',
                membership_id_label TEXT NOT NULL DEFAULT 'Membership ID',
                membership_id_placeholder TEXT NOT NULL DEFAULT 'e.g. LIB-2026-001',
                membership_id_helper TEXT NOT NULL DEFAULT 'Valid Membership ID or registered phone/email',
                book_title_label TEXT NOT NULL DEFAULT 'Book Title / Topic',
                book_title_placeholder TEXT NOT NULL DEFAULT 'Enter book name or subject',
                author_label TEXT NOT NULL DEFAULT 'Author Name (If Known)',
                author_placeholder TEXT NOT NULL DEFAULT 'e.g. J.K. Rowling',
                language_label TEXT NOT NULL DEFAULT 'Preferred Language',
                languages TEXT NOT NULL DEFAULT 'English\nTamil\nHindi\nOther',
                notes_label TEXT NOT NULL DEFAULT 'Additional Notes / Specific Edition',
                notes_placeholder TEXT NOT NULL DEFAULT 'Mention if you need a specific edition or have other queries...',
                consent_text TEXT NOT NULL DEFAULT 'I agree to be notified via email/phone regarding this request.',
                button_label TEXT NOT NULL DEFAULT 'Submit Inquiry',
                success_message TEXT NOT NULL DEFAULT 'Thank you! We received your request and will notify you.'
            );

            CREATE TABLE IF NOT EXISTS how_to_borrow_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                heading TEXT NOT NULL,
                body TEXT NOT NULL,
                checklist TEXT NOT NULL DEFAULT '',
                position INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS book_inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                membership_id TEXT DEFAULT '',
                contact_info TEXT DEFAULT '',
                book_title TEXT NOT NULL,
                author TEXT DEFAULT '',
                language TEXT DEFAULT 'English',
                notes TEXT DEFAULT '',
                consent INTEGER NOT NULL DEFAULT 1,
                user_id INTEGER,
                member_name TEXT DEFAULT '',
                member_email TEXT DEFAULT '',
                member_phone TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'New',
                admin_notes TEXT DEFAULT '',
                ip_hash TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Seed page config if missing
        existing_cfg = conn.execute("SELECT id FROM how_to_borrow_page WHERE id=1").fetchone()
        if not existing_cfg:
            conn.execute(
                """
                INSERT INTO how_to_borrow_page (id, page_heading, form_enabled, form_title,
                    membership_id_label, membership_id_placeholder, membership_id_helper,
                    book_title_label, book_title_placeholder, author_label, author_placeholder,
                    language_label, languages, notes_label, notes_placeholder, consent_text,
                    button_label, success_message)
                VALUES (1, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    DEFAULT_HEADING,
                    DEFAULT_FORM_TITLE,
                    "Membership ID",
                    "e.g. LIB-2026-001",
                    DEFAULT_MEM_HELPER,
                    "Book Title / Topic",
                    "Enter book name or subject",
                    "Author Name (If Known)",
                    "e.g. J.K. Rowling",
                    "Preferred Language",
                    "English\nTamil\nHindi\nOther",
                    "Additional Notes / Specific Edition",
                    "Mention if you need a specific edition or have other queries...",
                    "I agree to be notified via email/phone regarding this request.",
                    "Submit Inquiry",
                    DEFAULT_SUCCESS_MSG,
                ),
            )

        # Seed default blocks if table is empty
        block_count = conn.execute("SELECT COUNT(*) FROM how_to_borrow_blocks").fetchone()[0]
        if block_count == 0:
            for b in DEFAULT_BLOCKS:
                conn.execute(
                    "INSERT INTO how_to_borrow_blocks (heading, body, checklist, position, is_active) VALUES (?, ?, ?, ?, ?)",
                    (b["heading"], b["body"], b["checklist"], b["position"], b["is_active"]),
                )

        # Create trigger for admin notification if app_flags table exists
        try:
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS notify10_book_inquiries AFTER INSERT ON book_inquiries
                WHEN (SELECT value FROM app_flags WHERE key='notifications_enabled')='1'
                BEGIN
                    INSERT OR IGNORE INTO admin_notifications(kind,title,body,url,source_key)
                    VALUES (
                        'library',
                        'New book inquiry',
                        NEW.book_title || ' · ' || COALESCE(NULLIF(NEW.member_name,''), NULLIF(NEW.contact_info,''), NULLIF(NEW.membership_id,''), 'Visitor'),
                        '/admin/book-inquiries/' || NEW.id || '/',
                        'book_inquiries:' || NEW.id
                    );
                END;
                """
            )
        except Exception:
            pass

        conn.commit()

    def get_page_data():
        """Retrieve page configuration and active blocks."""
        db = get_db()
        cfg_row = db.execute("SELECT * FROM how_to_borrow_page WHERE id=1").fetchone()
        cfg = dict(cfg_row) if cfg_row else {}
        # Languages list
        raw_langs = cfg.get("languages", "English\nTamil\nHindi\nOther")
        cfg["language_options"] = [l.strip() for l in raw_langs.splitlines() if l.strip()]

        block_rows = db.execute(
            "SELECT * FROM how_to_borrow_blocks WHERE is_active=1 ORDER BY position ASC, id ASC"
        ).fetchall()
        blocks = []
        for r in block_rows:
            b = dict(r)
            b["checklist_items"] = parse_checklist(b.get("checklist", ""))
            blocks.append(b)
        return cfg, blocks

    def lookup_member(membership_id: str):
        """Look up member account by membership ID, numeric ID, email, or phone."""
        if not membership_id:
            return None
        db = get_db()
        raw = membership_id.strip()
        # Direct ID check if digits
        digits = re.findall(r"\d+", raw)
        if digits:
            try:
                num = int(digits[-1])
                user = db.execute("SELECT id, name, email, phone FROM users WHERE id=?", (num,)).fetchone()
                if user:
                    return dict(user)
            except Exception:
                pass
        # Check by email or phone
        user = db.execute(
            "SELECT id, name, email, phone FROM users WHERE LOWER(email)=LOWER(?) OR phone=?",
            (raw, raw),
        ).fetchone()
        if user:
            return dict(user)
        return None

    def admin_role_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            admin = current_admin()
            if not admin:
                return redirect("/admin/login/?next=" + quote(request.path))
            row = get_db().execute("SELECT role, is_active FROM admin_users WHERE id=?", (admin["id"],)).fetchone()
            if not row or not row["is_active"] or row["role"] not in {"super_admin", "org_admin", "librarian"}:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper

    # --- Public Route Handler ---

    @app.route("/how-to-borrow/", methods=["GET", "POST"], endpoint="how_to_borrow_route")
    def how_to_borrow_route():
        cfg, blocks = get_page_data()
        db = get_db()

        # Check logged in user for prefilling
        user_id = session.get("user_id")
        logged_user = None
        if user_id:
            logged_user = db.execute("SELECT id, name, email, phone FROM users WHERE id=?", (user_id,)).fetchone()

        default_mem_id = f"LIB-2026-{logged_user['id']:03d}" if logged_user else ""

        errors = []
        form_data = {
            "membership_id": default_mem_id,
            "book_title": "",
            "author": "",
            "language": "English",
            "notes": "",
            "consent": "1",
        }

        submitted = bool(request.args.get("submitted"))

        if request.method == "POST":
            # 1. Honeypot check
            if request.form.get("website_hp", "").strip():
                # Bot submission trapped: simulate success without saving
                return redirect("/how-to-borrow/?submitted=1")

            # 2. Form enabled check
            if not cfg.get("form_enabled", 1):
                flash("Online book inquiries are temporarily paused. Please visit the library circulation desk.", "danger")
                return redirect("/how-to-borrow/")

            # 3. Rate limiting (max 5 submissions per hour per IP hash)
            client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
            ip_hash = get_ip_hash(client_ip)
            recent_count = db.execute(
                "SELECT COUNT(*) FROM book_inquiries WHERE ip_hash=? AND created_at >= datetime('now', '-1 hour')",
                (ip_hash,),
            ).fetchone()[0]
            if recent_count >= 5:
                errors.append("Too many requests from this address. Please wait a short while before submitting again.")

            # 4. Form inputs & lengths
            mem_id = request.form.get("membership_id", "").strip()[:80]
            book_title = request.form.get("book_title", "").strip()[:250]
            author = request.form.get("author", "").strip()[:150]
            language = request.form.get("language", "English").strip()[:50]
            notes = request.form.get("notes", "").strip()[:1000]
            consent = 1 if request.form.get("consent") else 0

            form_data = {
                "membership_id": mem_id,
                "book_title": book_title,
                "author": author,
                "language": language,
                "notes": notes,
                "consent": str(consent),
            }

            if not book_title:
                errors.append("Please enter the book title or subject topic.")
            if not consent:
                errors.append("Please check the box agreeing to be notified regarding this request.")

            # 5. Member lookup & identification
            matched_member = lookup_member(mem_id) if mem_id else None
            matched_user_id = matched_member["id"] if matched_member else (logged_user["id"] if logged_user else None)
            m_name = matched_member["name"] if matched_member else (logged_user["name"] if logged_user else "")
            m_email = matched_member["email"] if matched_member else (logged_user["email"] if logged_user else "")
            m_phone = matched_member["phone"] if matched_member else (logged_user["phone"] if logged_user else "")

            contact_info = ""
            if matched_member:
                contact_info = matched_member.get("email") or matched_member.get("phone") or ""
            elif "@" in mem_id or re.search(r"\d{7,}", mem_id):
                contact_info = mem_id
            elif mem_id:
                # Entered an ID format that was not matched
                if not logged_user:
                    errors.append("Membership ID was not recognized. Please check your ID number or provide your email or phone.")
            elif not logged_user:
                errors.append("Please provide either your Membership ID or your contact email/phone so we can reach you.")

            if not errors:
                cur = db.cursor()
                cur.execute(
                    """
                    INSERT INTO book_inquiries (membership_id, contact_info, book_title, author,
                        language, notes, consent, user_id, member_name, member_email, member_phone,
                        status, ip_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'New', ?)
                    """,
                    (
                        mem_id,
                        contact_info,
                        book_title,
                        author,
                        language,
                        notes,
                        consent,
                        matched_user_id,
                        m_name,
                        m_email,
                        m_phone,
                        ip_hash,
                    ),
                )
                inquiry_id = cur.lastrowid
                db.commit()

                # Fallback manual notification if trigger is off
                try:
                    flag = db.execute("SELECT value FROM app_flags WHERE key='notifications_enabled'").fetchone()
                    if flag and flag[0] == "1":
                        db.execute(
                            """
                            INSERT OR IGNORE INTO admin_notifications(kind,title,body,url,source_key)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                "library",
                                "New book inquiry",
                                f"{book_title} · {m_name or contact_info or mem_id or 'Visitor'}",
                                f"/admin/book-inquiries/{inquiry_id}/",
                                f"book_inquiries:{inquiry_id}",
                            ),
                        )
                        db.commit()
                except Exception:
                    pass

                flash(cfg.get("success_message", DEFAULT_SUCCESS_MSG), "success")
                return redirect("/how-to-borrow/?submitted=1")

        if render_site:
            return render_site(
                "accounts/how_to_borrow",
                "library",
                page=cfg,
                blocks=blocks,
                form_data=form_data,
                errors=errors,
                submitted=submitted,
            )
        return render_template(
            "site/accounts/how_to_borrow.html",
            page=cfg,
            blocks=blocks,
            form_data=form_data,
            errors=errors,
            submitted=submitted,
            user=logged_user,
        )

    # --- Admin Editor Route ---

    @app.route("/admin/how-to-borrow-editor/", methods=["GET", "POST"])
    @admin_role_required
    def admin_how_to_borrow_editor():
        db = get_db()
        admin = current_admin()

        # Check for legacy cms_pages conflict
        cms_row = db.execute(
            "SELECT id, slug, title, is_active FROM cms_pages WHERE slug='how-to-borrow' AND is_active=1"
        ).fetchone()

        if request.method == "POST":
            action = request.form.get("action", "save_settings")

            if action == "save_settings":
                page_heading = request.form.get("page_heading", DEFAULT_HEADING).strip()
                form_enabled = 1 if request.form.get("form_enabled") else 0
                form_title = request.form.get("form_title", DEFAULT_FORM_TITLE).strip()
                membership_id_label = request.form.get("membership_id_label", "Membership ID").strip()
                membership_id_placeholder = request.form.get("membership_id_placeholder", "").strip()
                membership_id_helper = request.form.get("membership_id_helper", DEFAULT_MEM_HELPER).strip()
                book_title_label = request.form.get("book_title_label", "").strip()
                book_title_placeholder = request.form.get("book_title_placeholder", "").strip()
                author_label = request.form.get("author_label", "").strip()
                author_placeholder = request.form.get("author_placeholder", "").strip()
                language_label = request.form.get("language_label", "").strip()
                languages = request.form.get("languages", "English\nTamil\nHindi\nOther").strip()
                notes_label = request.form.get("notes_label", "").strip()
                notes_placeholder = request.form.get("notes_placeholder", "").strip()
                consent_text = request.form.get("consent_text", "").strip()
                button_label = request.form.get("button_label", "Submit Inquiry").strip()
                success_message = request.form.get("success_message", DEFAULT_SUCCESS_MSG).strip()

                db.execute(
                    """
                    UPDATE how_to_borrow_page SET
                        page_heading=?, form_enabled=?, form_title=?,
                        membership_id_label=?, membership_id_placeholder=?, membership_id_helper=?,
                        book_title_label=?, book_title_placeholder=?,
                        author_label=?, author_placeholder=?,
                        language_label=?, languages=?,
                        notes_label=?, notes_placeholder=?,
                        consent_text=?, button_label=?, success_message=?
                    WHERE id=1
                    """,
                    (
                        page_heading,
                        form_enabled,
                        form_title,
                        membership_id_label,
                        membership_id_placeholder,
                        membership_id_helper,
                        book_title_label,
                        book_title_placeholder,
                        author_label,
                        author_placeholder,
                        language_label,
                        languages,
                        notes_label,
                        notes_placeholder,
                        consent_text,
                        button_label,
                        success_message,
                    ),
                )
                db.execute(
                    "INSERT INTO admin_audit(admin_id, action) VALUES(?, ?)",
                    (admin["id"], "Updated How to Borrow page settings"),
                )
                db.commit()
                flash("How to Borrow settings saved.", "success")
                return redirect("/admin/how-to-borrow-editor/")

            elif action == "save_blocks":
                block_ids = request.form.getlist("block_id")

                for b_id in block_ids:
                    if not b_id or not b_id.isdigit():
                        continue
                    bid = int(b_id)
                    h = request.form.get(f"block_heading_{bid}", "").strip()
                    b = request.form.get(f"block_body_{bid}", "").strip()
                    c = request.form.get(f"block_checklist_{bid}", "").strip()
                    pos_str = request.form.get(f"block_position_{bid}", "0").strip()
                    pos = int(pos_str) if pos_str.isdigit() else 0
                    is_act = 1 if request.form.get(f"block_active_{bid}") else 0

                    if h:
                        db.execute(
                            "UPDATE how_to_borrow_blocks SET heading=?, body=?, checklist=?, position=?, is_active=? WHERE id=?",
                            (h, b, c, pos, is_act, bid),
                        )

                # Add new block if provided
                new_h = request.form.get("new_heading", "").strip()
                new_b = request.form.get("new_body", "").strip()
                new_c = request.form.get("new_checklist", "").strip()
                new_pos = request.form.get("new_position", "0").strip()
                if new_h:
                    p = int(new_pos) if new_pos.isdigit() else len(block_ids) + 1
                    db.execute(
                        "INSERT INTO how_to_borrow_blocks (heading, body, checklist, position, is_active) VALUES (?, ?, ?, ?, 1)",
                        (new_h, new_b, new_c, p),
                    )

                db.execute(
                    "INSERT INTO admin_audit(admin_id, action) VALUES(?, ?)",
                    (admin["id"], "Updated How to Borrow content blocks"),
                )
                db.commit()
                flash("Content blocks saved.", "success")
                return redirect("/admin/how-to-borrow-editor/#blocks")

            elif action == "delete_block":
                delete_id = request.form.get("delete_block_id")
                if delete_id and delete_id.isdigit():
                    db.execute("DELETE FROM how_to_borrow_blocks WHERE id=?", (int(delete_id),))
                    db.execute(
                        "INSERT INTO admin_audit(admin_id, action) VALUES(?, ?)",
                        (admin["id"], f"Deleted How to Borrow block {delete_id}"),
                    )
                    db.commit()
                    flash("Block removed.", "info")
                return redirect("/admin/how-to-borrow-editor/#blocks")

        cfg, _ = get_page_data()
        all_blocks = db.execute("SELECT * FROM how_to_borrow_blocks ORDER BY position ASC, id ASC").fetchall()
        blocks = [dict(b) for b in all_blocks]

        # Public preview data
        preview_blocks = []
        for b in blocks:
            if b.get("is_active"):
                pb = dict(b)
                pb["checklist_items"] = parse_checklist(pb.get("checklist", ""))
                preview_blocks.append(pb)

        return render_template(
            "workspace/how_to_borrow_editor.html",
            title="How to borrow page",
            admin=admin,
            active="how_to_borrow_editor",
            page=cfg,
            blocks=blocks,
            preview_blocks=preview_blocks,
            cms_conflict=cms_row,
        )

    # --- Admin Book Inquiries Management Routes ---

    @app.route("/admin/book-inquiries/", methods=["GET"])
    @admin_role_required
    def admin_book_inquiries():
        db = get_db()
        admin = current_admin()

        status_filter = request.args.get("status", "").strip()
        lang_filter = request.args.get("language", "").strip()
        q = request.args.get("q", "").strip()

        query = "SELECT * FROM book_inquiries WHERE 1=1"
        params = []

        if status_filter and status_filter in VALID_STATUSES:
            query += " AND status = ?"
            params.append(status_filter)

        if lang_filter:
            query += " AND language = ?"
            params.append(lang_filter)

        if q:
            query += """ AND (
                book_title LIKE ? OR author LIKE ? OR membership_id LIKE ?
                OR member_name LIKE ? OR member_email LIKE ? OR contact_info LIKE ?
                OR notes LIKE ?
            )"""
            wild = f"%{q}%"
            params.extend([wild] * 7)

        query += " ORDER BY id DESC"

        rows = db.execute(query, params).fetchall()
        inquiries = [dict(r) for r in rows]

        # Available distinct languages for filter dropdown
        lang_rows = db.execute(
            "SELECT DISTINCT language FROM book_inquiries WHERE language != '' ORDER BY language"
        ).fetchall()
        available_langs = [r[0] for r in lang_rows]

        return render_template(
            "workspace/book_inquiries.html",
            title="Book requests / inquiries",
            admin=admin,
            active="book_inquiries",
            inquiries=inquiries,
            status_filter=status_filter,
            lang_filter=lang_filter,
            q=q,
            valid_statuses=VALID_STATUSES,
            available_langs=available_langs,
        )

    @app.route("/admin/book-inquiries/export-csv/", methods=["GET"])
    @admin_role_required
    def export_book_inquiries_csv():
        db = get_db()
        status_filter = request.args.get("status", "").strip()
        lang_filter = request.args.get("language", "").strip()
        q = request.args.get("q", "").strip()

        query = "SELECT * FROM book_inquiries WHERE 1=1"
        params = []
        if status_filter and status_filter in VALID_STATUSES:
            query += " AND status = ?"
            params.append(status_filter)
        if lang_filter:
            query += " AND language = ?"
            params.append(lang_filter)
        if q:
            query += """ AND (
                book_title LIKE ? OR author LIKE ? OR membership_id LIKE ?
                OR member_name LIKE ? OR member_email LIKE ? OR contact_info LIKE ?
                OR notes LIKE ?
            )"""
            wild = f"%{q}%"
            params.extend([wild] * 7)
        query += " ORDER BY id DESC"

        rows = db.execute(query, params).fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Date", "Status", "Book Title", "Author", "Language",
            "Membership ID", "Member Name", "Email", "Phone", "Contact Info",
            "Notes", "Admin Notes"
        ])
        for r in rows:
            writer.writerow([
                r["id"], r["created_at"], r["status"], r["book_title"], r["author"], r["language"],
                r["membership_id"], r["member_name"], r["member_email"], r["member_phone"], r["contact_info"],
                r["notes"], r["admin_notes"]
            ])

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=book_inquiries_{datetime.now().strftime('%Y%m%d')}.csv"},
        )

    @app.route("/admin/book-inquiries/<int:inquiry_id>/", methods=["GET", "POST"])
    @admin_role_required
    def admin_book_inquiry_detail(inquiry_id: int):
        db = get_db()
        admin = current_admin()

        row = db.execute("SELECT * FROM book_inquiries WHERE id=?", (inquiry_id,)).fetchone()
        if not row:
            abort(404, "Inquiry not found")

        inquiry = dict(row)

        if request.method == "POST":
            new_status = request.form.get("status", inquiry["status"]).strip()
            admin_notes = request.form.get("admin_notes", "").strip()

            if new_status in VALID_STATUSES:
                db.execute(
                    "UPDATE book_inquiries SET status=?, admin_notes=? WHERE id=?",
                    (new_status, admin_notes, inquiry_id),
                )
                db.execute(
                    "INSERT INTO admin_audit(admin_id, action) VALUES(?, ?)",
                    (admin["id"], f"Updated inquiry {inquiry_id} status to {new_status}"),
                )
                db.commit()
                flash(f"Inquiry updated: Status set to {new_status}.", "success")
                return redirect(f"/admin/book-inquiries/{inquiry_id}/")

        # Ready email text for "Notify Member" when available
        recipient_name = inquiry["member_name"] or "Reader"
        book_title = inquiry["book_title"]
        author_text = f" by {inquiry['author']}" if inquiry["author"] else ""
        recipient_email = inquiry["member_email"] or (inquiry["contact_info"] if "@" in inquiry["contact_info"] else "")

        email_subject = f"Your requested book is now available: {book_title}"
        email_body = (
            f"Dear {recipient_name},\n\n"
            f"Great news! The book you requested, '{book_title}'{author_text}, is now available at Book Buddy.\n\n"
            f"You can visit the circulation desk during library hours to borrow your copy. "
            f"Please bring your Membership ID card ({inquiry['membership_id'] or 'or government ID'}) for quick checkout.\n\n"
            f"Library Address: MK Complex 2nd floor, K.Pudur, Madurai\n"
            f"Working Hours: Tue-Sun 10:00 AM - 1:00 PM & 4:30 PM - 8:30 PM (Closed Monday)\n\n"
            f"Happy Reading,\n"
            f"Book Buddy Library Team"
        )

        return render_template(
            "workspace/book_inquiry_detail.html",
            title=f"Inquiry #{inquiry['id']} · {inquiry['book_title']}",
            admin=admin,
            active="book_inquiries",
            inquiry=inquiry,
            valid_statuses=VALID_STATUSES,
            email_subject=email_subject,
            email_body=email_body,
            recipient_email=recipient_email,
        )
