import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_menu_urls_return_200(client):
    """Verify that all frozen primary menu URLs return 200 OK."""
    urls = [
        "/",
        "/library/",
        "/membership/",
        "/how-to-borrow/",
        "/visit-us/",
        "/community/",
        "/community/media/",
        "/events/",
        "/about/",
        "/gallery/",
        "/collaborators/",
        "/contact/",
    ]
    for url in urls:
        res = client.get(url)
        assert res.status_code == 200, f"Expected 200 for {url}, got {res.status_code}"


def test_gallery_category_urls_return_200(client):
    """Verify that the 4 category gallery pages return 200 and contain their respective CTAs."""
    cat_specs = [
        ("/gallery/reading-moments/", "/library/"),
        ("/gallery/events-workshops/", "/events/"),
        ("/gallery/our-space/", "/visit-us/"),
        ("/gallery/community-events/", "/community/"),
    ]
    for url, cta_link in cat_specs:
        res = client.get(url)
        assert res.status_code == 200, f"Expected 200 for {url}, got {res.status_code}"
        html = res.get_data(as_text=True)
        assert cta_link in html, f"Expected CTA link {cta_link} in {url}"
        assert 'id="bb-lightbox"' in html, f"Expected lightbox in {url}"


def test_old_urls_redirect(client):
    """Verify that old URLs redirect cleanly to their new destinations."""
    redirect_checks = [
        ("/publications/", "/community/media/"),
        ("/newspaper/", "/community/media/?tab=newspapers"),
        ("/magazine/", "/community/media/?tab=magazines"),
        ("/podcasts/", "/community/media/?tab=podcasts"),
        ("/reading-circles/", "/events/?type=reading-circle"),
        ("/contests/", "/events/?type=contest"),
    ]
    for old_url, expected_target in redirect_checks:
        res = client.get(old_url, follow_redirects=False)
        assert res.status_code in (301, 302), f"Expected redirect for {old_url}, got {res.status_code}"
        assert expected_target in res.location, f"Expected redirect from {old_url} to {expected_target}, got {res.location}"


def test_catalogue_export_excel_and_pdf(client):
    """Verify that Excel and PDF export endpoints return valid streaming file downloads."""
    # Excel export
    res_excel = client.get("/library/export/xlsx/")
    assert res_excel.status_code == 200
    assert "spreadsheetml" in res_excel.content_type or "octet-stream" in res_excel.content_type
    assert len(res_excel.data) > 0
    assert "book_catalogue.xlsx" in res_excel.headers.get("Content-Disposition", "")

    # PDF export
    res_pdf = client.get("/library/export/pdf/")
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.content_type
    assert len(res_pdf.data) > 0
    assert res_pdf.data.startswith(b"%PDF")
    assert "book_catalogue.pdf" in res_pdf.headers.get("Content-Disposition", "")


def test_collaborators_page_renders_4_categories(client):
    """Verify that the collaborators page renders all 4 sections with friendly Coming soon notes if empty."""
    res = client.get("/collaborators/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Library Partners" in html
    assert "Storytellers &amp; Authors" in html or "Storytellers & Authors" in html
    assert "Community Partners" in html
    assert "Creative Partners" in html
    assert "Coming soon" in html or "Partnerships in progress" in html


def test_events_page_current_and_past_views(client):
    """Verify that events page handles both current and past views, and date filtering."""
    # Current view
    res_current = client.get("/events/?view=current")
    assert res_current.status_code == 200
    html_curr = res_current.get_data(as_text=True)
    assert "Upcoming Events" in html_curr or "Current" in html_curr

    # Past view
    res_past = client.get("/events/?view=past")
    assert res_past.status_code == 200
    html_past = res_past.get_data(as_text=True)
    assert "Past Events" in html_past

    # Date filter
    res_date = client.get("/events/?date=2026-11-24")
    assert res_date.status_code == 200
    html_date = res_date.get_data(as_text=True)
    assert "Filtered for date" in html_date or "2026-11-24" in html_date


def test_catalogue_filter_panel_and_no_total_count(client):
    """Verify that catalogue removes 'total books available' text and includes export buttons."""
    res = client.get("/library/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "books found" not in html
    assert "total books available" not in html.lower()
    assert "Download as Excel" in html
    assert "Download as PDF" in html
    assert "Refine Catalogue" in html
