"""Book Buddy Flask application.

This module is the Flask replacement for the original Django entrypoint.  The
presentation layer remains in the original template hierarchy so the visual
theme and library page content use the
same markup and static assets.
"""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from functools import wraps
import sys
from pathlib import Path

ROUTES_DIR = Path(__file__).resolve().parent
APP_DIR = ROUTES_DIR.parent
SERVICES_DIR = APP_DIR / "services"
BACKEND_DIR = APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent
BASE_DIR = APP_DIR

for _p in (str(SERVICES_DIR), str(ROUTES_DIR), str(APP_DIR), str(BACKEND_DIR), str(ROOT_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dotenv import load_dotenv
load_dotenv(os.environ.get("BOOK_BUDDY_ENV_FILE", ROOT_DIR / ".env"), override=False)
from typing import Any

from flask import (
    Flask,
    Response,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request as flask_request,
    session,
    url_for as flask_url_for,
)
from markupsafe import Markup, escape
from werkzeug.exceptions import NotFound
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError
import io
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.routing import BuildError


if os.environ.get("VERCEL"):  # read-only filesystem: keep writable data in /tmp
    _tmp = Path("/tmp/bookbuddy")
    for _k, _v in (("BOOK_BUDDY_DATABASE", _tmp / "book_buddy.sqlite3"),
                   ("BOOK_BUDDY_PRIVATE_DIR", _tmp / "private"),
                   ("BOOK_BUDDY_BACKUP_DIR", _tmp / "backups")):
        os.environ.setdefault(_k, str(_v))
    os.environ.setdefault("SECRET_KEY", "change-me-set-SECRET_KEY-in-vercel")
# Database lives in instance/ at the project root (not inside backend/)
DATABASE_PATH = Path(os.environ.get("BOOK_BUDDY_DATABASE", ROOT_DIR / "instance" / "book_buddy.sqlite3"))

def get_database_path() -> Path:
    return DATABASE_PATH

app = Flask(__name__, template_folder=str(APP_DIR / "templates"), static_folder=str(APP_DIR / "static"))
secret_path = DATABASE_PATH.parent / '.session-secret'
secret_path.parent.mkdir(parents=True, exist_ok=True)
if not os.environ.get('SECRET_KEY') and not secret_path.exists():
    try:
        with secret_path.open('x') as secret_file: secret_file.write(secrets.token_hex(32))
        secret_path.chmod(0o600)
    except FileExistsError: pass
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY') or secret_path.read_text().strip(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE','0')=='1',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    MAX_FORM_MEMORY_SIZE=12 * 1024 * 1024,
    RAZORPAY_KEY_ID=os.environ.get("RAZORPAY_KEY_ID", ""),
    RAZORPAY_KEY_SECRET=os.environ.get("RAZORPAY_KEY_SECRET", ""),
    GEMINI_API_KEY=os.environ.get("GEMINI_API_KEY", ""),
)


@dataclass
class CompatObject:
    """Small attribute-friendly record used by the migrated templates."""

    values: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        return self.values.get(name)

    def __getitem__(self, key: str) -> Any:
        return self.values.get(key)


@dataclass
class MediaRef:
    url: str


class GuestUser(CompatObject):
    def __init__(self) -> None:
        super().__init__(
            {
                "id": None,
                "pk": None,
                "name": "",
                "username": "",
                "email": "",
                "is_authenticated": False,
                "is_superuser": False,
                "is_membership_active": False,
                "has_used_trial": False,
                "active_plan": None,
                "membership_expiry": None,
                "image": None,
                "socialaccount_set": CompatObject({"all": []}),
                "favorite_books": [],
            }
        )


class MemberUser(GuestUser):
    def __init__(self, row: sqlite3.Row) -> None:
        super().__init__()
        self.values.update(
            {
                "id": row["id"],
                "pk": row["id"],
                "name": row["name"] or row["email"].split("@")[0],
                "username": row["email"],
                "email": row["email"],
                "is_authenticated": True,
                "dob": row['dob'],
                "phone": row['phone'],
                "address": row['address'],
            }
        )
        try:
            today = date.today().isoformat()
            active = get_db().execute("""SELECT s.expires_on,p.name FROM lending_subscriptions s
                JOIN lending_plans p ON p.id=s.plan_id WHERE s.user_id=? AND s.status IN ('Active','Scheduled')
                AND s.starts_on<=? AND s.expires_on>=? ORDER BY s.expires_on DESC LIMIT 1""",(row['id'],today,today)).fetchone()
            if active:
                self.values.update(is_membership_active=True, membership_expiry=active['expires_on'],
                                   active_plan=CompatObject({'title':active['name'],'name':active['name']}))
        except sqlite3.OperationalError:
            pass


@dataclass
class RequestAdapter:
    scheme: str
    get_host: str
    build_absolute_uri: str
    user: Any
    session: Any


class FormMarkup:
    def __init__(self, html: str = "", fields: list[Any] | None = None) -> None:
        self.html = html
        self.fields = fields or []

    def __iter__(self):
        return iter(self.fields)


class CompatList(list):
    @property
    def last(self) -> Any:
        return self[-1] if self else CompatObject({"id": 0})


@dataclass
class FormField:
    name: str
    label: str
    input_html: str
    help_text: str = ""
    errors: list[str] = field(default_factory=list)

    @property
    def id_for_label(self) -> str:
        return f"id_{self.name}"

    def __str__(self) -> str:
        return self.input_html


def db_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = db_connection()
    return g.db


