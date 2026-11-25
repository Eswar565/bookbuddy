import requests
import re
import sys

BASE_URL = "http://127.0.0.1:5001"

FORBIDDEN_PATTERNS = [
    r"\blearn\s*&\s*play\b",
    r"\blearn[-_]play\b",
    r"\blearning\s+hub\b",
    r"\bskill\s+modules\b",
    r"\bbrain\s+twisters\b",
    r"\blogic\s+puzzles\b",
    r"\btimed\s+challenges\b",
    r"\bbeyond\s+school\b",
    r"\binnovation\s+lab\b",
    r"\bbuilt\s+by\s+our\s+interns\b",
    r"\bmvps\b",
    r"\bweb\s+tools\b",
    r"\btech\s+products\b",
    r"\bsharpen\s+your\s+mind\b",
    r"\bdaily\s+challenges\b",
    r"\bkids\s+math\b",
    r"\bfinancial\s+literacy\b",
    r"\bbusiness\s+analyst\b",
    r"\bcollege-projects\b",
]

session = requests.Session()

# 1. Login to admin
login_page = session.get(f"{BASE_URL}/admin/login/")
if login_page.status_code != 200:
    print(f"Failed to load login page: {login_page.status_code}")
    sys.exit(1)

# Extract CSRF token
csrf_match = re.search(r'name=["\']csrf_guard["\']\s+value=["\']([^"\']+)["\']', login_page.text)
csrf_guard = csrf_match.group(1) if csrf_match else ""

resp = session.post(
    f"{BASE_URL}/admin/login/?next=",
    data={"email": "admin@gmail.com", "password": "admin123", "csrf_guard": csrf_guard},
    allow_redirects=True,
)
if resp.status_code != 200 or "/admin/login/" in resp.url:
    print("Admin login failed!")
    sys.exit(1)
print("Admin login successful!")

PAGES_TO_CHECK = [
    "/admin/dashboard/",
    "/admin/about-editor/",
    "/admin/library-center/",
    "/admin/manage/books/",
    "/admin/manage/events/",
    "/admin/manage/events/0/",
    "/admin/manage/publications/",
    "/admin/manage/gallery/",
    "/admin/manage/enquiries/",
    "/admin/manage/partners/",
    "/admin/manage/members/",
    "/admin/manage/home-sections/",
    "/admin/manage/home-sections/1/",
    "/admin/manage/navigation/",
    "/admin/page-map/",
    "/admin/notifications/",
    "/admin/settings/",
    "/admin/password/",
]

violations = []
status_ok = True

for path in PAGES_TO_CHECK:
    r = session.get(f"{BASE_URL}{path}")
    if r.status_code != 200:
        print(f"ERROR: {path} returned status {r.status_code}")
        status_ok = False
        continue
    
    html = r.text
    for pattern in FORBIDDEN_PATTERNS:
        matches = re.findall(pattern, html, flags=re.IGNORECASE)
        if matches:
            violations.append((path, pattern, matches))
            print(f"VIOLATION in {path}: pattern '{pattern}' matched {matches}")

if not violations and status_ok:
    print(f"\nSUCCESS: All {len(PAGES_TO_CHECK)} admin pages loaded cleanly (200 OK) with ZERO forbidden terms!")
else:
    print(f"\nFAILED: Found {len(violations)} violations across tested pages.")
    sys.exit(1)
