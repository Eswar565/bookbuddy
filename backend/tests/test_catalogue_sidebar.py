"""Tests for Simplified Filter Sidebar on Library > Book Catalogue (/library/ and /api/v1/books)."""
from __future__ import annotations

import pytest
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


class TestCatalogueSidebarHTML:
    """Test Jinja template sidebar structure and simplified controls."""

    def test_sidebar_contains_simplified_controls(self, client):
        resp = client.get("/library/")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)

        # 1. Search Box
        assert 'id="sidebar-search-q"' in html
        assert 'placeholder="Search title or author..."' in html

        # 2. New Arrivals
        assert 'id="sidebar-new-arrivals-btn"' in html
        assert "New Arrivals" in html

        # 3. Sort By dropdown
        assert 'id="sidebar-sort-btn"' in html
        assert 'id="sidebar-sort-menu"' in html
        assert "A–Z" in html
        assert "Z–A" in html
        assert "Newest" in html

        # 4. Categories dropdown
        assert 'id="sidebar-cat-btn"' in html
        assert 'id="sidebar-cat-menu"' in html
        assert "Baby" in html
        assert "Toddler" in html
        assert "Junior" in html
        assert "Middle Grade" in html
        assert "Young Adults" in html
        assert "Adults" in html
        assert "Fiction" in html
        assert "Non Fiction" in html
        assert "Languages" in html

        # Old removed controls should NOT be present in the sidebar
        assert 'name="age_group"' not in html
        assert 'name="genre"' not in html
        assert 'name="availability"' not in html

    def test_sort_orders(self, client):
        # Newest
        r_newest = client.get("/library/?sort=newest")
        assert r_newest.status_code == 200

        # A-Z
        r_az = client.get("/library/?sort=az")
        assert r_az.status_code == 200

        # Z-A
        r_za = client.get("/library/?sort=za")
        assert r_za.status_code == 200

    def test_new_arrivals_filter(self, client):
        resp = client.get("/library/?new=1")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'aria-pressed="true"' in html
        assert "New Arrivals" in html

    def test_category_filter(self, client):
        for cat in ["Fiction", "Non Fiction", "Junior", "Baby", "Adults"]:
            resp = client.get(f"/library/?category={cat}")
            assert resp.status_code == 200
            html = resp.get_data(as_text=True)
            assert cat in html

    def test_empty_category_message(self, client):
        resp = client.get("/library/?category=NonExistentCategoryXYZ")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "No books found in this category" in html

    def test_language_filter_and_chips(self, client):
        resp = client.get("/library/?lang=English")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "Language: English" in html
        assert "Clear All" in html


class TestCatalogueSidebarAPI:
    """Test API /api/v1/books endpoint with simplified sidebar parameters."""

    def test_api_filter_options(self, client):
        resp = client.get("/api/v1/books")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload.get("ok") is True
        data = payload.get("data", {})
        opts = data.get("filter_options", {})

        assert "categories" in opts
        assert "Baby" in opts["categories"]
        assert "Fiction" in opts["categories"]
        assert "Non Fiction" in opts["categories"]
        assert "languages" in opts
        assert "sort_options" in opts

    def test_api_sort_orders(self, client):
        r_az = client.get("/api/v1/books?sort=az")
        assert r_az.status_code == 200
        payload = r_az.get_json()
        books_az = payload.get("data", {}).get("books", [])
        if len(books_az) >= 2:
            titles = [b["title"].lower() for b in books_az]
            assert titles == sorted(titles)

    def test_api_category_filter(self, client):
        resp = client.get("/api/v1/books?category=Fiction")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload.get("ok") is True
        assert "books" in payload.get("data", {})

    def test_api_new_arrivals(self, client):
        resp = client.get("/api/v1/books?new=1")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload.get("ok") is True
        assert "books" in payload.get("data", {})

    def test_api_combined_filters(self, client):
        resp = client.get("/api/v1/books?q=the&category=Fiction&sort=az&new=1")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload.get("ok") is True
        assert "books" in payload.get("data", {})


class TestExcelExportWithFilters:
    """Test that Excel export succeeds with new sidebar parameters."""

    def test_export_with_category_and_sort(self, client):
        resp = client.get("/library/export/xlsx/?category=Fiction&sort=az")
        assert resp.status_code == 200
        assert resp.content_type in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/octet-stream"
        ]