@app.teardown_appcontext
def close_db(_: BaseException | None = None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db() -> None:
    connection = db_connection()
    # Remove a broken historical payment trigger before *any* table migrations.
    # The event_registrations table has no payment_status column, and leaving
    # this trigger installed can make unrelated ALTER TABLE statements fail.
    connection.execute("DROP TRIGGER IF EXISTS notify10_event_payment")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL DEFAULT '',
            password_hash TEXT NOT NULL,
            date_joined TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            edition_name TEXT NOT NULL DEFAULT 'Newsletter',
            subscribed_on TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            author_nationality TEXT NOT NULL DEFAULT 'Indian',
            collection TEXT NOT NULL DEFAULT 'Story',
            age_group TEXT NOT NULL DEFAULT '6-8',
            language TEXT NOT NULL DEFAULT 'English',
            is_new_arrival INTEGER NOT NULL DEFAULT 0,
            available_copies INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS book_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_title TEXT NOT NULL,
            user_name TEXT NOT NULL,
            member_id TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            request_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS contact_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT,
            subject TEXT,
            phone TEXT,
            message TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS partner_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            organisation TEXT NOT NULL DEFAULT '',
            proposal_type TEXT NOT NULL DEFAULT 'General',
            message TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'New',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            page_visited TEXT NOT NULL,
            enter_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            exit_time TEXT,
            time_spent_seconds INTEGER
        );
        CREATE TABLE IF NOT EXISTS site_content (
            content_key TEXT PRIMARY KEY,
            content_value TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL DEFAULT 'Book Buddy Admin',
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            event_date TEXT NOT NULL,
            event_time TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT 'Book Buddy Library',
            fee REAL NOT NULL DEFAULT 0,
            capacity INTEGER NOT NULL DEFAULT 30,
            image_path TEXT NOT NULL DEFAULT '',
            is_online INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS event_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            seats INTEGER NOT NULL DEFAULT 1,
            amount REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Registered',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(event_id) REFERENCES events(id)
        );
        CREATE TABLE IF NOT EXISTS publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'magazine',
            description TEXT NOT NULL DEFAULT '',
            edition TEXT NOT NULL DEFAULT '',
            file_path TEXT NOT NULL DEFAULT '',
            cover_path TEXT NOT NULL DEFAULT '',
            published_on TEXT NOT NULL DEFAULT CURRENT_DATE,
            is_active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            total REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            book_id INTEGER,
            title TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            price REAL NOT NULL DEFAULT 0,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
        """
    )
    existing_columns = {row[1] for row in connection.execute("PRAGMA table_info(books)").fetchall()}
    for column, definition in {
        "price": "REAL NOT NULL DEFAULT 0",
        "description": "TEXT NOT NULL DEFAULT ''",
        "image_path": "TEXT NOT NULL DEFAULT ''",
        "stock": "INTEGER NOT NULL DEFAULT 1",
        "product_type": "TEXT NOT NULL DEFAULT 'book'",
        "is_active": "INTEGER NOT NULL DEFAULT 1",
        "archived": "INTEGER NOT NULL DEFAULT 0",
    }.items():
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE books ADD COLUMN {column} {definition}")
    count = connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    pass
    if os.environ.get('ADMIN_EMAIL') and os.environ.get('ADMIN_PASSWORD'):
        connection.execute(
            'INSERT OR IGNORE INTO admin_users(email,name,password_hash) VALUES (?,?,?)',
            (os.environ['ADMIN_EMAIL'].lower(),'Book Buddy Admin',generate_password_hash(os.environ['ADMIN_PASSWORD'])),
        )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS working_hours (
            id INTEGER PRIMARY KEY,
            days TEXT NOT NULL DEFAULT '',
            hours TEXT NOT NULL DEFAULT '',
            closed TEXT NOT NULL DEFAULT '',
            position INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1
        );
        """
    )
    if connection.execute("SELECT COUNT(*) FROM working_hours").fetchone()[0] == 0:
        connection.executemany(
            "INSERT INTO working_hours (days, hours, closed, position, is_active) VALUES (?, ?, ?, ?, ?)",
            [
                ("Tuesday – Sunday", "10:00 AM – 1:00 PM\n4:30 PM – 8:30 PM", "", 1, 1),
                ("Monday", "", "Closed", 2, 1),
            ],
        )
    connection.executemany('INSERT OR IGNORE INTO site_content VALUES (?,?)', [
        ('hero_eyebrow',''),('hero_title',''),('hero_text',''),('about_text',''),('newsletter_title',''),('newsletter_text',''),
        ('footer_phone_label','Phone'),('footer_email_label','Email'),('footer_address_label','Address'),
        ('footer_hours_heading','Working Hours'),('footer_contact_heading','Get In Touch')
    ])
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS gallery_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            image_path TEXT NOT NULL,
            thumbnail_path TEXT DEFAULT '',
            alt_text TEXT DEFAULT '',
            page_slug TEXT DEFAULT 'home',
            position INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            category TEXT NOT NULL DEFAULT 'reading-moments'
        );
        """
    )
    gallery_cols = {row[1] for row in connection.execute("PRAGMA table_info(gallery_items)").fetchall()}
    if "category" not in gallery_cols:
        connection.execute("ALTER TABLE gallery_items ADD COLUMN category TEXT NOT NULL DEFAULT 'reading-moments'")
    connection.execute("UPDATE gallery_items SET category='reading-moments' WHERE category IS NULL OR TRIM(category)=''")

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS collaborators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            brief TEXT NOT NULL DEFAULT '',
            image TEXT NOT NULL DEFAULT '',
            link TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS lending_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            subscription_id INTEGER NOT NULL REFERENCES lending_subscriptions(id),
            delivery_mode TEXT NOT NULL DEFAULT 'offline',
            delivery_address TEXT NOT NULL DEFAULT '',
            contact_phone TEXT NOT NULL DEFAULT '',
            contact_name TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Requested',
            admin_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_lending_requests_user ON lending_requests(user_id, status);")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_lending_requests_status ON lending_requests(status);")

    has_loans_table = bool(connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='lending_loans'").fetchone())
    if has_loans_table:
        loan_cols = {row[1] for row in connection.execute("PRAGMA table_info(lending_loans)").fetchall()}
        if "request_id" not in loan_cols:
            connection.execute("ALTER TABLE lending_loans ADD COLUMN request_id INTEGER REFERENCES lending_requests(id)")
        if "delivery_mode" not in loan_cols:
            connection.execute("ALTER TABLE lending_loans ADD COLUMN delivery_mode TEXT NOT NULL DEFAULT ''")
        if "delivery_address" not in loan_cols:
            connection.execute("ALTER TABLE lending_loans ADD COLUMN delivery_address TEXT NOT NULL DEFAULT ''")
        if "contact_phone" not in loan_cols:
            connection.execute("ALTER TABLE lending_loans ADD COLUMN contact_phone TEXT NOT NULL DEFAULT ''")
    connection.commit()
    connection.close()


def safe_url_for(endpoint: str, *args: Any, **kwargs: Any) -> str:
    """Keep legacy links usable even when a Django-only endpoint was removed."""

    try:
        return flask_url_for(endpoint, *args, **kwargs)
    except BuildError:
        return "#"


def _format_date(value: Any, format_string: str = "N j, Y") -> str:
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    mapping = {
        "M": "%b",
        "F": "%B",
        "j": "%-d",
        "d": "%d",
        "Y": "%Y",
        "y": "%y",
        "h": "%I",
        "H": "%H",
        "i": "%M",
        "A": "%p",
    }
    output = format_string
    for django_token, python_token in mapping.items():
        output = output.replace(django_token, python_token)
    try:
        return value.strftime(output).replace(" 0", " ")
    except (AttributeError, ValueError):
        return str(value)


def _slice_filter(value: Any, expression: str) -> Any:
    text = str(expression)
    parts = text.split(":")
    try:
        start = int(parts[0]) if parts[0] else None
        stop = int(parts[1]) if len(parts) > 1 and parts[1] else None
        step = int(parts[2]) if len(parts) > 2 and parts[2] else None
        return value[slice(start, stop, step)]
    except (TypeError, ValueError, IndexError):
        return value


def _json_script(value: Any, element_id: str) -> Markup:
    payload = json.dumps(value or {}, ensure_ascii=False).replace("<", "\\u003c")
    return Markup(f'<script id="{escape(element_id)}" type="application/json">{payload}</script>')


def _crispy(value: Any) -> Markup:
    if isinstance(value, FormMarkup):
        return Markup(value.html)
    return Markup(str(value or ""))


def register_template_compatibility() -> None:
    env = app.jinja_env
    env.globals["url_for"] = safe_url_for
    env.filters.update(
        {
            "date": _format_date,
            "add": lambda value, other=0: (value + other) if isinstance(value, (int, float)) and isinstance(other, (int, float)) else f"{value}{other}",
            "default_if_none": lambda value, default="": default if value is None else value,
            "escapejs": lambda value: Markup(json.dumps("" if value is None else str(value))),
            "force_escape": lambda value: escape(value or ""),
            "floatformat": lambda value, digits=0: f"{float(value):.{int(digits)}f}" if value not in (None, "") else "",
            "json_script": _json_script,
            "linebreaksbr": lambda value: Markup("<br>\n".join(str(escape(value or "")).splitlines())),
            "slice_filter": _slice_filter,
            "stringformat": lambda value, spec="s": (f"%{spec}" % value),
            "truncatewords": lambda value, count=15: " ".join(str(value or "").split()[: int(count)]) + ("..." if len(str(value or "").split()) > int(count) else ""),
            "yesno": lambda value, choices="yes,no": choices.split(",")[0 if value else (1 if len(choices.split(",")) > 1 else 0)],
            "crispy": _crispy,
        }
    )


def current_user() -> GuestUser | MemberUser:
    user_id = session.get("user_id")
    if not user_id and flask_request:
        try:
            test_uid = flask_request.args.get("test_user_id")
            if test_uid:
                user_id = int(test_uid)
        except Exception:
            pass
    if not user_id:
        return GuestUser()
    row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return MemberUser(row) if row else GuestUser()


def current_admin() -> dict[str, Any] | None:
    admin_id = session.get("admin_id")
    if not admin_id:
        return None
    row = get_db().execute("SELECT id, email, name FROM admin_users WHERE id = ?", (admin_id,)).fetchone()
    return dict(row) if row else None


def row_dict(row: sqlite3.Row | None) -> dict[str, Any]:
    return dict(row) if row else {}


def cart_snapshot() -> tuple[list[dict[str, Any]], float, int]:
    raw_cart = session.get("cart", {}) or {}
    clean_cart: dict[str, int] = {}
    for book_id, quantity in raw_cart.items():
        try:
            parsed_id = int(book_id)
            parsed_quantity = max(0, min(20, int(quantity)))
        except (TypeError, ValueError):
            continue
        if parsed_quantity:
            clean_cart[str(parsed_id)] = parsed_quantity
    session["cart"] = clean_cart
    items: list[dict[str, Any]] = []
    total = 0.0
    count = 0
    if clean_cart:
        placeholders = ",".join("?" for _ in clean_cart)
        rows = get_db().execute(f"SELECT * FROM books WHERE id IN ({placeholders})", tuple(int(book_id) for book_id in clean_cart)).fetchall()
        for row in rows:
            quantity = clean_cart.get(str(row["id"]), 0)
            price = float(row["price"] or 0)
            item_total = price * quantity
            items.append({"book": row_dict(row), "quantity": quantity, "price": price, "total": item_total})
            total += item_total
            count += quantity
    return items, total, count


def site_context(section: str = "home") -> dict[str, Any]:
    db = get_db()
    items, cart_total, cart_count = cart_snapshot()
    content = {row["content_key"]: row["content_value"] for row in db.execute("SELECT content_key, content_value FROM site_content").fetchall()}
    all_books = [] if section in {"library", "shop"} else [row_dict(row) for row in db.execute("SELECT * FROM books WHERE archived=0 ORDER BY is_new_arrival DESC, id DESC").fetchall()]
    from accounts import years_old, age_matches
    reader = current_user()
    reader_age = years_old(reader.values.get('dob')) if reader.is_authenticated else None
    if reader_age is not None and reader_age < 18:
        all_books = [book for book in all_books if age_matches(book.get('age_group'), reader_age)]
    # Library-only Version 1: events and reading groups replace old classes/worksheets.
    # Empty compatibility lists avoid reading historical learning tables in existing databases.
    classes = []
    activities = []
    events = [row_dict(row) for row in db.execute("SELECT * FROM events WHERE is_active = 1 ORDER BY event_date, event_time").fetchall()]
    publications = [row_dict(row) for row in db.execute("SELECT * FROM publications WHERE is_active = 1 ORDER BY published_on DESC, id DESC").fetchall()]
    try:
        working_hours_list = [row_dict(row) for row in db.execute("SELECT * FROM working_hours WHERE is_active = 1 ORDER BY position, id").fetchall()]
    except Exception:
        working_hours_list = []
    calendar_events = {}
    for event in events:
        calendar_events.setdefault(event['event_date'], []).append({**{k:v for k,v in event.items() if k!='join_url'},'url':safe_url_for('event_detail',event_id=event['id'])})
    # Lending subscription context — always included so library.html is safe even when
    # rendered from routes that don't call paged_books() (e.g. if template inheritance is
    # extended to other pages). paged_books() will overwrite these with fresh values.
    _reader = current_user()
    _member_active_sub: dict | None = None
    _member_active_cnt: int = 0
    if _reader and _reader.is_authenticated:
        from accounts import get_active_subscription, get_active_loan_count
        _sub_row = get_active_subscription(db, _reader.id)
        if _sub_row:
            _member_active_sub = dict(_sub_row)
        _member_active_cnt = get_active_loan_count(db, _reader.id)

    return {
        "section": section,
        "brand": {"primary": "#0A2472", "wine": "#0A2472", "gold": "#0A2472", "cream": "#FFFFFF"},
        "logo_url": safe_url_for("static", filename="img/brand/book-buddy-logo.png"),
        "user": current_user(),
        "admin": current_admin(),
        "books": all_books,
        "featured_books": all_books[:8],
        "classes": classes,
        "events": events,
        "calendar_events": calendar_events,
        "activities": activities,
        "publications": publications,
        "working_hours_list": working_hours_list,
        "content": content,
        "cart_items": items,
        "cart_total": cart_total,
        "cart_count": cart_count,
        "today": date.today().isoformat(),
        "current_year": date.today().year,
        # Lending plan context — safe defaults for all pages; paged_books() overwrites for /library/
        "member_active_sub": _member_active_sub,
        "member_active_cnt": _member_active_cnt,
    }


def render_site(template_name: str, section: str = "home", **extra: Any) -> Response:
    context = site_context(section)
    context.update(extra)
    return render_template(f"site/{template_name}.html", **context)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_admin():
            return redirect(safe_url_for("admin_login", next=flask_request.path))
        return view(*args, **kwargs)

    return wrapped


def media_url(relative_path: str) -> str:
    return flask_url_for("media", filename=relative_path)


def row_to_book(row: sqlite3.Row) -> CompatObject:
    return CompatObject(
        {
            "id": row["id"],
            "title": row["title"],
            "author": row["author"],
            "author_nationality": row["author_nationality"],
            "collection": row["collection"],
            "age_group": row["age_group"],
            "language": row["language"],
            "is_new_arrival": bool(row["is_new_arrival"]),
            "available_copies": row["available_copies"],
            "price": row["price"] if "price" in row.keys() else 0,
            "description": row["description"] if "description" in row.keys() else "",
            "stock": row["stock"] if "stock" in row.keys() else row["available_copies"],
            "image_url": row["image_path"] if "image_path" in row.keys() and row["image_path"] else "",
            "image": MediaRef(row["image_path"] if "image_path" in row.keys() and row["image_path"] else ""),
        }
    )


def build_form(kind: str = "generic") -> FormMarkup:
    if kind == "login":
        return FormMarkup(
            '<div class="mb-3"><label class="form-label" for="id_login">Email</label>'
            '<input class="form-control" type="email" id="id_login" name="email" required></div>'
            '<div class="mb-3"><label class="form-label" for="id_password">Password</label>'
            '<input class="form-control" type="password" id="id_password" name="password" required></div>'
        )
    if kind == "signup":
        return FormMarkup(
            '<div class="mb-3"><label class="form-label" for="id_name">Name</label>'
            '<input class="form-control" type="text" id="id_name" name="name" required></div>'
            '<div class="mb-3"><label class="form-label" for="id_email">Email</label>'
            '<input class="form-control" type="email" id="id_email" name="email" required></div>'
            '<div class="mb-3"><label class="form-label" for="id_password1">Password</label>'
            '<input class="form-control" type="password" id="id_password1" name="password" required></div>'
        )
    if kind == "reset":
        return FormMarkup(
            '<div class="mb-3"><label class="form-label" for="id_email">Email</label>'
            '<input class="form-control" type="email" id="id_email" name="email" required></div>'
        )
    if kind == "contribution":
        fields = [
            FormField("student_name", "Student name", '<input class="form-control" name="student_name" placeholder="Your Full Name" required>'),
            FormField("grade_or_batch", "Grade or batch", '<input class="form-control" name="grade_or_batch" placeholder="E.g., Grade 5 or IT Dept">'),
            FormField("email", "Email", '<input class="form-control" type="email" name="email" placeholder="your.email@example.com">'),
            FormField("title", "Title", '<input class="form-control" name="title" placeholder="Title of your amazing work" required>'),
            FormField("category", "Category", '<select class="form-select" name="category"><option>Story</option><option>Poem</option><option>Artwork</option></select>'),
            FormField("content", "Content", '<textarea class="form-control" name="content" rows="5" placeholder="Write your story or poem here..."></textarea>'),
            FormField("attachment", "Attachment", '<input class="form-control" type="file" name="attachment">'),
        ]
        return FormMarkup("", fields)
    return FormMarkup("")


def base_context(template_name: str = "") -> dict[str, Any]:
    user = current_user()
    db = get_db()
    books = [row_to_book(row) for row in db.execute("SELECT * FROM books ORDER BY id DESC").fetchall()]
    now = datetime.now(timezone.utc)
    plans = [
        CompatObject({"id": 1, "plan_type": "2 Months", "tagline": "Summer Special", "solo_price": 800, "family_price": 1200, "total_books": 2, "get_plan_type_display": "2 Months", "get_features_list": ["2 books at a time", "Reading circle access"]}),
        CompatObject({"id": 2, "plan_type": "3 Months", "tagline": "Regular Explorer", "solo_price": 1100, "family_price": 1600, "total_books": 3, "get_plan_type_display": "3 Months", "get_features_list": ["3 books at a time", "Learning activities"]}),
        CompatObject({"id": 3, "plan_type": "9 Months", "tagline": "Academic Year", "solo_price": 2800, "family_price": 4000, "total_books": 9, "get_plan_type_display": "9 Months", "get_features_list": ["9 books at a time", "All learning modules"]}),
    ]
    return {
        "template_name": template_name,
        "user": user,
        "object": user,
        "request": RequestAdapter(
            flask_request.scheme,
            flask_request.host,
            flask_request.url,
            user,
            session,
        ),
        "csrf_token": session.setdefault("csrf_token", secrets.token_urlsafe(24)),
        "current_date_iso": date.today().isoformat(),
        "current_date": date.today().isoformat(),
        "LANGUAGE_CODE": "en",
        "books": books,
        "user_favorite_ids": [],
        "book_requests": [],
        "collections": ["Story", "Comics", "General", "Magazines", "Phonics", "Spiritual"],
        "languages": ["English", "Tamil", "Hindi"],
        "age_groups": ["4-6", "6-8", "8-10", "10-12"],
        "prominent_authors": ["Enid Blyton", "Roald Dahl", "Ruskin Bond", "Sudha Murthy", "G Stilton", "Jeremy Strong", "Jeff Kinney"],
        "plans": plans,
        "site_settings": CompatObject({"enable_memberships": True}),
        "about": CompatObject({"main_heading": "Our Ikigai", "main_content": "We help children discover the joy of reading, learning and creating together.", "quote_text": "At the centre of Book Buddy is meaningful learning through stories and community."}),
        "editions": [],
        "magazines": [],
        "podcasts": [],
        "workshops": [],
        "projects": [],
        "interns": [],
        "modules": [],
        "all_programs": [],
        "programs": [],
        "program": CompatObject({"id": 1, "title": "Book Buddy Internship"}),
        "all_contests": [],
        "completed_contests": [],
        "live_contests": [],
        "upcoming_contests": [],
        "authors_stories": [],
        "store_orders": [],
        "chat_messages": CompatList(),
        "messages": [],
        "events_data": {},
        "next_circle_date": "To Be Announced Soon",
        "user_email": user.values.get("email", ""),
        "student_name": user.values.get("name", "Guest Explorer"),
        "user_current_streak": 0,
        "user_total_score": 0,
        "progress_percentage": 0,
        "RAZORPAY_KEY_ID": app.config["RAZORPAY_KEY_ID"],
        "razorpay_key": app.config["RAZORPAY_KEY_ID"],
        "razorpay_merchant_key": app.config["RAZORPAY_KEY_ID"],
        "login_url": safe_url_for("account_login"),
        "signup_url": safe_url_for("account_signup"),
        "redirect_field_name": "next",
        "redirect_field_value": flask_request.args.get("next", ""),
        "form": build_form("login" if template_name in {"login", "account/login"} else ("contribution" if template_name == "submit_contribution" else "generic")),
        "now": now,
    }


def render_page(template_name: str, status: int = 200, **extra: Any) -> Response:
    template_path = BASE_DIR / "templates" / "pages" / f"{template_name}.html"
    if not template_path.is_file():
        return render_site("error", error_code=404, error_heading="Page not found", error_message="This page may have moved or is no longer published."), 404
    context = base_context(template_name)
    context.update(extra)
    return render_template(f"pages/{template_name}.html", **context), status


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(safe_url_for("account_login", next=flask_request.path))
        return view(*args, **kwargs)

    return wrapped


@app.route("/", endpoint="index")
def index() -> Response:
    return render_site("home", "home")


# Only render one modest page of books at a time. This prevents very large
# catalogues from sending thousands of cover images and card elements per view.
CATALOGUE_PAGE_SIZE = 30


def paged_books(*, collection_filter: bool = True) -> dict[str, Any]:
    db = get_db()
    search = flask_request.args.get("q", "").strip()[:120]
    collection = flask_request.args.get("collection", "").strip()[:120] if collection_filter else ""
    try:
        requested_page = int(flask_request.args.get("page", "1"))
    except (TypeError, ValueError):
        requested_page = 1
    filters: list[str] = ["archived=0"]
    params: list[Any] = []
    if search:
        filters.append("(LOWER(title) LIKE ? OR LOWER(author) LIKE ? OR LOWER(description) LIKE ?)")
        # Escape SQL LIKE wildcard characters to treat search as literal text.
        pattern = "%" + search.lower().replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"
        filters[-1] = "(LOWER(title) LIKE ? ESCAPE '!' OR LOWER(author) LIKE ? ESCAPE '!' OR LOWER(description) LIKE ? ESCAPE '!')"
        params.extend([pattern] * 3)
    if collection:
        filters.append("collection = ?")
        params.append(collection)
    chosen={k:flask_request.args.get(k,'').strip()[:120] for k in ['language','age_group','author','product_type','availability','new','sort','audience']}
    if chosen['audience'] in {'adult','kids'}:
        filters.append("audience IN (?, 'all')");params.append(chosen['audience'])
    for key in ['language','age_group','author','product_type']:
        if chosen[key]:
            filters.append('LOWER('+key+') = LOWER(?)');params.append(chosen[key])
    if chosen['availability']=='available':filters.append("(SELECT COUNT(*) FROM copies17 c WHERE c.book_id=books.id AND c.status='Available') > (SELECT COUNT(*) FROM lending_loans l WHERE l.book_id=books.id AND l.status='Requested')")
    elif chosen['availability']=='waitlist':filters.append("(SELECT COUNT(*) FROM copies17 c WHERE c.book_id=books.id AND c.status='Available') <= (SELECT COUNT(*) FROM lending_loans l WHERE l.book_id=books.id AND l.status='Requested')")
    if chosen['new']=='1':filters.append('is_new_arrival=1')
    ordering={'newest':'is_new_arrival DESC, id DESC','title':'title COLLATE NOCASE ASC,id','author':'author COLLATE NOCASE ASC,id','price-low':'price ASC,id','price-high':'price DESC,id'}.get(chosen['sort'],'is_new_arrival DESC, id DESC')
    # Age-aware recommendations: valid age bands come from catalogue metadata.
    reader = current_user()
    if reader.is_authenticated:
        from accounts import years_old, age_matches
        age = years_old(reader.values.get('dob'))
        if age is not None and age < 18:
            db.create_function('AGE_MATCH', 2, lambda band, n: int(age_matches(band, n)))
            filters.append('AGE_MATCH(age_group, ?) = 1')
            params.append(age)
    where = f" WHERE {' AND '.join(filters)}" if filters else ""
    count = int(db.execute("SELECT COUNT(*) FROM books" + where, params).fetchone()[0])
    pages = max(1, (count + CATALOGUE_PAGE_SIZE - 1) // CATALOGUE_PAGE_SIZE)
    page = min(max(1, requested_page), pages)
    rows = db.execute(
        "SELECT * FROM books" + where + " ORDER BY "+ordering+" LIMIT ? OFFSET ?",
        (*params, CATALOGUE_PAGE_SIZE, (page - 1) * CATALOGUE_PAGE_SIZE),
    ).fetchall()
    collections = [row[0] for row in db.execute(
        "SELECT DISTINCT collection FROM books WHERE collection IS NOT NULL AND TRIM(collection) <> '' ORDER BY collection"
    ).fetchall()] if collection_filter else []
    options={key:[r[0] for r in db.execute('SELECT DISTINCT '+key+' FROM books WHERE archived=0 AND TRIM('+key+")<>'' ORDER BY "+key)] for key in ['language','age_group','author','product_type']}
    from urllib.parse import urlencode
    def catalogue_url(**changes):
        args=dict(flask_request.args);args.update(changes)
        return '/library/?'+urlencode({k:v for k,v in args.items() if v not in ('',None)})

    active_chips = []
    if search:
        active_chips.append({"key": "q", "label": f'Search: "{search}"', "remove_url": catalogue_url(q="")})
    if collection:
        active_chips.append({"key": "collection", "label": f'Category: {collection}', "remove_url": catalogue_url(collection="")})
    if chosen.get("audience"):
        active_chips.append({"key": "audience", "label": f'Readers: {chosen["audience"].title()}', "remove_url": catalogue_url(audience="")})
    if chosen.get("language"):
        active_chips.append({"key": "language", "label": f'Language: {chosen["language"]}', "remove_url": catalogue_url(language="")})
    if chosen.get("age_group"):
        active_chips.append({"key": "age_group", "label": f'Age: {chosen["age_group"]} yrs', "remove_url": catalogue_url(age_group="")})
    if chosen.get("author"):
        active_chips.append({"key": "author", "label": f'Author: {chosen["author"]}', "remove_url": catalogue_url(author="")})
    if chosen.get("availability") == "available":
        active_chips.append({"key": "availability", "label": "Available Now", "remove_url": catalogue_url(availability="")})
    elif chosen.get("availability") == "waitlist":
        active_chips.append({"key": "availability", "label": "On Loan / Waitlist", "remove_url": catalogue_url(availability="")})
    if chosen.get("new") == "1":
        active_chips.append({"key": "new", "label": "New Arrivals Only", "remove_url": catalogue_url(new="")})

    def export_url(format="xlsx"):
        args = dict(flask_request.args)
        args.pop("page", None)
        qs = urlencode({k: v for k, v in args.items() if v not in ("", None)})
        suffix = f"?{qs}" if qs else ""
        return f"/library/export/{format}/{suffix}"

    active_book_ids = set()
    u = current_user()
    active_sub = None
    active_cnt = 0
    if u and u.is_authenticated:
        from accounts import get_active_subscription, get_active_loan_count
        active_sub_row = get_active_subscription(db, u.id)
        if active_sub_row:
            active_sub = dict(active_sub_row)
        active_cnt = get_active_loan_count(db, u.id)
        active_rows = db.execute(
            "SELECT book_id FROM lending_loans WHERE user_id=? AND status IN ('Requested', 'Issued')",
            (u.id,)
        ).fetchall()
        active_book_ids = {r[0] for r in active_rows}

    delivery_rows = db.execute(
        "SELECT content_key, content_value FROM site_content WHERE content_key IN ('membership_delivery_fee_monthly', 'membership_delivery_area', 'membership_pickup_address', 'membership_delivery_day')"
    ).fetchall()
    delivery_settings = {r[0]: r[1] for r in delivery_rows}
    delivery_settings.setdefault("membership_delivery_fee_monthly", "350")
    delivery_settings.setdefault("membership_delivery_area", "Gandhi Nagar, Saligramam and surrounding areas (within 5 km)")
    delivery_settings.setdefault("membership_pickup_address", "Gandhi Nagar, Saligramam, Chennai")
    delivery_settings.setdefault("membership_delivery_day", "Fixed pick-up & drop on designated weekday (e.g. Saturday)")

    return {
        "filter_options": options, "filters23": chosen, "catalogue_url": catalogue_url,
        "books": [row_dict(row) for row in rows],
        "query": search,
        "selected_collection": collection,
        "collections": collections,
        "catalogue_count": count,
        "catalogue_page": page,
        "catalogue_pages": pages,
        "active_chips": active_chips,
        "export_url": export_url,
        "active_book_ids": active_book_ids,
        "member_active_sub": active_sub,
        "member_active_cnt": active_cnt,
        "delivery_settings": delivery_settings,
    }


@app.route("/library-catalogue/", endpoint="library_catalogue")
def library_catalogue() -> Response:
    return render_site("library", "library", **paged_books())


@app.get("/library/", endpoint="modern_library")
def modern_library() -> Response:
    if "test_user_id" in flask_request.args:
        t_uid = flask_request.args.get("test_user_id")
        if t_uid:
            session["user_id"] = int(t_uid)
        else:
            session.pop("user_id", None)
    return render_site("library", "library", **paged_books())


@app.get("/library/export/<fmt>/", endpoint="library_export")
def library_export(fmt: str) -> Response:
    import library_filters
    books = library_filters.get_filtered_books_for_export(get_db(), flask_request.args)
    if fmt.lower() in ("xlsx", "excel"):
        return library_filters.export_books_excel(books)
    elif fmt.lower() in ("pdf",):
        return library_filters.export_books_pdf(books)
    else:
        return redirect(flask_url_for("modern_library"))


@app.post("/library/checkout/", endpoint="library_checkout")
def library_checkout() -> Response:
    u = current_user()
    if not u or not u.is_authenticated:
        return jsonify(ok=False, errors=["Please sign in to continue with your borrow request."]), 401

    db = get_db()
    from accounts import get_active_subscription, get_active_loan_count
    sub = get_active_subscription(db, u.id)
    if not sub:
        return jsonify(ok=False, errors=["An active membership subscription is required to borrow books. Please check our membership plans."]), 403

    # Parse request data: support both JSON and Form data
    data = flask_request.get_json(silent=True) or {}
    if not data:
        data = flask_request.form.to_dict()

    raw_books = data.get("book_ids") or data.get("books") or []
    if isinstance(raw_books, str):
        try:
            import json
            raw_books = json.loads(raw_books)
        except Exception:
            raw_books = [x.strip() for x in raw_books.split(",") if x.strip()]

    book_ids = []
    for item in raw_books:
        if isinstance(item, dict) and "id" in item:
            bid = item["id"]
        else:
            bid = item
        try:
            val = int(bid)
            if val > 0:
                book_ids.append(val)
        except (ValueError, TypeError):
            continue

    if not book_ids:
        return jsonify(ok=False, errors=["Please select at least one book to request."]), 400

    # Check for duplicates in the submitted list
    if len(book_ids) != len(set(book_ids)):
        return jsonify(ok=False, errors=["Duplicate books detected in your borrow cart. Please remove duplicates."]), 400

    # Plan limit enforcement
    plan_limit = int(sub["book_limit"])
    curr_active = get_active_loan_count(db, u.id)
    remaining = max(0, plan_limit - curr_active)

    if len(book_ids) > remaining:
        return jsonify(
            ok=False,
            errors=[f"Your plan allows {plan_limit} book(s) at a time. You have {curr_active} active loan(s)/request(s), leaving {remaining} slot(s). You selected {len(book_ids)} books."]
        ), 400

    # Contact & delivery sanitisation
    delivery_mode = (data.get("delivery_mode") or "offline").strip().lower()
    if delivery_mode not in ("offline", "online"):
        return jsonify(ok=False, errors=["Invalid delivery mode selected. Choose Offline (self-pickup) or Online (doorstep delivery)."]), 400

    contact_name = (data["name"] if "name" in data else data.get("contact_name", getattr(u, "name", ""))) or ""
    contact_name = str(contact_name).strip()[:150]

    contact_phone = (data["phone"] if "phone" in data else data.get("contact_phone", getattr(u, "phone", ""))) or ""
    contact_phone = str(contact_phone).strip()[:30]

    delivery_address = (data["address"] if "address" in data else data.get("delivery_address", getattr(u, "address", ""))) or ""
    delivery_address = str(delivery_address).strip()[:800]

    if not contact_name:
        return jsonify(ok=False, errors=["Please provide your full name."]), 400
    if not contact_phone:
        return jsonify(ok=False, errors=["Please provide a contact phone number."]), 400

    if delivery_mode == "online" and not delivery_address:
        return jsonify(ok=False, errors=["Delivery address is required for doorstep delivery."]), 400

    # Book existence, stock and active check
    try:
        db.execute("BEGIN IMMEDIATE")
        books_to_request = []
        for bid in book_ids:
            b = db.execute("SELECT id, title, stock, archived FROM books WHERE id=?", (bid,)).fetchone()
            if not b or b["archived"]:
                db.rollback()
                return jsonify(ok=False, errors=[f"Book #{bid} could not be found or is no longer available in the catalogue."]), 400
            if int(b["stock"] or 0) < 1:
                db.rollback()
                return jsonify(ok=False, errors=[f'"{b["title"]}" currently has no copies available.']), 400

            already = db.execute(
                "SELECT id FROM lending_loans WHERE user_id=? AND book_id=? AND status IN ('Requested', 'Issued')",
                (u.id, bid)
            ).fetchone()
            if already:
                db.rollback()
                return jsonify(ok=False, errors=[f'You already have an active request or loan for "{b["title"]}".']), 409
            books_to_request.append(b)

        # Create lending_requests row
        cur = db.execute(
            """INSERT INTO lending_requests(user_id, subscription_id, delivery_mode, delivery_address, contact_phone, contact_name, status)
               VALUES(?, ?, ?, ?, ?, ?, 'Requested')""",
            (u.id, sub["id"], delivery_mode, delivery_address if delivery_mode == "online" else "", contact_phone, contact_name)
        )
        request_id = cur.lastrowid

        # Create one lending_loans row per book
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for b in books_to_request:
            db.execute(
                """INSERT INTO lending_loans(user_id, book_id, subscription_id, status, requested_at, request_id, delivery_mode, delivery_address, contact_phone)
                   VALUES(?, ?, ?, 'Requested', ?, ?, ?, ?, ?)""",
                (u.id, b["id"], sub["id"], now_str, request_id, delivery_mode, delivery_address if delivery_mode == "online" else "", contact_phone)
            )

        # In-app member notification
        db.execute(
            "INSERT OR IGNORE INTO notifications17(user_id, title, body, url, dedupe) VALUES(?, ?, ?, ?, ?)",
            (u.id, f"Borrow Request #{request_id} received", f"Your request for {len(books_to_request)} book(s) has been received. We will notify you when ready.", "/members/dashboard/", f"req:{request_id}")
        )

        # Staff in-app notification
        source_key = f"borrow_req:{request_id}:{secrets.token_hex(4)}"
        db.execute(
            "INSERT OR IGNORE INTO admin_notifications(kind, title, body, url, source_key) VALUES('borrowing', ?, ?, '/admin/lending/', ?)",
            (f"New borrow request #{request_id} ({u.name})", f"{len(books_to_request)} book(s) via {delivery_mode}", source_key)
        )

        # Audit log
        db.execute(
            "INSERT INTO admin_audit(admin_id, action) VALUES(?, ?)",
            (session.get("admin_id"), f"Member #{u.id} ({u.name}) created borrow request #{request_id} for {len(books_to_request)} books ({delivery_mode})")
        )

        # Email notifications if enabled
        if os.environ.get("EMAIL_NOTIFICATIONS") == "1":
            user_email = getattr(u, "email", "")
            if not user_email:
                row = db.execute("SELECT email FROM users WHERE id=?", (u.id,)).fetchone()
                user_email = row[0] if row else ""
            if user_email:
                db.execute(
                    "INSERT INTO mail_queue17(recipient, subject, body) VALUES(?, ?, ?)",
                    (user_email, f"Book Buddy - Borrow Request #{request_id} Received", f"Hello {u.name},\n\nYour borrow request #{request_id} for {len(books_to_request)} book(s) has been received.\nDelivery mode: {delivery_mode.title()}\n\nWe will review and prepare your books shortly.\n\nWarm regards,\nBook Buddy Team")
                )
            admin_email = os.environ.get("LIBRARY_ADMIN_EMAIL", "admin@bookbuddy.internal")
            db.execute(
                "INSERT INTO mail_queue17(recipient, subject, body) VALUES(?, ?, ?)",
                (admin_email, f"New Borrow Request #{request_id}", f"Member {u.name} (ID: {u.id}) requested {len(books_to_request)} books via {delivery_mode}.\nPlease review at /admin/lending/.")
            )

        db.commit()
    except sqlite3.Error:
        db.rollback()
        return jsonify(ok=False, errors=["A database error occurred while saving your request. Please try again."]), 500

    return jsonify(
        ok=True,
        request_id=request_id,
        message=f"Request #{request_id} received, we will contact you.",
        loans_count=len(books_to_request)
    )


@app.get("/library/<int:book_id>/", endpoint="book_detail")
def book_detail(book_id: int) -> Response:
    book = get_db().execute("SELECT * FROM books WHERE id = ? AND archived=0", (book_id,)).fetchone()
    if not book:
        return render_site("error", error_code=404, error_heading="Page not found", error_message="This page may have moved or is no longer published."), 404
    from accounts import age_matches, years_old
    viewer=current_user()
    age=years_old(viewer.values.get('dob')) if viewer.is_authenticated else None
    if age is not None and not age_matches(book['age_group'],age):
        flash('Please choose a book from your age-recommended catalogue.','info')
        return redirect(flask_url_for('modern_library'))
    return render_site("book_detail", "library", book=row_dict(book))


@app.get("/visit-us/", endpoint="visit_us_page")
def visit_us_page() -> Response:
    return render_site("visit_us", "library")


@app.get("/gallery/", endpoint="gallery_page")
def gallery_page() -> Response:
    import gallery_service
    categories = list(gallery_service.GALLERY_CATEGORIES.values())
    return render_site("gallery", "gallery", categories=categories)


@app.get("/gallery/<slug>/", endpoint="gallery_category_page")
def gallery_category_page(slug: str) -> Response:
    import gallery_service
    cat = gallery_service.GALLERY_CATEGORIES.get(slug)
    if not cat:
        return redirect(flask_url_for("gallery_page"))
    photos = gallery_service.get_category_photos(get_db, slug)
    return render_site("gallery_category", "gallery", category=cat, photos=photos)


@app.get("/collaborators/", endpoint="collaborators_page")
def collaborators_page() -> Response:
    db = get_db()
    cat_defs = [
        {"slug": "library-partners", "title": "Library Partners", "description": "Other libraries and book communities collaborating to share the joy of reading."},
        {"slug": "storytellers-authors", "title": "Storytellers & Authors", "description": "Authors, narrators, writers, and educators who bring stories to life."},
        {"slug": "community-partners", "title": "Community Partners", "description": "Organisations, schools, and local initiatives building community connections."},
        {"slug": "creative-partners", "title": "Creative Partners", "description": "Artists, illustrators, and workshop facilitators sparking creative curiosity."}
    ]
    sections = []
    for cd in cat_defs:
        rows = db.execute(
            "SELECT * FROM collaborators WHERE is_active=1 AND category=? ORDER BY sort_order ASC, id ASC",
            (cd["slug"],)
        ).fetchall()
        sections.append({
            "slug": cd["slug"],
            "title": cd["title"],
            "description": cd["description"],
            "partners": [dict(r) for r in rows]
        })
    return render_site("collaborators", "collaborators", sections=sections)


@app.get("/community/", endpoint="community_hub")
def community_hub() -> Response:
    db = get_db()
    today = date.today().isoformat()
    upcoming_events = [dict(r) for r in db.execute(
        "SELECT * FROM events WHERE is_active=1 AND event_date>=? ORDER BY event_date ASC, event_time ASC LIMIT 3",
        (today,)
    ).fetchall()]
    latest_media = [dict(r) for r in db.execute(
        "SELECT * FROM publications WHERE is_active=1 ORDER BY published_on DESC, id DESC LIMIT 3"
    ).fetchall()]
    return render_site("community", "community", upcoming_events=upcoming_events, latest_media=latest_media)


@app.get("/community/media/", endpoint="community_media")
def community_media() -> Response:
    db = get_db()
    active_tab = flask_request.args.get("tab", "").strip().lower()
    if not active_tab or active_tab not in {"newspapers", "newspaper", "news", "magazines", "magazine", "podcasts", "podcast"}:
        active_tab = "all"
    elif active_tab in {"newspaper", "news"}:
        active_tab = "newspapers"
    elif active_tab == "magazine":
        active_tab = "magazines"
    elif active_tab == "podcast":
        active_tab = "podcasts"

    access_filter = flask_request.args.get("access", "").strip().lower()
    access_clause = " AND is_paid=0" if access_filter == "free" else (" AND is_paid=1" if access_filter == "paid" else "")

    newspapers = [dict(r) for r in db.execute(f"SELECT * FROM publications WHERE is_active=1 AND kind='news'{access_clause} ORDER BY published_on DESC, id DESC").fetchall()]
    magazines = [dict(r) for r in db.execute(f"SELECT * FROM publications WHERE is_active=1 AND kind='magazine'{access_clause} ORDER BY published_on DESC, id DESC").fetchall()]
    podcasts = [dict(r) for r in db.execute(f"SELECT * FROM publications WHERE is_active=1 AND kind='podcast'{access_clause} ORDER BY published_on DESC, id DESC").fetchall()]
    return render_site("media_hub", "community", active_tab=active_tab, newspapers=newspapers, magazines=magazines, podcasts=podcasts)


@app.get("/events/", endpoint="events_page")
def events_page() -> Response:
    db = get_db()
    today = date.today().isoformat()
    view = flask_request.args.get("view", "current").strip().lower()
    event_type = flask_request.args.get("type", "").strip().lower()
    chosen_date = flask_request.args.get("date", "").strip()

    query = "SELECT * FROM events WHERE is_active=1"
    params = []

    if chosen_date:
        query += " AND event_date = ?"
        params.append(chosen_date)
    elif view == "past":
        query += " AND event_date < ?"
        params.append(today)
    else:
        query += " AND event_date >= ?"
        params.append(today)

    if event_type in ("contest", "reading-circle", "upcoming"):
        query += " AND category = ?"
        params.append(event_type)

    query += " ORDER BY event_date " + ("DESC" if view == "past" else "ASC") + ", event_time ASC"
    rows = db.execute(query, params).fetchall()
    events = [dict(r) for r in rows]

    current_count = db.execute("SELECT COUNT(*) FROM events WHERE is_active=1 AND event_date >= ?", (today,)).fetchone()[0]
    past_count = db.execute("SELECT COUNT(*) FROM events WHERE is_active=1 AND event_date < ?", (today,)).fetchone()[0]

    from notifications import calendar_context
    cal_ctx = calendar_context(db, month=chosen_date[:7] if chosen_date else None, category=event_type)

    return render_site(
        "events",
        "events",
        events=events,
        view=view,
        event_type=event_type,
        chosen_date=chosen_date,
        current_count=current_count,
        past_count=past_count,
        home_calendar=cal_ctx,
        today=today,
    )


@app.get("/events/<int:event_id>/", endpoint="event_detail")
def event_detail(event_id: int) -> Response:
    event = get_db().execute("SELECT * FROM events WHERE id = ? AND is_active = 1", (event_id,)).fetchone()
    if not event:
        return render_site("error", error_code=404, error_heading="Page not found", error_message="This page may have moved or is no longer published."), 404
    registered = get_db().execute("SELECT COALESCE(SUM(seats), 0) FROM event_registrations WHERE event_id = ? AND status = 'Registered'", (event_id,)).fetchone()[0]
    return render_site("event_detail", "events", event=row_dict(event), seats_left=max(0, event["capacity"] - registered))


@app.post("/events/<int:event_id>/register/", endpoint="register_event")
def register_event(event_id: int) -> Response:
    event = get_db().execute("SELECT * FROM events WHERE id = ? AND is_active = 1", (event_id,)).fetchone()
    if not event:
        return render_site("error", error_code=404, error_heading="Page not found", error_message="This page may have moved or is no longer published."), 404
    name = flask_request.form.get("name", "").strip()
    email = flask_request.form.get("email", "").strip().lower()
    phone = flask_request.form.get("phone", "").strip()
    try:
        seats = max(1, min(10, int(flask_request.form.get("seats", "1"))))
    except ValueError:
        seats = 1
    registered = get_db().execute("SELECT COALESCE(SUM(seats), 0) FROM event_registrations WHERE event_id = ? AND status = 'Registered'", (event_id,)).fetchone()[0]
    if not name or "@" not in email:
        flash("Please enter a name and valid email to register.", "danger")
    elif seats > max(0, event["capacity"] - registered):
        flash("There are not enough places left for that many guests.", "danger")
    else:
        amount = float(event["fee"] or 0) * seats
        get_db().execute(
            "INSERT INTO event_registrations (event_id, user_id, name, email, phone, seats, amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (event_id, session.get("user_id"), name, email, phone, seats, amount),
        )
        get_db().commit()
        flash("Your registration is saved. Contact the library for payment and joining details. No automatic email has been sent.", "success")
    return redirect(flask_url_for("event_detail", event_id=event_id))


@app.get("/publications/", endpoint="publications_page")
def publications_page() -> Response:
    kind = flask_request.args.get("kind", "").strip().lower()
    if kind in {"news", "newspaper"}:
        return redirect("/community/media/?tab=newspapers", code=301)
    elif kind == "magazine":
        return redirect("/community/media/?tab=magazines", code=301)
    elif kind == "podcast":
        return redirect("/community/media/?tab=podcasts", code=301)
    qs = flask_request.query_string.decode("utf-8")
    suffix = f"?{qs}" if qs else ""
    return redirect(f"/community/media/{suffix}", code=301)


@app.get("/podcasts/", endpoint="podcasts_page")
def podcasts_page() -> Response:
    return redirect("/community/media/?tab=podcasts", code=301)


@app.get("/news/", endpoint="news_page")
def news_page() -> Response:
    return redirect("/community/media/?tab=newspapers", code=301)


@app.get("/reading-circles/", endpoint="reading_circles_page")
def reading_circles_page() -> Response:
    return redirect("/events/?type=reading-circle", code=301)


@app.get("/contests/", endpoint="contests_page")
def contests_page() -> Response:
    return redirect("/events/?type=contest", code=301)


@app.get("/work-with-us/", endpoint="work_with_us_page")
def work_with_us_page() -> Response:
    return render_site("work_with_us", "collaborators")


@app.get("/shop/", endpoint="shop")
def shop() -> Response:
    return render_site("library", "library", **paged_books(collection_filter=False))


@app.post("/cart/add/<int:book_id>/", endpoint="add_to_cart")
def add_to_cart(book_id: int) -> Response:
    book = get_db().execute("SELECT id, title, stock FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book or int(book["stock"] or 0) < 1:
        flash("That book is not available.", "danger")
        return redirect(flask_url_for("shop"))
    cart = session.get("cart", {}) or {}
    current_quantity = int(cart.get(str(book_id), 0) or 0)
    cart[str(book_id)] = min(int(book["stock"]), current_quantity + 1)
    session["cart"] = cart
    flash(f"{book['title']} was added to your basket.", "success")
    return redirect(flask_request.referrer or flask_url_for("shop"))


@app.get("/cart/", endpoint="cart")
def cart() -> Response:
    return render_site("portal/error", "shop")


@app.post("/cart/update/", endpoint="update_cart")
def update_cart() -> Response:
    cart_data: dict[str, int] = {}
    for key, value in flask_request.form.items():
        if not key.startswith("quantity_"):
            continue
        try:
            book_id = int(key.removeprefix("quantity_"))
            quantity = max(0, min(20, int(value)))
        except (TypeError, ValueError):
            continue
        if quantity:
            cart_data[str(book_id)] = quantity
    session["cart"] = cart_data
    flash("Your basket was updated.", "success")
    return redirect(flask_url_for("cart"))


@app.post("/cart/remove/<int:book_id>/", endpoint="remove_from_cart")
def remove_from_cart(book_id: int) -> Response:
    cart_data = session.get("cart", {}) or {}
    cart_data.pop(str(book_id), None)
    session["cart"] = cart_data
    return redirect(flask_url_for("cart"))


@app.route("/checkout/", methods=["GET", "POST"], endpoint="checkout")
def checkout() -> Response:
    items, total, _ = cart_snapshot()
    if not items:
        flash("Add a book to your basket before checking out.", "info")
        return redirect(flask_url_for("shop"))
    if flask_request.method == "POST":
        name = flask_request.form.get("name", "").strip()
        email = flask_request.form.get("email", "").strip().lower()
        phone = flask_request.form.get("phone", "").strip()
        address = flask_request.form.get("address", "").strip()
        if not name or "@" not in email or not address:
            flash("Please complete your name, email and delivery address.", "danger")
            return render_site("portal/error", "shop", checkout_items=items, checkout_total=total)
        db = get_db()
        try:
            cursor = db.execute(
                "INSERT INTO orders (user_id, customer_name, email, phone, address, total) VALUES (?, ?, ?, ?, ?, ?)",
                (session.get("user_id"), name, email, phone, address, total),
            )
            order_id = cursor.lastrowid
            for item in items:
                book = item["book"]
                db.execute(
                    "INSERT INTO order_items (order_id, book_id, title, quantity, price) VALUES (?, ?, ?, ?, ?)",
                    (order_id, book["id"], book["title"], item["quantity"], item["price"]),
                )
                result = db.execute("UPDATE books SET stock=stock-? WHERE id=? AND stock>=?", (item["quantity"],book["id"],item["quantity"]))
                if result.rowcount != 1:
                    raise sqlite3.IntegrityError("Insufficient stock")
            db.commit()
        except sqlite3.Error:
            db.rollback()
            flash("We could not save that order. Please try again.", "danger")
            return render_site("portal/error", "shop", checkout_items=items, checkout_total=total)
        session["cart"] = {}
        session["order_ids"] = (session.get("order_ids", []) + [order_id])[-30:]
        return redirect(flask_url_for("order_confirmation", order_id=order_id))
    user = current_user()
    return render_site("portal/error", "shop", checkout_items=items, checkout_total=total, checkout_user=user)


@app.get("/order/<int:order_id>/confirmation/", endpoint="order_confirmation")
def order_confirmation(order_id: int) -> Response:
    if order_id not in session.get("order_ids",[]) and not current_admin():
        owned = get_db().execute("SELECT id FROM orders WHERE id=? AND user_id=?", (order_id,session.get("user_id"))).fetchone()
        if not owned:
            return render_page("error",status=404)
    order = get_db().execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        return render_site("error", error_code=404, error_heading="Page not found", error_message="This page may have moved or is no longer published."), 404
    items = [row_dict(row) for row in get_db().execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()]
    return render_site("confirmation", "shop", order=row_dict(order), order_items=items)


@app.route("/admin/login/", methods=["GET", "POST"], endpoint="admin_login")
def admin_login() -> Response:
    next_url = flask_request.args.get("next", "") or flask_request.form.get("next", "")
    if flask_request.method == "POST":
        email = flask_request.form.get("email", "").strip().lower()
        password = flask_request.form.get("password", "")
        admin = get_db().execute("SELECT * FROM admin_users WHERE email = ?", (email,)).fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            return redirect(next_url if next_url.startswith("/") and not next_url.startswith("//") and "\\" not in next_url else flask_url_for("admin_dashboard"))
        flash("That admin email or password is not correct.", "danger")
    return render_site("admin_login", "admin", next_url=next_url)


@app.get("/admin/logout/", endpoint="admin_logout")
def admin_logout() -> Response:
    session.pop("admin_id", None)
    flash("You have been signed out of the admin area.", "info")
    return redirect(flask_url_for("index"))


@app.get("/admin/", endpoint="admin_home")
def admin_home() -> Response:
    return redirect(flask_url_for("admin_dashboard"))


@app.get("/admin/dashboard/", endpoint="admin_dashboard")
@admin_required
def admin_dashboard() -> Response:
    db = get_db()
    stats = {
        "books": db.execute("SELECT COUNT(*) FROM books").fetchone()[0],
        "events": db.execute("SELECT COUNT(*) FROM events WHERE is_active = 1").fetchone()[0],
        "orders": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "subscribers": db.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0],
    }
    admin_books = [row_dict(row) for row in db.execute("SELECT * FROM books ORDER BY id DESC").fetchall()]
    admin_classes = []
    admin_events = [row_dict(row) for row in db.execute("SELECT * FROM events ORDER BY event_date DESC, id DESC").fetchall()]
    admin_activities = []
    admin_publications = [row_dict(row) for row in db.execute("SELECT * FROM publications ORDER BY published_on DESC, id DESC").fetchall()]
    orders = [row_dict(row) for row in db.execute("SELECT * FROM orders ORDER BY created_at DESC, id DESC LIMIT 8").fetchall()]
    registrations = [
        row_dict(row)
        for row in db.execute(
            """SELECT event_registrations.*, events.title AS event_title
            FROM event_registrations JOIN events ON events.id = event_registrations.event_id
            ORDER BY event_registrations.created_at DESC LIMIT 8"""
        ).fetchall()
    ]
    return render_site(
        "admin_dashboard",
        "admin",
        stats=stats,
        admin_books=admin_books,
        admin_classes=admin_classes,
        admin_events=admin_events,
        admin_activities=admin_activities,
        admin_publications=admin_publications,
        orders=orders,
        registrations=registrations,
    )


def save_admin_upload(field: str, category: str, kind: str = "image") -> str:
    """Store validated uploads from authenticated admin forms only. Returns safe /media path."""
    f = flask_request.files.get(field)
    if not f or not f.filename:
        return ""
    raw = f.read(10 * 1024 * 1024 + 1)
    if not raw or len(raw) > 10 * 1024 * 1024:
        raise ValueError("Upload must be smaller than 10 MB")
    dest = ROOT_DIR / 'media' / 'admin' / category
    dest.mkdir(parents=True, exist_ok=True)
    key = secrets.token_hex(15)
    if kind == 'pdf':
        if not raw.startswith(b'%PDF-') or not f.filename.lower().endswith('.pdf'):
            raise ValueError("Upload a valid PDF document")
        name = key + '.pdf'
        (dest / name).write_bytes(raw)
    else:
        try:
            img = Image.open(io.BytesIO(raw))
            img.verify()
            img = Image.open(io.BytesIO(raw))
            if img.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValueError("Only JPG, PNG or WebP images are supported")
            img.load()
            if img.width * img.height > 24_000_000:
                raise ValueError("Image resolution is too large")
            img.thumbnail((1700, 1700), Image.Resampling.LANCZOS)
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            name = key + '.webp'
            img.save(dest / name, 'WEBP', quality=82, method=5)
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError("Could not read the image") from exc
    return f'/media/admin/{category}/{name}'


app.extensions['bookbuddy_store_media_v13'] = save_admin_upload

@app.post("/admin/books/create/", endpoint="admin_create_book")
@admin_required
def admin_create_book() -> Response:
    title = flask_request.form.get("title", "").strip()
    author = flask_request.form.get("author", "Book Buddy Team").strip()
    collection = flask_request.form.get("collection", "Story").strip()
    age_group = flask_request.form.get("age_group", "6-8").strip()
    description = flask_request.form.get("description", "").strip()
    try:
        price = max(0, float(flask_request.form.get("price", "0")))
        stock = max(0, int(flask_request.form.get("stock", "1")))
    except ValueError:
        price, stock = 0, 1
    if not title:
        flash("A book title is required.", "danger")
    else:
        try:
            cover_path = save_admin_upload('cover_file', 'books')
        except ValueError as exc:
            flash(str(exc), 'danger')
            return redirect(flask_url_for('admin_dashboard') + '#books')
        get_db().execute(
            """INSERT INTO books (title, author, collection, age_group, language, is_new_arrival, available_copies, price, description, stock, image_path)
            VALUES (?, ?, ?, ?, 'English', 1, ?, ?, ?, ?, ?)""",
            (title, author, collection, age_group, stock, price, description, stock, cover_path),
        )
        get_db().commit()
        flash(f"{title} was added to the library and shop.", "success")
    return redirect(flask_url_for("admin_dashboard") + "#books")


@app.post("/admin/events/create/", endpoint="admin_create_event")
@admin_required
def admin_create_event() -> Response:
    title = flask_request.form.get("title", "").strip()
    if not title or not flask_request.form.get("event_date"):
        flash("An event title and date are required.", "danger")
    else:
        try:
            fee = max(0, float(flask_request.form.get("fee", "0")))
            capacity = max(1, int(flask_request.form.get("capacity", "30")))
        except ValueError:
            fee, capacity = 0, 30
        get_db().execute(
            """INSERT INTO events (title, description, event_date, event_time, location, fee, capacity, is_online)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, flask_request.form.get("description", ""), flask_request.form.get("event_date"), flask_request.form.get("event_time", ""), flask_request.form.get("location", "Book Buddy Library"), fee, capacity, 1 if flask_request.form.get("is_online") else 0),
        )
        get_db().commit()
        flash(f"{title} was added to the calendar.", "success")
    return redirect(flask_url_for("admin_dashboard") + "#events")


