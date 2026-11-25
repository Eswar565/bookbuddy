"""Database helpers and connections for Book Buddy."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from flask import g
from .config import DATABASE_PATH, ROOT_DIR

def get_database_path() -> Path:
    return DATABASE_PATH

def db_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = db_connection()
    return g.db

def close_db(_: BaseException | None = None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()
