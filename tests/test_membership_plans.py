import pytest
from app import app, get_db


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_membership_plans_seed():
    """Verify that all 6 plans (tier x duration) are seeded only if missing."""
    with app.app_context():
        db = get_db()
        plans = db.execute("SELECT * FROM lending_plans WHERE is_active=1 ORDER BY months, amount").fetchall()
        assert len(plans) >= 6

        # Check 2 Months plans
        two_mo = [p for p in plans if p['months'] == 2]
        assert len(two_mo) == 2
        solo_2 = next(p for p in two_mo if 'solo' in p['tier'].lower())
        family_2 = next(p for p in two_mo if 'family' in p['tier'].lower())
        assert solo_2['amount'] == 800.0
        assert solo_2['book_limit'] == 2
        assert solo_2['total_books'] == 8
        assert solo_2['tagline'] == 'Summer Special'

        assert family_2['amount'] == 1400.0
        assert family_2['book_limit'] == 4
        assert family_2['total_books'] == 16
        assert family_2['tagline'] == 'Summer Special'

        # Check 3 Months plans
        three_mo = [p for p in plans if p['months'] == 3]
        assert len(three_mo) == 2
        solo_3 = next(p for p in three_mo if 'solo' in p['tier'].lower())
        family_3 = next(p for p in three_mo if 'family' in p['tier'].lower())
        assert solo_3['amount'] == 1100.0
        assert solo_3['book_limit'] == 2
        assert solo_3['total_books'] == 12
        assert solo_3['tagline'] == 'Regular'

        assert family_3['amount'] == 2000.0
        assert family_3['book_limit'] == 4
        assert family_3['total_books'] == 24
        assert family_3['tagline'] == 'Regular'

        # Check 9 Months plans
        nine_mo = [p for p in plans if p['months'] == 9]
        assert len(nine_mo) == 2
        solo_9 = next(p for p in nine_mo if 'solo' in p['tier'].lower())
        family_9 = next(p for p in nine_mo if 'family' in p['tier'].lower())
        assert solo_9['amount'] == 3000.0
        assert solo_9['book_limit'] == 2
        assert solo_9['total_books'] == 36
        assert solo_9['tagline'] == 'Academic Year'
        assert solo_9['badge'] == 'BEST VALUE'

        assert family_9['amount'] == 5500.0
        assert family_9['book_limit'] == 4
        assert family_9['total_books'] == 72
        assert family_9['tagline'] == 'Academic Year'
        assert family_9['badge'] == 'BEST VALUE'

        # Check benefits for all
        for p in plans:
            assert 'Online Portal Access' in p['benefits']
            assert 'Academic Worksheets' in p['benefits']
            assert 'The Book Buddy Times' in p['benefits']
            assert 'Beyond School Activities' in p['benefits']
            assert 'Games' in p['benefits']
            assert 'Contribute to Magazine' in p['benefits']


def test_membership_page_render_and_layout(client):
    """Verify /membership/ returns 200, correct headings, comparison table, highlighted BEST VALUE, and service modes."""
    res = client.get('/membership/')
    assert res.status_code == 200
    html = res.data.decode('utf-8')

    # Headings
    assert 'Choose Your Membership Tier' in html
    assert "Pick the plan that fits your family&#39;s reading appetite." in html or "Pick the plan that fits your family's reading appetite." in html

    # Table columns & badges
    assert '2 Months' in html
    assert '3 Months' in html
    assert '9 Months' in html
    assert 'BEST VALUE' in html
    assert 'is-highlighted' in html

    # Tiers and prices
    assert 'Solo Explorer' in html
    assert 'Family Pack / Elite' in html
    assert '800' in html
    assert '1100' in html
    assert '3000' in html
    assert '1400' in html
    assert '2000' in html
    assert '5500' in html

    # Total books
    assert '8 books (Solo)' in html
    assert '16 books (Family)' in html
    assert '12 books (Solo)' in html
    assert '24 books (Family)' in html
    assert '36 books (Solo)' in html
    assert '72 books (Family)' in html

    # Service modes
    assert 'Offline (Self-Pickup)' in html
    assert 'Online (Doorstep Delivery)' in html
    assert 'Gandhi Nagar, Saligramam, Chennai' in html
    assert '+₹350/month' in html or '350' in html

    # Subscribe modal elements
    assert 'Complete Your Subscription' in html
    assert 'child_name' in html
    assert 'child_dob' in html
    assert 'student_grade' in html
    assert 'service_mode' in html


