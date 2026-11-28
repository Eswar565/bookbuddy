"""Language normalization and book-language relationship helpers."""
from __future__ import annotations

import re
from typing import Any

# Split regex for language delimiters: comma, slash, ampersand, semicolon, pipe, and the word "and"
_LANG_SPLIT_RE = re.compile(r'[,/&;|]|\band\b', re.IGNORECASE)


def parse_languages(raw_lang: Any) -> list[str]:
    """
    Split each book's language value on , / & ; "and" and "|",
    trim, title-case it ("english " -> "English"), and de-duplicate case-insensitively.
    """
    if not raw_lang:
        return []
    if isinstance(raw_lang, (list, tuple, set)):
        items = raw_lang
    else:
        items = _LANG_SPLIT_RE.split(str(raw_lang))

    seen = set()
    result = []
    for t in items:
        cleaned = str(t).strip()
        if not cleaned:
            continue
        titled = cleaned.title()
        lower = titled.lower()
        if lower not in seen:
            seen.add(lower)
            result.append(titled)
    return result


def sync_book_languages(db, book_id: int, raw_lang: Any) -> list[str]:
    """Sync normalized languages for a book into the book_languages join table."""
    langs = parse_languages(raw_lang)
    db.execute("DELETE FROM book_languages WHERE book_id = ?", (book_id,))
    for lang in langs:
        db.execute(
            "INSERT OR IGNORE INTO book_languages (book_id, language) VALUES (?, ?)",
            (book_id, lang)
        )
    return langs


def get_distinct_languages(db) -> list[str]:
    """
    Return distinct single languages sorted A-Z, de-duplicated case-insensitively.
    Never returns combined entries or duplicates.
    """
    langs_set = set()

    # Try from book_languages table first
    try:
        rows = db.execute(
            "SELECT DISTINCT language FROM book_languages WHERE language IS NOT NULL AND TRIM(language)<>''"
        ).fetchall()
        for r in rows:
            for l in parse_languages(r[0]):
                langs_set.add(l)
    except Exception:
        pass

    # If empty or table not populated, also read from books table
    if not langs_set:
        try:
            rows = db.execute(
                "SELECT DISTINCT language FROM books WHERE archived=0 AND language IS NOT NULL AND TRIM(language)<>''"
            ).fetchall()
            for r in rows:
                for l in parse_languages(r[0]):
                    langs_set.add(l)
        except Exception:
            pass

    if not langs_set:
        return ["English", "Hindi", "Tamil"]

    # De-duplicate case-insensitively and sort A-Z
    seen = set()
    result = []
    for lang in sorted(langs_set, key=lambda s: s.lower()):
        if lang.lower() not in seen:
            seen.add(lang.lower())
            result.append(lang)
    return result


def ensure_book_languages_table(connection) -> None:
    """Ensure book_languages table and indexes exist, and populate from existing books."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS book_languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
            language TEXT NOT NULL,
            UNIQUE(book_id, language)
        );
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_book_languages_lang ON book_languages(language);")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_book_languages_book ON book_languages(book_id);")

    # Migrate existing data safely and idempotently
    rows = connection.execute(
        "SELECT id, language FROM books WHERE language IS NOT NULL AND TRIM(language) <> ''"
    ).fetchall()
    for row in rows:
        book_id = row[0]
        langs = parse_languages(row[1])
        for lang in langs:
            connection.execute(
                "INSERT OR IGNORE INTO book_languages (book_id, language) VALUES (?, ?)",
                (book_id, lang)
            )
