"""Unit and integration tests for Visit Us page."""
import pytest
from app import create_app
from app.db import get_db
from app.services.visit_us import DEFAULT_ADDRESS, DEFAULT_LAT, DEFAULT_LNG, get_visit_us_data


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_visit_us_page_renders_200(client):
    res = client.get("/visit-us/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # 1. Header banner completely removed
    assert "class=\"bb-visit-hero\"" not in html
    assert "bb-visit-eyebrow" not in html
    assert "Step into our library and explore a world of books" not in html

    # 2. Exactly one visually-hidden <h1>Visit Us</h1>
    assert '<h1 class="sr-only">Visit Us</h1>' in html
    assert html.count("<h1") == 1

    # 3. Valid keyless embed URL with lat/lng & z=16, without any \r or %0D
    assert "%0D" not in html
    assert "13.0544,80.1983" in html
    assert "z=16" in html
    assert "output=embed" in html

    # 4. Graceful fallback card exists
    assert 'id="bb-map-fallback"' in html
    assert "Book Buddy Library" in html
    assert "Open in Maps" in html
    assert "Get Directions" in html

    # 5. Library Tour section is preserved
    assert "bb-visit-tour-section" in html
    assert "A Glimpse Inside Book Buddy" in html


def test_visit_us_data_encoding():
    app = create_app()
    with app.app_context():
        db = get_db()
        data = get_visit_us_data(db)
        # Check no %0D or \r in encoded strings
        assert "%0D" not in data["encoded_dest"]
        assert "\r" not in data["directions_dest"]
        assert data["lat"] == DEFAULT_LAT
        assert data["lng"] == DEFAULT_LNG
        assert "z=16" in data["embed_url"]
        assert "output=embed" in data["embed_url"]
