import re
import pytest
from app import app, get_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as c:
        yield c

def test_appearance_settings_and_routes(client):
    # 1. Public home page defaults
    res = client.get('/')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'data-theme="maroon"' in html or 'data-theme=' in html
    assert 'data-font="inter"' in html or 'data-font=' in html
    assert 'fonts.googleapis.com' in html
    assert 'Inter:wght@400;600;700' in html
    assert 'Playfair+Display:wght@400;600;700' in html
    assert 'Poppins:wght@400;600;700' in html
    assert '/static/css/bb-appearance.css' in html

    # 2. Unauthenticated admin route redirects to login
    res_unauth = client.get('/admin/appearance/')
    assert res_unauth.status_code == 302
    assert '/admin/login/' in res_unauth.location

    # 3. Authenticated admin access
    with client.session_transaction() as sess:
        sess['admin_id'] = 1

    res_app = client.get('/admin/appearance/')
    assert res_app.status_code == 200
    app_html = res_app.get_data(as_text=True)
    assert 'data-theme-val="maroon"' in app_html
    assert 'data-theme-val="navy"' in app_html
    assert 'data-theme-val="dark"' in app_html
    assert 'data-theme-val="custom"' in app_html
    assert 'data-font-val="inter"' in app_html
    assert 'data-font-val="playfair"' in app_html
    assert 'data-font-val="poppins"' in app_html
    assert 'live-preview-box' in app_html
    assert 'Save appearance' in app_html
    assert 'Reset to default' in app_html
    assert 'name="custom_p"' in app_html
    assert 'name="custom_bg"' in app_html
    assert 'name="custom_card"' in app_html
    assert 'name="custom_tx"' in app_html
    assert 'Low contrast, text may be hard to read' in app_html
    assert '#7a1230' in app_html
    assert '#0b2a6f' in app_html
    assert '#e0a93b' in app_html
    assert '#1f7a4d' in app_html
    assert '#6b3fa0' in app_html
    assert '#0f7b7b' in app_html
    assert '#d9622b' in app_html
    assert '#1a1a2e' in app_html

    # Extract CSRF token
    csrf_m = re.search(r'name=["\'](?:csrf_token|csrf_guard)["\']\s+value=["\']([^"\']+)["\']', app_html)
    csrf = csrf_m.group(1) if csrf_m else ''

    # 4. Save preset theme (navy + poppins)
    res_save = client.post('/admin/appearance/', data={
        'csrf_token': csrf,
        'csrf_guard': csrf,
        'action': 'save',
        'theme': 'navy',
        'font': 'poppins',
        'custom_p': '#0b2a6f',
        'custom_bg': '#eef3fb',
        'custom_card': '#ffffff',
        'custom_tx': '#10203f'
    }, follow_redirects=True)
    assert res_save.status_code == 200
    assert 'Saved ✓' in res_save.get_data(as_text=True)

    with app.app_context():
        row = get_db().execute('SELECT theme, font FROM site_settings WHERE id=1').fetchone()
        assert row['theme'] == 'navy'
        assert row['font'] == 'poppins'

    res_pub = client.get('/')
    assert 'data-theme="navy"' in res_pub.get_data(as_text=True)
    assert 'data-font="poppins"' in res_pub.get_data(as_text=True)

    # 5. Save custom colors palette
    res_custom = client.post('/admin/appearance/', data={
        'csrf_token': csrf,
        'csrf_guard': csrf,
        'action': 'save',
        'theme': 'custom',
        'font': 'inter',
        'custom_p': '#1f7a4d',
        'custom_bg': '#f0fff4',
        'custom_card': '#ffffff',
        'custom_tx': '#112211'
    }, follow_redirects=True)
    assert res_custom.status_code == 200
    assert 'Saved ✓' in res_custom.get_data(as_text=True)

    with app.app_context():
        row = get_db().execute('SELECT theme, font, custom_p, custom_bg, custom_card, custom_tx FROM site_settings WHERE id=1').fetchone()
        assert row['theme'] == 'custom'
        assert row['custom_p'] == '#1f7a4d'
        assert row['custom_bg'] == '#f0fff4'
        assert row['custom_card'] == '#ffffff'
        assert row['custom_tx'] == '#112211'

    res_pub_custom = client.get('/')
    pub_html = res_pub_custom.get_data(as_text=True)
    assert 'data-theme="custom"' in pub_html
    assert '<style>:root{--p:#1f7a4d;--bg:#f0fff4;--card:#ffffff;--tx:#112211;}</style>' in pub_html

    # 6. Reject invalid hex color
    res_bad = client.post('/admin/appearance/', data={
        'csrf_token': csrf,
        'csrf_guard': csrf,
        'action': 'save',
        'theme': 'custom',
        'font': 'inter',
        'custom_p': 'invalid-color',
        'custom_bg': '#f0fff4',
        'custom_card': '#ffffff',
        'custom_tx': '#112211'
    }, follow_redirects=True)
    assert 'Invalid hex color format' in res_bad.get_data(as_text=True)

    with app.app_context():
        row = get_db().execute('SELECT custom_p FROM site_settings WHERE id=1').fetchone()
        assert row['custom_p'] == '#1f7a4d'  # unchanged

    # 7. Reset to default
    res_reset = client.post('/admin/appearance/', data={
        'csrf_token': csrf,
        'csrf_guard': csrf,
        'action': 'reset'
    }, follow_redirects=True)
    assert res_reset.status_code == 200

    with app.app_context():
        row = get_db().execute('SELECT theme, font, custom_p, custom_bg, custom_card, custom_tx FROM site_settings WHERE id=1').fetchone()
        assert row['theme'] == 'maroon'
        assert row['font'] == 'inter'
        assert row['custom_p'] == '#7a1230'
        assert row['custom_bg'] == '#f7f8fc'
        assert row['custom_card'] == '#ffffff'
        assert row['custom_tx'] == '#1a1a2e'

    # 8. Trailing slash redirect check
    res_slash = client.get('/admin/appearance')
    assert res_slash.status_code in (301, 302, 308)
