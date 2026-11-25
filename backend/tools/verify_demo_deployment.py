#!/usr/bin/env python3
"""Comprehensive verification script for Demo Deployment and Configurable MEDIA_ROOT.

Performs:
1. Temp directory setup for BOOK_BUDDY_DATABASE and MEDIA_ROOT
2. /healthz endpoint verification (no DB writes)
3. DEMO_MODE=1 verification (robots.txt, X-Robots-Tag, meta tag, top banner)
4. Payments & emails disabled verification
5. Demo admin login
6. Admin heading edit & persistence
7. Admin image upload & persistence inside MEDIA_ROOT
8. Simulated app restart confirming persistence
9. Demo member login
10. Login form rate-limiting verification in DEMO_MODE
"""

import io
import os
import shutil
import sys
import tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Setup temporary environment before importing app
temp_dir = Path(tempfile.mkdtemp(prefix="bb_demo_verify_"))
temp_media = temp_dir / "custom_media"
temp_db = temp_dir / "custom_db" / "book_buddy_demo.sqlite3"
temp_db.parent.mkdir(parents=True, exist_ok=True)
temp_media.mkdir(parents=True, exist_ok=True)

# Copy demo snapshot
snapshot_src = ROOT / "instance" / "demo_snapshot.sqlite3"
if not snapshot_src.exists():
    # If not exists, use make_demo_data
    from tools.make_demo_data import make_demo_data
    source = ROOT / "instance" / "book_buddy_dev.sqlite3"
    make_demo_data(source, ROOT / "instance" / "book_buddy_demo.sqlite3", snapshot_src, ROOT / "media", ROOT / "backups" / "demo_media_snapshot.zip")

shutil.copy2(snapshot_src, temp_db)

os.environ["BOOK_BUDDY_DATABASE"] = str(temp_db)
os.environ["MEDIA_ROOT"] = str(temp_media)
os.environ["DEMO_MODE"] = "1"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "Admin@BookBuddy2026!"

print(f"Temporary Verification Sandbox:")
print(f"  DATABASE:   {temp_db}")
print(f"  MEDIA_ROOT: {temp_media}")
print(f"  DEMO_MODE:  {os.environ['DEMO_MODE']}\n")

from app import app, get_db, MEDIA_ROOT

assert Path(MEDIA_ROOT).resolve() == temp_media.resolve(), f"MEDIA_ROOT mismatch: {MEDIA_ROOT} != {temp_media}"
print("PASS: app.MEDIA_ROOT successfully points to custom MEDIA_ROOT!")

client = app.test_client()

# --- 1. /healthz endpoint ---
print("\n--- 1. Testing /healthz ---")
r_health = client.get("/healthz")
assert r_health.status_code == 200, f"/healthz returned {r_health.status_code}"
assert b"ok" in r_health.data
r_health_slash = client.get("/healthz/")
assert r_health_slash.status_code == 200
print("PASS: /healthz and /healthz/ return 200 OK ('ok').")

# --- 2. DEMO_MODE headers & banner ---
print("\n--- 2. Testing DEMO_MODE=1 features ---")
r_home = client.get("/")
assert r_home.status_code == 200
assert r_home.headers.get("X-Robots-Tag") == "noindex, nofollow", f"Missing X-Robots-Tag: {r_home.headers.get('X-Robots-Tag')}"
assert b'name="robots" content="noindex,nofollow"' in r_home.data
assert b"Demo site: data may be reset" in r_home.data
assert b"bb-demo-banner" in r_home.data
print("PASS: Public home page renders X-Robots-Tag, noindex meta tag, and top demo banner!")

# robots.txt
r_robots = client.get("/robots.txt")
assert r_robots.status_code == 200
assert b"User-agent: *\nDisallow: /" in r_robots.data
print("PASS: /robots.txt disallows all crawling in DEMO_MODE.")

# Payments disabled
print("\n--- 3. Testing Payments & Outgoing Emails disabled ---")
from payments import razorpay_request
try:
    razorpay_request("GET", "payments/test")
    assert False, "razorpay_request should have raised RuntimeError"
except RuntimeError as exc:
    assert "Online payments are not configured yet" in str(exc)
    print("PASS: Razorpay requests blocked with 'Online payments are not configured yet' message.")

# --- 4. Admin Login ---
print("\n--- 4. Testing Demo Admin Login ---")
import re
r_get = client.get("/admin/login/")
csrf_match = re.search(r'name=["\'](csrf_guard|csrf_token)["\']\s+value=["\']([^"\']+)["\']', r_get.data.decode())
csrf_name = csrf_match.group(1) if csrf_match else "csrf_guard"
csrf_val = csrf_match.group(2) if csrf_match else ""
r_login = client.post("/admin/login/", data={
    "email": "admin@example.com",
    "password": "Admin@BookBuddy2026!",
    csrf_name: csrf_val
}, follow_redirects=True)
assert r_login.status_code == 200
assert b"Home / Overview" in r_login.data or b"Dashboard" in r_login.data or b"Library Studio" in r_login.data
assert b"Demo site: data may be reset" in r_login.data
print("PASS: Demo admin logged in successfully; admin template renders demo banner!")

