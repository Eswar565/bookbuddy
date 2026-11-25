import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app import app

client = app.test_client()
with client.session_transaction() as sess:
    sess['admin_id'] = 1

resp = client.get('/admin/manage/gallery/2/')
print("Admin single photo edit status:", resp.status_code)
html = resp.data.decode('utf-8')
print("Contains title field:", 'name="title"' in html)
print("Contains description field:", 'name="description"' in html)
print("Contains alt_text field:", 'name="alt_text"' in html)

