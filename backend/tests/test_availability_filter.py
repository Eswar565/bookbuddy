"""Tests for Availability filter on Library > Book Catalogue (/library/, /api/v1/books, and exports)."""
from __future__ import annotations

import io
import pytest
import openpyxl
from app import app as flask_app
from app.db import get_db


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def sample_books():
    """Seed test database with books of 0, 1, and 5 available copies across categories and languages."""
    with flask_app.app_context():
        db = get_db()
        # Clean any existing test books
        db.execute("DELETE FROM books WHERE title LIKE 'AvailTest%'")
        db.commit()

        # Book 1: 0 copies (Unavailable), Fiction, English
        cur1 = db.execute(
            """INSERT INTO books (title, author, collection, language, category, available_copies, stock, is_new_arrival, archived)
               VALUES ('AvailTest Zero', 'Author Zero', 'Fiction', 'English', 'Fiction', 0, 0, 0, 0)"""
        )
        b1_id = cur1.lastrowid

        # Book 2: 1 copy (Available), Fiction, Tamil
        cur2 = db.execute(
            """INSERT INTO books (title, author, collection, language, category, available_copies, stock, is_new_arrival, archived)
               VALUES ('AvailTest One', 'Author One', 'Fiction', 'Tamil', 'Fiction', 1, 1, 0, 0)"""
        )
        b2_id = cur2.lastrowid

        # Book 3: 5 copies (Available), Non Fiction, English
        cur3 = db.execute(
            """INSERT INTO books (title, author, collection, language, category, available_copies, stock, is_new_arrival, archived)
               VALUES ('AvailTest Five', 'Author Five', 'Non Fiction', 'English', 'Non Fiction', 5, 5, 1, 0)"""
        )
        b3_id = cur3.lastrowid

        # Map languages
        db.execute("INSERT OR IGNORE INTO book_languages (book_id, language) VALUES (?, 'English')", (b1_id,))
        db.execute("INSERT OR IGNORE INTO book_languages (book_id, language) VALUES (?, 'Tamil')", (b2_id,))
        db.execute("INSERT OR IGNORE INTO book_languages (book_id, language) VALUES (?, 'English')", (b3_id,))
        db.commit()

        yield {"b1": b1_id, "b2": b2_id, "b3": b3_id}

        # Teardown
        db.execute("DELETE FROM books WHERE title LIKE 'AvailTest%'")
        db.execute("DELETE FROM book_languages WHERE book_id IN (?, ?, ?)", (b1_id, b2_id, b3_id))
        db.commit()


class TestAvailabilityAPI:
    """Test /api/v1/books endpoint with availability parameter."""

    def test_api_availability_all(self, client, sample_books):
        res = client.get("/api/v1/books?q=AvailTest")
        assert res.status_code == 200
        data = res.get_json()["data"]
        titles = [b["title"] for b in data["books"]]
        assert "AvailTest Zero" in titles
        assert "AvailTest One" in titles
        assert "AvailTest Five" in titles
        assert data["total_count"] == 3

    def test_api_availability_available(self, client, sample_books):
        res = client.get("/api/v1/books?q=AvailTest&availability=available")
        assert res.status_code == 200
        data = res.get_json()["data"]
        titles = [b["title"] for b in data["books"]]
        assert "AvailTest One" in titles
        assert "AvailTest Five" in titles
        assert "AvailTest Zero" not in titles
        assert data["total_count"] == 2

    def test_api_availability_unavailable(self, client, sample_books):
        res = client.get("/api/v1/books?q=AvailTest&availability=unavailable")
        assert res.status_code == 200
        data = res.get_json()["data"]
        titles = [b["title"] for b in data["books"]]
        assert "AvailTest Zero" in titles
        assert "AvailTest One" not in titles
        assert "AvailTest Five" not in titles
        assert data["total_count"] == 1

    def test_api_availability_combined_with_category(self, client, sample_books):
        # Fiction + available -> should return only AvailTest One (1 copy, Fiction)
        res = client.get("/api/v1/books?q=AvailTest&category=Fiction&availability=available")
        assert res.status_code == 200
        data = res.get_json()["data"]
        titles = [b["title"] for b in data["books"]]
        assert titles == ["AvailTest One"]

        # Fiction + unavailable -> should return only AvailTest Zero (0 copies, Fiction)
        res_unavail = client.get("/api/v1/books?q=AvailTest&category=Fiction&availability=unavailable")
        assert res_unavail.status_code == 200
        data_unavail = res_unavail.get_json()["data"]
        titles_unavail = [b["title"] for b in data_unavail["books"]]
        assert titles_unavail == ["AvailTest Zero"]

    def test_api_availability_combined_with_language(self, client, sample_books):
        # English + available -> should return only AvailTest Five (English, 5 copies)
        res = client.get("/api/v1/books?q=AvailTest&lang=English&availability=available")
        assert res.status_code == 200
        data = res.get_json()["data"]
        titles = [b["title"] for b in data["books"]]
        assert titles == ["AvailTest Five"]

        # English + unavailable -> should return only AvailTest Zero (English, 0 copies)
        res_zero = client.get("/api/v1/books?q=AvailTest&lang=English&availability=unavailable")
        assert res_zero.status_code == 200
        data_zero = res_zero.get_json()["data"]
        titles_zero = [b["title"] for b in data_zero["books"]]
        assert titles_zero == ["AvailTest Zero"]

    def test_api_availability_ignores_unknown_values(self, client, sample_books):
        res = client.get("/api/v1/books?q=AvailTest&availability=foobar")
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert data["total_count"] == 3


