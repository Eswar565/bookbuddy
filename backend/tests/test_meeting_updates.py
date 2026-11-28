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
        ("/publications/", "/media/"),
        ("/publications/?kind=news", "/newspaper/"),
        ("/publications/?kind=magazine", "/magazine/"),
        ("/publications/?kind=podcast", "/podcasts/"),
        ("/reading-circles/", "/events/?type=reading-circle"),
        ("/contests/", "/events/?type=contest"),
    ]
    for old_url, expected_target in redirect_checks:
        res = client.get(old_url, follow_redirects=False)
        assert res.status_code in (301, 302), f"Expected redirect for {old_url}, got {res.status_code}"
        assert expected_target in res.location, f"Expected redirect from {old_url} to {expected_target}, got {res.location}"


def test_catalogue_export_excel_and_pdf(client):
    """Verify that Excel export works and PDF export has been removed."""
    # Excel export
    res_excel = client.get("/library/export/xlsx/")
    assert res_excel.status_code == 200
    assert "spreadsheetml" in res_excel.content_type or "octet-stream" in res_excel.content_type
    assert len(res_excel.data) > 0
    assert "book_catalogue.xlsx" in res_excel.headers.get("Content-Disposition", "")

    # PDF export is removed
    res_pdf = client.get("/library/export/pdf/")
    assert res_pdf.status_code == 404


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
    assert "Download as PDF" not in html
    assert "Refine Catalogue" in html
    assert "Search the shelves, find a favorite" not in html
    assert "BOOK BUDDY / THE COLLECTION" not in html
    assert "The Book Buddy Library" not in html
    assert "Browse through our curated collection" not in html
    assert "Book Catalogue" in html
    assert "My Borrowed Books" in html


def test_admin_created_events_appear_on_public_page(client):
    """Verify that events, contests, and reading circles created in admin appear under filters, with correct badges and calendar month navigation."""
    from app import get_db
    with client.application.app_context():
        db = get_db()
        admin = db.execute("SELECT id FROM admin_users WHERE is_active=1 LIMIT 1").fetchone()
        aid = admin[0] if admin else db.execute("INSERT INTO admin_users(email,name,role,is_active) VALUES('admin-qa@test.com','Admin QA','super_admin',1)").lastrowid
        db.commit()

    with client.session_transaction() as sess:
        sess['admin_id'] = aid
        sess['admin_role'] = 'super_admin'

    # Get CSRF token from admin form
    res_form = client.get("/admin/manage/events/0/")
    assert res_form.status_code == 200

    # Insert items
    future_date = "2029-08-15"
    e_workshop_id = None
    e_contest_id = None
    e_circle_id = None

    with client.application.app_context():
        db = get_db()
        e_workshop_id = db.execute(
            "INSERT INTO events(title,category,event_date,event_time,capacity,fee,is_active) VALUES(?,?,?,?,?,?,?)",
            ("QA Storytelling Workshop", "upcoming", future_date, "10:00", 25, 0, 1)
        ).lastrowid
        e_contest_id = db.execute(
            "INSERT INTO events(title,category,event_date,event_time,capacity,fee,is_active) VALUES(?,?,?,?,?,?,?)",
            ("QA Creative Writing Contest", "contest", future_date, "14:00", 50, 50, 1)
        ).lastrowid
        e_circle_id = db.execute(
            "INSERT INTO events(title,category,event_date,event_time,capacity,fee,is_active) VALUES(?,?,?,?,?,?,?)",
            ("QA Weekend Reading Circle", "reading-circle", future_date, "16:00", 20, 0, 1)
        ).lastrowid
        db.commit()

    try:
        # Public: All events
        res_all = client.get("/events/")
        assert res_all.status_code == 200
        html_all = res_all.get_data(as_text=True)
        assert "QA Storytelling Workshop" in html_all
        assert "QA Creative Writing Contest" in html_all
        assert "QA Weekend Reading Circle" in html_all
        assert "Contest" in html_all
        assert "Reading Circle" in html_all

        # Public: Contests filter
        res_contests = client.get("/events/?type=contest")
        assert res_contests.status_code == 200
        html_contests = res_contests.get_data(as_text=True)
        assert "QA Creative Writing Contest" in html_contests
        assert "QA Weekend Reading Circle" not in html_contests

        # Public: Reading circles filter
        res_circles = client.get("/events/?type=reading-circle")
        assert res_circles.status_code == 200
        html_circles = res_circles.get_data(as_text=True)
        assert "QA Weekend Reading Circle" in html_circles
        assert "QA Creative Writing Contest" not in html_circles

        # Public: Events filter
        res_events = client.get("/events/?type=upcoming")
        assert res_events.status_code == 200
        html_events = res_events.get_data(as_text=True)
        assert "QA Storytelling Workshop" in html_events

        # Calendar month navigation test (prev/next month)
        res_month = client.get("/events/?month=2029-08")
        assert res_month.status_code == 200
        html_month = res_month.get_data(as_text=True)
        assert "August 2029" in html_month
        assert "2029-07" in html_month # prev month link
        assert "2029-09" in html_month # next month link
    finally:
        with client.application.app_context():
            db = get_db()
            db.execute("DELETE FROM events WHERE id IN (?,?,?)", (e_workshop_id, e_contest_id, e_circle_id))
            db.commit()


