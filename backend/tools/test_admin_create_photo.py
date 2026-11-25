import sys, os, re
sys.path.insert(0, os.path.abspath('.'))
from app import app, get_db

client = app.test_client()
with client.session_transaction() as sess:
    sess['admin_id'] = 1

get_resp = client.get('/admin/manage/gallery/0/')
csrf_token = re.search(r'name="csrf_token"\s+value="([^"]+)"', get_resp.data.decode('utf-8')).group(1)

post_resp = client.post('/admin/manage/gallery/0/', data={
    'csrf_token': csrf_token,
    'image_path': '/static/uploads/04e716f9cbf20d48b9bfd220759274d1.png',
    'alt_text': 'Single photo test creation',
    'position': '99',
    'is_active': '0'
})
print("post_resp status:", post_resp.status_code)
print("Location:", post_resp.headers.get('Location'))

with app.app_context():
    row = get_db().execute('SELECT * FROM gallery_items WHERE alt_text = ?', ('Single photo test creation',)).fetchone()
    if row:
        row = dict(row)
        print("Created row in DB:", row)
        get_db().execute('DELETE FROM gallery_items WHERE id = ?', (row['id'],))
        get_db().commit()
        print("Cleaned up test row.")
    else:
        print("Not found in DB!")
