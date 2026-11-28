"""Shared book availability helpers for Book Buddy.
Computes available copies consistently across card pills, catalogue filters, and exports.
"""
from __future__ import annotations
import sqlite3
from typing import Any

def get_book_available_copies(book: dict | sqlite3.Row | Any) -> int:
    """Return available copies for a book: total copies minus copies on active loans/requests.
    In the Book Buddy schema, available_copies is updated whenever loans/requests change.
    Fallback to stock or 0 if missing.
    """
    if isinstance(book, (dict, sqlite3.Row)):
        val = book["available_copies"] if "available_copies" in book and book["available_copies"] is not None else book.get("stock", 0)
    else:
        val = getattr(book, "available_copies", getattr(book, "stock", 0))
    try:
        return max(0, int(val or 0))
    except (ValueError, TypeError):
        return 0

def is_book_available(book: dict | sqlite3.Row | Any) -> bool:
    """Returns True if the book has 1 or more available copies."""
    return get_book_available_copies(book) > 0

def get_availability_sql_filter(availability: str | None) -> str | None:
    """Return an index-friendly SQL WHERE clause snippet for a given availability string."""
    if not availability:
        return None
    val = str(availability).strip().lower()
    if val == "available":
        return "available_copies > 0"
    elif val in ("unavailable", "waitlist"):
        return "available_copies <= 0"
    return None