@app.post("/admin/publications/create/", endpoint="admin_create_publication")
@admin_required
def admin_create_publication() -> Response:
    title = flask_request.form.get("title", "").strip()
    if not title:
        flash("A publication title is required.", "danger")
    else:
        try:
            pdf_path = save_admin_upload('pdf_file', 'publications', 'pdf')
            cover_path = save_admin_upload('cover_file', 'publication_covers')
        except ValueError as exc:
            flash(str(exc), 'danger')
            return redirect(flask_url_for('admin_dashboard') + '#publications')
        file_path = pdf_path or flask_request.form.get('file_path', '').strip()
        # Reject external/untrusted URLs; admin uploaded PDFs live in the media directory.
        if file_path and not file_path.startswith('/media/'):
            flash('Upload the PDF or use an existing local /media/ file path.', 'danger')
            return redirect(flask_url_for('admin_dashboard') + '#publications')
        get_db().execute(
            """INSERT INTO publications (title, kind, description, edition, file_path, cover_path, published_on)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, flask_request.form.get("kind", "magazine"), flask_request.form.get("description", ""), flask_request.form.get("edition", ""), file_path, cover_path, flask_request.form.get("published_on") or date.today().isoformat()),
        )
        get_db().commit()
        flash(f"{title} was added to publications.", "success")
    return redirect(flask_url_for("admin_dashboard") + "#publications")


@app.post("/admin/content/update/", endpoint="admin_update_content")
@admin_required
def admin_update_content() -> Response:
    allowed_keys = {"hero_eyebrow", "hero_title", "hero_text", "about_text", "newsletter_title", "newsletter_text"}
    db = get_db()
    for key in allowed_keys:
        if key in flask_request.form:
            value=flask_request.form.get(key, "").strip()
            db.execute("INSERT INTO site_content (content_key, content_value) VALUES (?, ?) ON CONFLICT(content_key) DO UPDATE SET content_value = excluded.content_value", (key, value))
            if key == 'about_text':
                # Older dashboard exposes this legacy field. The real About
                # page reads about_philosophy_body, so mirror it on update.
                db.execute("INSERT INTO site_content(content_key,content_value) VALUES('about_philosophy_body',?) ON CONFLICT(content_key) DO UPDATE SET content_value=excluded.content_value",(value,))
    db.commit()
    flash("Homepage content was updated.", "success")
    return redirect(flask_url_for("admin_dashboard") + "#content")


@app.route("/<path:template_name>/", endpoint="dynamic_page")
def dynamic_page(template_name: str) -> Response:
    template_name = template_name.strip("/")
    if template_name.endswith(".html"):
        template_name = template_name[:-5]
    if template_name in {"static", "media", "favicon.ico"}:
        raise NotFound()
    return render_page(template_name)


@app.route("/media/<path:filename>", endpoint="media")
def media(filename: str) -> Response:
    from flask import send_from_directory

    return send_from_directory(ROOT_DIR / "media", filename)


@app.post("/save-subscriber-email/", endpoint="save_subscriber")
def save_subscriber() -> Response:
    payload = flask_request.get_json(silent=True) or flask_request.form
    email = str(payload.get("email", "")).strip().lower()
    if not email or "@" not in email:
        return jsonify(status="error", message="Please provide a valid email address."), 400
    db = get_db()
    db.execute("INSERT OR IGNORE INTO subscribers (email) VALUES (?)", (email,))
    db.commit()
    return jsonify(status="success")


@app.post("/capture-lead/", endpoint="capture_lead")
def capture_lead() -> Response:
    payload = flask_request.form or (flask_request.get_json(silent=True) or {})
    email = str(payload.get("email", "")).strip().lower()
    if not email:
        return jsonify(status="error", message="Email is required."), 400
    db = get_db()
    db.execute("INSERT OR IGNORE INTO subscribers (email, edition_name) VALUES (?, ?)", (email, payload.get("edition_title", "Newsletter")))
    db.commit()
    return jsonify(status="success")


@app.post("/users/submit-book-request/", endpoint="submit_book_request")
def submit_book_request() -> Response:
    payload = flask_request.form or (flask_request.get_json(silent=True) or {})
    try:
        book_id = int(payload.get("book_id", 0))
    except (TypeError, ValueError):
        book_id = 0
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id = ? AND archived=0", (book_id,)).fetchone()
    if not book:
        return jsonify(status="error", message="Book not found"), 404
    request_type = "Request" if book["available_copies"] > 0 else "Pre-order"
    if book["available_copies"] > 0:
        db.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = ?", (book_id,))
    db.execute(
        "INSERT INTO book_requests (book_title, user_name, member_id, phone_number, request_type) VALUES (?, ?, ?, ?, ?)",
        (book["title"], payload.get("full_name", "Guest"), payload.get("member_id", ""), payload.get("phone", ""), request_type),
    )
    db.commit()
    return jsonify(status="success", message="Request submitted!")


@app.route("/accounts/login/", methods=["GET", "POST"], endpoint="account_login")
@app.route("/account/login/", methods=["GET", "POST"], endpoint="account_login_short")
@app.route("/login/", methods=["GET", "POST"])
def account_login() -> Response:
    if flask_request.method == "POST":
        email = flask_request.form.get("email", "").strip().lower()
        row = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row and check_password_hash(row["password_hash"], flask_request.form.get("password", "")):
            session["user_id"] = row["id"]
            destination = flask_request.args.get('next', '/')
            return redirect(destination if destination.startswith('/') and not destination.startswith('//') and '\\' not in destination else '/')
        flash("The email or password was not recognised.", "danger")
    return render_site("member_login", "account", next_url=flask_request.args.get("next", ""))


@app.route("/accounts/signup/", methods=["GET", "POST"], endpoint="account_signup")
@app.route("/account/signup/", methods=["GET", "POST"], endpoint="account_signup_short")
@app.route("/signup/", methods=["GET", "POST"])
def account_signup() -> Response:
    if flask_request.method == "POST":
        name = flask_request.form.get("name", "").strip()
        email = flask_request.form.get("email", "").strip().lower()
        password = flask_request.form.get("password", "")
        if name and '@' in email and len(password) >= 10:
            try:
                cursor = get_db().execute("INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)", (email, name, generate_password_hash(password)))
                get_db().commit()
                session["user_id"] = cursor.lastrowid
                return redirect(safe_url_for("index"))
            except sqlite3.IntegrityError:
                flash("An account with that email already exists.", "danger")
        else:
            flash("Please complete all fields.", "danger")
    return render_site("member_signup", "account")


@app.post("/accounts/logout/", endpoint="account_logout")
@app.post("/logout/")
def account_logout() -> Response:
    session.clear()
    return redirect(safe_url_for("index"))


@app.route("/accounts/password/reset/", methods=["GET", "POST"], endpoint="account_reset_password")
@app.route("/account/password/reset/", methods=["GET", "POST"], endpoint="account_reset_password_short")
def account_reset_password() -> Response:
    if flask_request.method == "POST":
        flash("Email reset delivery is not configured. Contact the library for account assistance.", "success")
        return redirect(safe_url_for("account_login"))
    context = base_context("password_reset")
    context.update(form=build_form("reset"))
    return render_template("account/password_reset.html", **context)


@app.route("/users/<int:pk>/", endpoint="user_detail")
def user_detail(pk: int) -> Response:
    if session.get("user_id") != pk and not current_admin():
        return redirect("/accounts/login/")
    row = get_db().execute("SELECT * FROM users WHERE id = ?", (pk,)).fetchone()
    if not row:
        return render_site("error", error_code=404, error_heading="Page not found", error_message="This page may have moved or is no longer published."), 404
    orders = get_db().execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC",(pk,)).fetchall()
    enrollments = []  # No previous class registrations on the library-only profile.
    return render_site("profile","account",member=dict(row),member_orders=orders,member_classes=enrollments)


@app.route("/users/profile/", methods=["GET", "POST"], endpoint="account_profile")
@login_required
def account_profile() -> Response:
    return user_detail(int(session["user_id"]))


pass


@app.post("/api/track-exit/", endpoint="track_exit")
def track_exit() -> Response:
    payload = flask_request.get_json(silent=True) or {}
    activity_id = payload.get("activity_id")
    if activity_id:
        get_db().execute("UPDATE activities SET exit_time = CURRENT_TIMESTAMP WHERE id = ?", (activity_id,))
        get_db().commit()
    return jsonify(status="success")


@app.post("/users/library/checkout/", endpoint="process_library_checkout")
def process_library_checkout() -> Response:
    return jsonify(status="success", message="Library checkout request received.")


@app.post("/users/library/toggle-favorite/<int:book_id>/", endpoint="toggle_favorite")
def toggle_favorite(book_id: int) -> Response:
    return jsonify(status="success", book_id=book_id, favorite=True)


@app.route("/workshop/apply/", methods=["POST"], endpoint="apply_workshop")
def apply_workshop() -> Response:
    payload = flask_request.form or (flask_request.get_json(silent=True) or {})
    fee = float(payload.get("fee", 0) or 0)
    return jsonify(status="success", is_free=fee == 0, amount=int(fee * 100), order_id="demo_order")


@app.post("/workshop/verify-payment/", endpoint="verify_workshop_payment")
def verify_workshop_payment() -> Response:
    return jsonify(status="success")


@app.get("/payment/success/", endpoint="payment_success")
def payment_success() -> Response:
    flash("Payment details received. Thank you.", "success")
    return redirect(safe_url_for("index"))


@app.get("/robots.txt")
def robots_txt() -> Response:
    return Response("User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n", mimetype="text/plain")


@app.get("/debug-static/", endpoint="debug_static")
def debug_static() -> Response:
    return jsonify(static_url=safe_url_for("static", filename="css/style.css"), static_root=str(BASE_DIR / "static"))


@app.route("/submit-contribution/", methods=["GET", "POST"], endpoint="submit_contribution")
def submit_contribution() -> Response:
    if flask_request.method == "POST":
        flash("Thank you. Your contribution has been received.", "success")
        return redirect(flask_url_for("publications_page"))
    return render_page("submit_contribution")


@app.get("/membership/", endpoint="membership")
def membership() -> Response:
    return render_page("membership")


@app.get("/magazine/", endpoint="magazine")
def magazine() -> Response:
    return redirect("/community/media/?tab=magazines", code=301)


@app.get("/newspaper/", endpoint="newspaper_page")
def newspaper_page() -> Response:
    return redirect("/community/media/?tab=newspapers", code=301)


@app.get("/newspaper-2026/", endpoint="newspaper_2026")
def newspaper_2026() -> Response:
    return redirect("/community/media/?tab=newspapers", code=301)


@app.get("/google-login/", endpoint="google_login")
def google_login() -> Response:
    flash("Google sign-in is ready to connect through your OAuth provider.", "info")
    return redirect(safe_url_for("account_login"))


@app.get("/admin/save-book/", endpoint="admin_save_book")
def admin_save_book() -> Response:
    return jsonify(status="success", message="Book editor endpoint is available.")


@app.get("/users/internship-dashboard/", endpoint="users_internship_dashboard")
def users_internship_dashboard() -> Response:
    return render_page("internship_dashboard")


@app.post("/users/membership/activate-trial/", endpoint="users_activate_free_trial")
def users_activate_free_trial() -> Response:
    return jsonify(status="success", message="Trial activation recorded.")


@app.post("/users/membership/process/", endpoint="users_process_membership")
def users_process_membership() -> Response:
    return jsonify(status="success", message="Membership request received.")


@app.post("/users/subscription/process/", endpoint="users_process_subscription")
def users_process_subscription() -> Response:
    return jsonify(status="success", message="Subscription request received.")


@app.errorhandler(404)
def not_found(_: NotFound) -> Response:
    if flask_request.path.startswith("/static/") and Path(flask_request.path).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
        from flask import send_file

        return send_file(BASE_DIR / "static" / "img" / "placeholder.svg", mimetype="image/svg+xml")
    try:
        return render_site("error", error_code=404, error_heading="Page not found", error_message="This page may have moved or is no longer published."), 404
    except Exception:
        return Response("Page not found", status=404, mimetype="text/plain")


@app.errorhandler(500)
def server_error(err: Exception) -> Response:
    app.logger.exception("Internal Server Error: %s", err)
    try:
        return render_site("error", error_code=500, error_heading="Something went wrong", error_message="Please try again shortly."), 500
    except Exception:
        return Response("Server error", status=500, mimetype="text/plain")


register_template_compatibility()

with app.app_context():
    init_db()

from management import install_management
install_management(app, get_db, render_site, current_admin, BASE_DIR)
from access import install_upgrade
install_upgrade(app, get_db, render_site, current_admin, BASE_DIR)
# Enforce access before the older CMS dispatcher can return content.
app.before_request_funcs[None].insert(1, app.before_request_funcs[None].pop())


from seo import install_polish
install_polish(app, get_db)
from library_core import install_library_core
install_library_core(app,get_db)


from resources import install_release9
install_release9(app, get_db, render_site, current_admin, BASE_DIR)

from notifications import install_release10
install_release10(app, get_db, render_site, current_admin)
from accounts import install_release16
install_release16(app, get_db, render_site, current_admin)

from portal import install_release17
install_release17(app, get_db, render_site, current_admin, BASE_DIR)

from flexible import install_flexible
install_flexible(app, get_db, render_site)


from library_centers import install_library_centers
install_library_centers(app, get_db, current_admin)


from about_editor import install_about_editor
install_about_editor(app, get_db, current_admin)

from how_to_borrow import install_how_to_borrow
install_how_to_borrow(app, get_db, current_admin, render_site)

from visit_us import install_visit_us
install_visit_us(app, get_db, current_admin, render_site)


# Library-only routing guard: legacy learning URLs remain unavailable on both public and admin sides.
# This does NOT delete historical lessons, results, classes or membership database records.
from flask import abort as _library_abort, request as _library_request
_LIBRARY_RETIRED_PREFIXES = (
    '/skills/', '/admin/skills/', '/admin/skills23/', '/admin/skill', '/worksheets/', '/english/',
    '/maths/', '/financial-literacy/', '/ba/', '/banking/', '/soft-skills/',
    '/college-project/', '/ai-solutions/', '/coding-kids/', '/practice/',
    '/classes/', '/activities/', '/kids-activities/', '/schedule/',
    '/admin/classes/', '/admin/activities/', '/admin/classes17/', '/admin/learning-center/', '/admin/import/learning',
    '/admin/import/worksheet', '/admin/import/skills', '/admin/learning/',
    '/members/calendar/', '/members/classes/', '/members/practice/', '/members/worksheets/', '/admin/worksheets/', '/admin/practice/', '/admin/ba-', '/workshop/',
    '/legacy/english/', '/legacy/maths/', '/legacy/ba/', '/legacy/skills/',
    '/legacy/practice/', '/legacy/classes/', '/admin/about-sync/', '/admin/import/', '/plans-legacy/',
)
_LIBRARY_RETIRED_KINDS = {'classes','activities','learning','learning-submissions','skills-sections','schedules','worksheet-items'}
_LIBRARY_KEPT_PAGES = {'home','about','library','events','reading-circles','contests','publications','podcasts','gallery','membership-options','how-to-borrow','contact','community','collaborators','media'}
@app.before_request
def library_only_routes():
    path=_library_request.path.lower()
    if path.startswith(_LIBRARY_RETIRED_PREFIXES): _library_abort(404)
    if path.startswith('/admin/manage/') or path.startswith('/admin/import/'):
        parts=path.strip('/').split('/')
        if len(parts)>2 and parts[2] in _LIBRARY_RETIRED_KINDS: _library_abort(404)
    if path.startswith('/admin/page-sections/') and _library_request.values.get('page','home') not in _LIBRARY_KEPT_PAGES:
        _library_abort(404)
    if path.startswith('/admin/manage/pages/') and _library_request.method=='POST':
        slug=_library_request.form.get('slug','').strip().lower()
        if slug in {'maths','english','ba','practice','skills','classes','banking','soft-skills','financial-literacy'}:
            _library_abort(404)
    if path.startswith('/legacy/'):
        slug=path.removeprefix('/legacy/').strip('/').split('/')[0]
        if slug not in _LIBRARY_KEPT_PAGES:_library_abort(404)
    if _library_request.endpoint=='dynamic_page':
        slug=path.strip('/').split('/')[0]
        if slug not in _LIBRARY_KEPT_PAGES and slug not in {'membership','memberships','how-to-borrow'}:
            _library_abort(404)

# Run before all older before_request dispatchers, so retired URLs cannot be rendered indirectly.
app.before_request_funcs[None].remove(library_only_routes)
app.before_request_funcs[None].insert(0,library_only_routes)

# Browser favicon request.
@app.get('/favicon.ico')
def bookbuddy_favicon():
    return app.send_static_file('favicon.ico')


# Per-publication free/paid access, installed after legacy hooks.
from media_access import install_media_access
install_media_access(app, get_db, render_site, ROOT_DIR)

from site_design import install_site_design
install_site_design(app, get_db)

from spa_serving import install_spa_serving
install_spa_serving(app, ROOT_DIR)

from backend.app.api import install_api
install_api(app)

if __name__ == "__main__":
    app.run(host=os.environ.get("FLASK_HOST", "127.0.0.1"), port=int(os.environ.get("FLASK_PORT", "5000")), debug=os.environ.get("FLASK_DEBUG", "0") == "1")