def test_become_a_partner_page_and_submissions(client):
    """Verify that Become a Partner page renders compact form, handles redirects, and processes submissions."""
    from app import get_db

    # Redirect checks
    res_redir1 = client.get("/partner/", follow_redirects=False)
    assert res_redir1.status_code in (301, 302)
    assert res_redir1.location.endswith("/work-with-us/")

    res_redir2 = client.get("/become-a-partner/", follow_redirects=False)
    assert res_redir2.status_code in (301, 302)
    assert res_redir2.location.endswith("/work-with-us/")

    # Form render check
    res_page = client.get("/work-with-us/")
    assert res_page.status_code == 200
    html = res_page.get_data(as_text=True)
    assert "Partner with Book Buddy" in html
    assert "Tell us about your proposal" in html
    assert "full_name" in html
    assert "proposal_type" in html

    # Submit HTML Form
    import re
    csrf_m = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html)
    csrf = csrf_m.group(1) if csrf_m else ""
    if not csrf:
        with client.session_transaction() as sess:
            csrf = sess.get("csrf_token", "")

    res_post = client.post("/work-with-us/", data={
        "csrf_token": csrf,
        "full_name": "QA Partner Tester",
        "email": "partner-qa@example.com",
        "phone": "+91 99999 88888",
        "organisation": "QA Reading Advocates",
        "proposal_type": "Reading Circle Partner",
        "message": "We would love to co-organise weekly reading circles.",
    }, follow_redirects=True)
    assert res_post.status_code == 200

    with client.application.app_context():
        db = get_db()
        row = db.execute("SELECT * FROM partner_submissions WHERE email='partner-qa@example.com'").fetchone()
        assert row is not None
        assert row["full_name"] == "QA Partner Tester"
        db.execute("DELETE FROM partner_submissions WHERE email='partner-qa@example.com'")
        db.commit()

    # Submit API JSON
    res_api = client.post("/api/v1/partners", json={
        "full_name": "QA API Partner",
        "email": "api-partner@example.com",
        "phone": "+91 98888 77777",
        "organisation": "API Community Library",
        "proposal_type": "School Library Outreach",
        "message": "Proposal submitted via API endpoint.",
    })
    assert res_api.status_code == 201
    assert res_api.json["ok"] is True

    with client.application.app_context():
        db = get_db()
        db.execute("DELETE FROM partner_submissions WHERE email='api-partner@example.com'")
        db.commit()


