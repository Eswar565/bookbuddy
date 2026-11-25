import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app import app

client = app.test_client()
with client.session_transaction() as sess:
    sess['admin_id'] = 1

resp = client.get('/admin/manage/gallery/')
print("Admin gallery status:", resp.status_code)
html = resp.data.decode('utf-8')
print("Pill input in admin:", 'name="gallery_pill"' in html)
print("Heading input in admin:", 'name="gallery_heading"' in html)
print("Multi-upload input in admin:", 'type="file"' in html and 'multiple' in html)
print("No title/desc inputs:", 'name="title"' not in html and 'name="description"' not in html)
print("Missing file badge shown for ID 1:", 'Missing File' in html)
print("Test data hint shown for ID 2:", 'demo1' in html)
