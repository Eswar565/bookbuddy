import sys, os, re
sys.path.insert(0, os.path.abspath('.'))
from app import app, get_db

client = app.test_client()
with client.session_transaction() as sess:
    sess['admin_id'] = 1

# 1. Newspaper edit
print("--- 1. Testing Newspaper Edit in Admin ---")
get_resp = client.get('/admin/manage/publications/5/')
csrf_token = re.search(r'name="csrf_token"\s+value="([^"]+)"', get_resp.data.decode('utf-8')).group(1)

post_resp = client.post('/admin/manage/publications/5/', data={
    'csrf_token': csrf_token,
    'title': 'Book Buddy Times - November Edition',
    'kind': 'news',
    'volume': 'VOLUME 02',
    'issue_number': 'ISSUE 03',
    'edition': 'VOLUME 02 | ISSUE 03',
    'cover_path': '/media/admin/publications/61bdb56408a45414138427ad482887.webp',
    'file_path': '/media/admin/publications/a5f0f7db073dbcd1695e2360ee0876.pdf',
    'description': 'Comprehensive monthly reading report, school outreach, and young writer submissions.',
    'published_on': '2026-11-06',
    'position': '0',
    'is_active': '1'
}, follow_redirects=True)
assert post_resp.status_code == 200
print("Admin POST for Newspaper saved successfully.")

# Check public newspaper page
news_resp = client.get('/newspaper/')
news_html = news_resp.data.decode('utf-8')
assert 'Book Buddy Times - November Edition' in news_html
assert 'VOLUME 02' in news_html
print("PASS: Public newspaper page reflects updated title and volume!")

# 2. Magazine edit
print("\n--- 2. Testing Magazine Edit in Admin ---")
get_resp2 = client.get('/admin/manage/publications/2/')
csrf_token2 = re.search(r'name="csrf_token"\s+value="([^"]+)"', get_resp2.data.decode('utf-8')).group(1)

post_resp2 = client.post('/admin/manage/publications/2/', data={
    'csrf_token': csrf_token2,
    'title': 'Community Edition 1',
    'kind': 'magazine',
    'edition': 'Winter Special Edition',
    'badge_label': 'INTERACTIVE',
    'cover_path': '/static/uploads/04e716f9cbf20d48b9bfd220759274d1.png',
    'file_path': '/static/uploads/04e716f9cbf20d48b9bfd220759274d1.png',
    'description': 'Winter stories and interactive reader submissions.',
    'published_on': '2026-11-06',
    'position': '0',
    'is_active': '1'
}, follow_redirects=True)
assert post_resp2.status_code == 200
print("Admin POST for Magazine saved successfully.")

mag_resp = client.get('/magazine/')
mag_html = mag_resp.data.decode('utf-8')
assert 'Winter Special Edition' in mag_html
assert 'INTERACTIVE' in mag_html
print("PASS: Public magazine page reflects edition title and INTERACTIVE badge!")

# 3. Podcast edit with auto Spotify embed conversion
print("\n--- 3. Testing Podcast Edit with Spotify Auto-Conversion ---")
get_resp3 = client.get('/admin/manage/publications/6/')
csrf_token3 = re.search(r'name="csrf_token"\s+value="([^"]+)"', get_resp3.data.decode('utf-8')).group(1)

# Normal Spotify URL:
normal_spotify_url = "https://open.spotify.com/episode/3G7W5q6kKj4pM8b5zN9o4R"

post_resp3 = client.post('/admin/manage/publications/6/', data={
    'csrf_token': csrf_token3,
    'title': 'Inspiring Young Readers with Mel Robbins',
    'kind': 'podcast',
    'episode_label': 'EPISODE 05',
    'embed_url': normal_spotify_url,
    'cover_path': '/media/admin/publications/2600698127caeaa6f3c4ddd157233b.webp',
    'file_path': '/media/admin/publications/5abc7016f1616bd10d35754d255a65.pdf',
    'description': 'Setting intentions, reading habits and overcoming hesitation.',
    'published_on': '2026-11-05',
    'position': '0',
    'is_active': '1'
}, follow_redirects=True)
assert post_resp3.status_code == 200
print("Admin POST for Podcast saved successfully.")

with app.app_context():
    row = dict(get_db().execute('SELECT * FROM publications WHERE id=6').fetchone())
    print("Database embed_url after save:", row['embed_url'])
    assert "https://open.spotify.com/embed/episode/3G7W5q6kKj4pM8b5zN9o4R" in row['embed_url']
    print("PASS: Normal Spotify URL automatically converted to embed URL in database!")

pod_resp = client.get('/podcasts/')
pod_html = pod_resp.data.decode('utf-8')
assert 'Inspiring Young Readers with Mel Robbins' in pod_html
assert 'EPISODE 05' in pod_html
assert 'open.spotify.com/embed/episode/3G7W5q6kKj4pM8b5zN9o4R' in pod_html
print("PASS: Public podcasts page renders converted Spotify embed iframe!")

# 4. Podcast Fallback Test
print("\n--- 4. Testing Podcast Fallback Card ---")
with app.app_context():
    # Insert temporary podcast without embed URL
    get_db().execute("INSERT INTO publications (title, kind, episode_label, description, embed_url, is_active) VALUES ('Fallback Test Episode', 'podcast', 'EPISODE 99', 'No embed URL provided', '', 1)")
    get_db().commit()
    temp_id = get_db().execute("SELECT last_insert_rowid()").fetchone()[0]

fb_resp = client.get('/podcasts/')
fb_html = fb_resp.data.decode('utf-8')
assert 'Fallback Test Episode' in fb_html
assert 'Open on Spotify' in fb_html
print("PASS: Episode without Spotify embed cleanly renders fallback card with 'Open on Spotify' button!")

# Cleanup temporary episode
with app.app_context():
    get_db().execute("DELETE FROM publications WHERE id=?", (temp_id,))
    get_db().commit()
    print("Cleaned up temporary fallback test episode.")

print("\nALL ADMIN MEDIA CRUD TESTS PASSED SUCCESSFULLY!")

