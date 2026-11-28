import pytest
from app import app

def test_events_switcher_placement_and_design():
    with app.test_client() as client:
        res = client.get("/events/")
        assert res.status_code == 200
        html = res.get_data(as_text=True)

        # 1. Switcher should be inside events-content-header, not in events-sidebar
        assert "events-view-switcher" in html
        assert 'role="tablist"' in html
        assert 'aria-label="Event timeframes"' in html

        # 2. Old nav menu must be removed from sidebar
        assert "events-nav-menu" not in html

        # 3. Both tabs present with counts and aria-selected
        assert "Current &amp; Upcoming" in html or "Current & Upcoming" in html
        assert "Past Events" in html
        assert 'id="tab-current"' in html
        assert 'id="tab-past"' in html
        assert 'aria-selected="true"' in html

        # 4. Heading changes with view
        assert "Upcoming Events &amp; Contests" in html or "Upcoming Events & Contests" in html

        # 5. Test past events view
        res_past = client.get("/events/?view=past")
        assert res_past.status_code == 200
        html_past = res_past.get_data(as_text=True)
        assert "Past Events &amp; Contests" in html_past or "Past Events & Contests" in html_past

        # 6. Button text in event card
        assert "btn-book-event" in html
        assert ("Join contest" in html) or ("Register" in html)

        # 7. No top storybook banner on /events/
        assert "MARK YOUR CALENDAR" not in html
        assert "Your community calendar." not in html
        assert "folio-page-banner" not in html