class TestAvailabilityExport:
    """Test Excel export with availability filter."""

    def test_export_books_excel_with_availability(self, client, sample_books):
        res = client.get("/library/export/xlsx/?q=AvailTest&availability=available")
        assert res.status_code == 200
        assert res.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        wb = openpyxl.load_workbook(io.BytesIO(res.data))
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        # Header + 2 available books
        assert len(rows) == 3
        headers = rows[0]
        assert "Title" in headers
        assert "Availability" in headers

        exported_titles = [r[0] for r in rows[1:]]
        assert "AvailTest One" in exported_titles
        assert "AvailTest Five" in exported_titles
        assert "AvailTest Zero" not in exported_titles

        # Check availability column value
        avail_idx = headers.index("Availability")
        for r in rows[1:]:
            assert r[avail_idx] == "Available"

    def test_export_books_excel_with_unavailable(self, client, sample_books):
        res = client.get("/library/export/xlsx/?q=AvailTest&availability=unavailable")
        assert res.status_code == 200
        wb = openpyxl.load_workbook(io.BytesIO(res.data))
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        # Header + 1 unavailable book
        assert len(rows) == 2
        assert rows[1][0] == "AvailTest Zero"
        avail_idx = rows[0].index("Availability")
        assert rows[1][avail_idx] == "Unavailable"


class TestAvailabilityHTMLUI:
    """Test Jinja template sidebar, dropdown markup, order, chips, and empty state."""

    def test_sidebar_dropdown_order_and_markup(self, client):
        res = client.get("/library/")
        assert res.status_code == 200
        html = res.get_data(as_text=True)

        # Check order: Search, New Arrivals, Sort By, Categories, Availability
        pos_search = html.find('id="sidebar-search-q"')
        pos_new = html.find('id="sidebar-new-arrivals-btn"')
        pos_sort = html.find('id="sidebar-sort-btn"')
        pos_cat = html.find('id="sidebar-cat-btn"')
        pos_avail = html.find('id="sidebar-avail-btn"')

        assert pos_search != -1
        assert pos_new != -1
        assert pos_sort != -1
        assert pos_cat != -1
        assert pos_avail != -1

        assert pos_search < pos_new < pos_sort < pos_cat < pos_avail

        # Check Availability button text and dropdown items
        assert 'id="sidebar-avail-btn"' in html
        assert 'id="sidebar-avail-label"' in html
        assert 'id="sidebar-avail-menu"' in html
        assert "All Books" in html
        assert "Available" in html
        assert "Unavailable" in html

    def test_availability_chips_and_label_when_active(self, client, sample_books):
        # When available is active
        res_avail = client.get("/library/?q=AvailTest&availability=available")
        assert res_avail.status_code == 200
        html_avail = res_avail.get_data(as_text=True)
        assert "Availability: Available" in html_avail
        assert 'data-remove-key="availability"' in html_avail

        # When unavailable is active
        res_unavail = client.get("/library/?q=AvailTest&availability=unavailable")
        assert res_unavail.status_code == 200
        html_unavail = res_unavail.get_data(as_text=True)
        assert "Availability: Unavailable" in html_unavail
        assert 'data-remove-key="availability"' in html_unavail

    def test_availability_empty_state(self, client, sample_books):
        # Non-existent query + unavailable -> empty state
        res = client.get("/library/?q=NonExistentBookXYZ999&availability=unavailable")
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert "No unavailable books right now" in html
        assert "Reset All Filters" in html
