"""Configuration settings for Book Buddy."""
from __future__ import annotations

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

# Load environment file from root if present
load_dotenv(os.environ.get("BOOK_BUDDY_ENV_FILE", ROOT_DIR / ".env"), override=False)

if os.environ.get("VERCEL"):  # read-only filesystem: keep writable data in /tmp
    _tmp = Path("/tmp/bookbuddy")
    for _k, _v in (("BOOK_BUDDY_DATABASE", _tmp / "book_buddy.sqlite3"),
                   ("BOOK_BUDDY_PRIVATE_DIR", _tmp / "private"),
                   ("BOOK_BUDDY_BACKUP_DIR", _tmp / "backups")):
        os.environ.setdefault(_k, str(_v))
    os.environ.setdefault("SECRET_KEY", "change-me-set-SECRET_KEY-in-vercel")

DATABASE_PATH = Path(os.environ.get("BOOK_BUDDY_DATABASE", ROOT_DIR / "instance" / "book_buddy.sqlite3"))

def get_database_path() -> Path:
    return DATABASE_PATH
