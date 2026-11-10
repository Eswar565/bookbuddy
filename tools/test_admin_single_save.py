import sys, os, re
sys.path.insert(0, os.path.abspath('.'))
from app import app, get_db

client = app.test_client()
with client.session_transaction() as sess:
    sess['admin_id'] = 1

# 1. GET form to extract csrf_token
get_resp = client.get('/admin/manage/gallery/2/')
csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', get_resp.data.decode('utf-8'))
csrf_token = csrf_match.group(1) if csrf_match else ''
print("Found CSRF token:", bool(csrf_token))

post_resp = client.post('/admin/manage/gallery/2/', data={
    'csrf_token': csrf_token,
    'image_path': '/media/admin/gallery/030d1457308724467f99b91370da37.webp',
    'alt_text': 'Children reading story books together',
    'position': '0',
    'is_active': '1'
}, follow_redirects=True)
print("POST status:", post_resp.status_code)

with app.app_context():
    row = dict(get_db().execute('SELECT * FROM gallery_items WHERE id = 2').fetchone())
    print("Updated DB row:", row)