def token(c):
    from bs4 import BeautifulSoup
    return BeautifulSoup(c.get('/membership/').data, 'html.parser').select_one('input[name=csrf_guard]')['value']


def test_server_side_price_calculation_and_delivery_fee(client):
    """Test price calculations: offline = plan fee; online = plan fee + 350 * months."""
    with app.app_context():
        db = get_db()
        # Create a test user
        uid = db.execute("INSERT INTO users(name, email, password_hash, dob) VALUES('Test Parent', 'parent@example.test', 'hash', '1985-05-15')").lastrowid
        db.commit()

        # Find 2 Months Solo Explorer (800) and 9 Months Family Pack (5500)
        p_solo_2 = db.execute("SELECT * FROM lending_plans WHERE months=2 AND book_limit=2").fetchone()
        p_fam_9 = db.execute("SELECT * FROM lending_plans WHERE months=9 AND book_limit=4").fetchone()

    # Simulate logged-in session
    with client.session_transaction() as sess:
        sess['user_id'] = uid

    t = token(client)

    # 1. Offline subscription for 2 Months Solo Explorer: ₹800 + 0 = ₹800
    res1 = client.post(f'/memberships/request/{p_solo_2["id"]}/', data={
        'csrf_guard': t,
        'service_mode': 'offline',
        'child_name': 'Aarav',
        'child_dob': '2016-04-10',
        'student_grade': 'Class 1 to 3',
        'parent_name': 'Test Parent',
        'email': 'parent@example.test',
        'phone': '9876543210'
    })
    assert res1.status_code == 302
    assert '/members/billing/' in res1.headers['Location']

    with app.app_context():
        db = get_db()
        sub1 = db.execute("SELECT * FROM lending_subscriptions WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
        assert sub1['plan_id'] == p_solo_2['id']
        assert sub1['amount'] == 800.0
        assert sub1['delivery_fee'] == 0.0
        assert sub1['service_mode'] == 'offline'
        assert sub1['child_name'] == 'Aarav'
        assert sub1['student_grade'] == 'Class 1 to 3'

    # 2. Online subscription for 9 Months Family Pack: ₹5500 + 350*9 (3150) = ₹8650
    t2 = token(client)
    res2 = client.post(f'/memberships/request/{p_fam_9["id"]}/', data={
        'csrf_guard': t2,
        'service_mode': 'online',
        'child_name': 'Diya',
        'child_dob': '2014-08-20',
        'student_grade': 'Class 4 to 5',
        'parent_name': 'Test Parent',
        'email': 'parent@example.test',
        'phone': '9876543210',
        'address_flat': 'Flat 402, Lotus Tower',
        'address_street': 'Gandhi Nagar Main Rd',
        'address_city': 'Chennai',
        'address_state': 'Tamil Nadu',
        'address_pincode': '600093',
        'address_country': 'India',
        'referral_code': 'READ2026'
    })
    assert res2.status_code == 302
    assert '/members/billing/' in res2.headers['Location']

    with app.app_context():
        db = get_db()
        sub2 = db.execute("SELECT * FROM lending_subscriptions WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
        assert sub2['plan_id'] == p_fam_9['id']
        assert sub2['delivery_fee'] == 3150.0  # 350 * 9
        assert sub2['amount'] == 8650.0        # 5500 + 3150
        assert sub2['service_mode'] == 'online'
        assert sub2['child_name'] == 'Diya'
        assert sub2['address_flat'] == 'Flat 402, Lotus Tower'
        assert sub2['address_pincode'] == '600093'
        assert sub2['referral_code'] == 'READ2026'


def test_navigation_and_seo(client):
    """Verify Library dropdown has 'Membership & Plans' and footer link works."""
    res = client.get('/')
    assert res.status_code == 200
    html = res.data.decode('utf-8')

    # Dropdown link
    assert 'href="/membership/">Membership &amp; Plans</a>' in html or 'href="/membership/">Membership & Plans</a>' in html

    # Footer link
    assert '/membership/' in html

    # SEO metadata on /membership/
    res_mem = client.get('/membership/')
    mem_html = res_mem.data.decode('utf-8')
    assert '<title>Choose Your Membership Tier · Book Buddy</title>' in mem_html
    assert 'Choose your Book Buddy membership tier' in mem_html


def test_guest_redirect_flow(client):
    """Guests requesting a plan are redirected to login with next parameter preserving the plan."""
    with app.app_context():
        p = get_db().execute("SELECT id FROM lending_plans WHERE is_active=1 LIMIT 1").fetchone()

    t = token(client)
    res = client.post(f'/memberships/request/{p["id"]}/', data={
        'csrf_guard': t,
        'months': '3'
    })
    assert res.status_code == 302
    assert '/login/' in res.headers['Location']
    assert f'plan_id%3D{p["id"]}' in res.headers['Location'] or f'plan_id={p["id"]}' in res.headers['Location']


def test_admin_plans_editor_and_settings(client):
    """Admin can edit plan attributes (tier, badge, tagline, total_books) and service settings."""
    with app.app_context():
        db = get_db()
        admin_id = db.execute("SELECT id FROM admin_users LIMIT 1").fetchone()[0]
        plan = db.execute("SELECT * FROM lending_plans WHERE is_active=1 LIMIT 1").fetchone()

    with client.session_transaction() as sess:
        sess['admin_id'] = admin_id

    t = token(client)
    # 1. Save service settings
    res_settings = client.post('/admin/plans17/', data={
        'csrf_guard': t,
        'action': 'settings',
        'membership_delivery_fee_monthly': '400',
        'membership_delivery_area': 'Saligramam & Vadapalani (6 km)',
        'membership_delivery_day': 'Every Sunday morning',
        'membership_pickup_address': 'Gandhi Nagar, Saligramam, Chennai - 600093'
    })
    assert res_settings.status_code == 302

    with app.app_context():
        db = get_db()
        fee = db.execute("SELECT content_value FROM site_content WHERE content_key='membership_delivery_fee_monthly'").fetchone()[0]
        assert fee == '400'
        area = db.execute("SELECT content_value FROM site_content WHERE content_key='membership_delivery_area'").fetchone()[0]
        assert area == 'Saligramam & Vadapalani (6 km)'

    # 2. Edit plan
    t2 = token(client)
    res_plan = client.post('/admin/plans17/', data={
        'csrf_guard': t2,
        'action': 'plan',
        'id': str(plan['id']),
        'name': plan['name'],
        'tier': 'Solo Explorer Custom',
        'months': '2',
        'duration_days': '60',
        'tagline': 'Super Summer Offer',
        'badge': 'TOP PICK',
        'amount': '850',
        'book_limit': '2',
        'total_books': '10',
        'loan_days': '14',
        'renewal_limit': '1',
        'fine_daily': '0',
        'benefits': "Online Portal Access\nAcademic Worksheets",
        'description': 'Updated test description',
        'is_active': '1'
    })
    assert res_plan.status_code == 302

    with app.app_context():
        db = get_db()
        updated = db.execute("SELECT * FROM lending_plans WHERE id=?", (plan['id'],)).fetchone()
        assert updated['tier'] == 'Solo Explorer Custom'
        assert updated['tagline'] == 'Super Summer Offer'
        assert updated['badge'] == 'TOP PICK'
        assert updated['amount'] == 850.0
        assert updated['total_books'] == 10