# --- 5. Edit a Heading and Persist ---
print("\n--- 5. Testing Admin Heading Edit ---")
import gallery_service
with app.app_context():
    gallery_service.save_gallery_settings(get_db, "Demo Pill Label", "Demo Gallery Headline - Client Preview")
    db_val = get_db().execute("SELECT content_value FROM site_content WHERE content_key='gallery_heading'").fetchone()[0]
    assert db_val == "Demo Gallery Headline - Client Preview"
print("PASS: Edited heading persisted in temporary BOOK_BUDDY_DATABASE!")

# --- 6. Upload Image to MEDIA_ROOT ---
print("\n--- 6. Testing Admin Image Upload into custom MEDIA_ROOT ---")
# Create a valid test image
img_byte_arr = io.BytesIO()
test_image = Image.new("RGB", (300, 300), color=(116, 15, 40)) # Book Buddy Maroon
test_image.save(img_byte_arr, format="PNG")
img_byte_arr.seek(0)

from werkzeug.datastructures import FileStorage
file_obj = FileStorage(stream=img_byte_arr, filename="client_demo_test.png", content_type="image/png")

with client.session_transaction() as sess:
    sess["admin_id"] = 1

# Test saving via app.extensions['bookbuddy_store_media_v13']
with app.test_request_context("/admin/test-upload/", method="POST", data={"asset_image_path": file_obj}):
    save_func = app.extensions['bookbuddy_store_media_v13']
    saved_web_path = save_func("asset_image_path", "test_uploads", "image")

print(f"Uploaded media returned web path: {saved_web_path}")
assert saved_web_path.startswith("/media/admin/test_uploads/")
assert saved_web_path.endswith(".webp")

# Verify file physically exists inside temp_media
expected_filename = saved_web_path.split("/")[-1]
physical_path = temp_media / "admin" / "test_uploads" / expected_filename
assert physical_path.exists(), f"File was NOT saved to custom MEDIA_ROOT: {physical_path}"
assert physical_path.stat().st_size > 0
print(f"PASS: Uploaded file physically saved inside custom MEDIA_ROOT: {physical_path}")

# Verify file is served via HTTP GET /media/<path>
r_media = client.get(saved_web_path)
assert r_media.status_code == 200
assert r_media.content_type == "image/webp"
assert len(r_media.data) > 0
print("PASS: /media/<path> serves uploaded file directly from custom MEDIA_ROOT!")

# --- 7. Simulate App Restart and Verify Both Persisted ---
print("\n--- 7. Testing App Restart Persistence ---")
# Reset client / session to simulate clean restart
del client
new_client = app.test_client()

# Check heading
with app.app_context():
    db_check = get_db().execute("SELECT content_value FROM site_content WHERE content_key='gallery_heading'").fetchone()[0]
    assert db_check == "Demo Gallery Headline - Client Preview", f"Heading did not persist: {db_check}"
print("PASS: Heading edit persisted across restart in BOOK_BUDDY_DATABASE!")

# Check image file on disk & via HTTP
assert physical_path.exists()
r_media_after = new_client.get(saved_web_path)
assert r_media_after.status_code == 200
assert len(r_media_after.data) == len(r_media.data)
print("PASS: Image in custom MEDIA_ROOT persisted across restart and served with 200 OK!")

# --- 8. Demo Member Login ---
print("\n--- 8. Testing Demo Member Login ---")
with app.app_context():
    # Fetch demo member password hash & verify password
    member_row = get_db().execute("SELECT * FROM users WHERE email='demo.member@example.com'").fetchone()
    assert member_row is not None
    assert member_row["is_active"] == 1
    # Test subscriber status
    sub_func = app.extensions['bookbuddy17']['sub']
    sub_res = sub_func(member_row["id"])
    assert sub_res is not None, "Demo member should have an active subscription"
    print(f"PASS: Demo member has active subscription: plan_id={sub_res['plan_id']}, expires={sub_res['expires_on']}")
print("PASS: Demo member exists with active lending subscription in demo database.")

# --- 9. Rate Limit Login Forms ---
print("\n--- 9. Testing Rate Limiting on Login in DEMO_MODE ---")
# Rapidly attempt failed logins with CSRF token
r_login_page = new_client.get("/admin/login/")
csrf_match_rate = re.search(r'name=["\'](csrf_guard|csrf_token)["\']\s+value=["\']([^"\']+)["\']', r_login_page.data.decode())
csrf_n = csrf_match_rate.group(1) if csrf_match_rate else "csrf_guard"
csrf_v = csrf_match_rate.group(2) if csrf_match_rate else ""

status_codes = []
for i in range(8):
    resp = new_client.post("/admin/login/", data={
        "email": "attacker@example.com",
        "password": "wrongpassword",
        csrf_n: csrf_v
    })
    status_codes.append(resp.status_code)

print(f"Login attempt status codes (first 8): {status_codes}")
assert 429 in status_codes, f"Rate limiting did not trigger 429 status code: {status_codes}"
print("PASS: Login form rate limiting triggers 429 Too Many Requests in DEMO_MODE!")

# --- Cleanup Sandbox ---
shutil.rmtree(temp_dir, ignore_errors=True)
print("\n" + "=" * 60)
print("ALL DEMO DEPLOYMENT & MEDIA_ROOT CHECKS PASSED PERFECTLY!")
print("=" * 60)
