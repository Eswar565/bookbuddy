import os
import shutil
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
ORIGINAL_DB = BASE_DIR / "instance" / "book_buddy.sqlite3"
TEST_DB = BASE_DIR / "instance" / "book_buddy_test.sqlite3"


def pytest_configure(config):
    """Isolate all test runs to a dedicated temporary database copy."""
    os.environ["APP_ENV"] = "testing"
    if ORIGINAL_DB.exists():
        TEST_DB.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ORIGINAL_DB, TEST_DB)
    os.environ["BOOK_BUDDY_DATABASE"] = str(TEST_DB)
    # Ensure notifications are disabled during tests in the test database
    import sqlite3
    try:
        conn = sqlite3.connect(TEST_DB)
        conn.execute("CREATE TABLE IF NOT EXISTS app_flags(key TEXT PRIMARY KEY,value TEXT NOT NULL);")
        conn.execute("INSERT OR REPLACE INTO app_flags(key, value) VALUES ('notifications_enabled', '0');")
        conn.commit()
        conn.close()
    except Exception:
        pass


def pytest_unconfigure(config):
    """Clean up test database at end of pytest session."""
    try:
        if TEST_DB.exists():
            TEST_DB.unlink()
    except Exception:
        pass

