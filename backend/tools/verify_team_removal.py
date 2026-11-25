import urllib.request
import urllib.parse
import http.cookiejar
import re
import sys

base_url = "http://127.0.0.1:5001"

forbidden_strings = [
    "MEET OUR TEAM",
    "Our library team",
    "demo title",
    "Full Stack Development",
    "name=\"team_heading\"",
    "team_heading",
    "team_members",
    "/admin/manage/team/",
    "bb24-experts",
    "s33-experts",
    "About team"
]

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# Login as admin
resp = opener.open(f"{base_url}/admin/login/")
html = resp.read().decode('utf-8')
csrf_match = re.search(r'name=["\']csrf_guard["\']\s+value=["\']([^"\']+)["\']', html)
csrf_guard = csrf_match.group(1) if csrf_match else ""

login_data = urllib.parse.urlencode({
    'csrf_guard': csrf_guard,
    'email': 'admin@gmail.com',
    'password': 'admin123',
    'next': ''
}).encode('utf-8')

req = urllib.request.Request(f"{base_url}/admin/login/", data=login_data, headers={'User-Agent': 'Mozilla/5.0'})
resp = opener.open(req)
print("Admin login URL:", resp.geturl())

urls_to_check = [
    ("/about/", "Public About Page"),
    ("/admin/about-editor/", "Admin About Editor"),
    ("/admin/page-map/", "Admin Page Map"),
    ("/admin/dashboard/", "Admin Dashboard"),
    ("/admin/manage/pages/", "Admin Website Pages"),
    ("/admin/settings/", "Admin Settings")
]

all_passed = True
print("\n" + "=" * 70)
print(f"{'Page':<30} | {'Status':<6} | {'Forbidden Found'}")
print("-" * 70)

for path, label in urls_to_check:
    full_url = f"{base_url}{path}"
    req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
    res = opener.open(req)
    content = res.read().decode('utf-8')
    
    found = []
    for s in forbidden_strings:
        if s.lower() in content.lower():
            # Special check: make sure it's not a generic word
            found.append(s)
            
    status = "FAIL" if found else "PASS"
    if found:
        all_passed = False
    print(f"{label:<30} | {status:<6} | {', '.join(found) if found else 'None (Clean)'}")

# Check that /admin/manage/team/ returns 404
team_url = f"{base_url}/admin/manage/team/"
try:
    req = urllib.request.Request(team_url, headers={'User-Agent': 'Mozilla/5.0'})
    res = opener.open(req)
    print(f"{'/admin/manage/team/':<30} | FAIL   | Returned {res.getcode()} instead of 404")
    all_passed = False
except urllib.error.HTTPError as e:
    if e.code == 404:
        print(f"{'/admin/manage/team/':<30} | PASS   | Returned 404 Not Found as expected")
    else:
        print(f"{'/admin/manage/team/':<30} | FAIL   | Returned {e.code}")
        all_passed = False

print("=" * 70)
if all_passed:
    print("ALL VERIFICATION CHECKS PASSED!")
else:
    print("SOME CHECKS FAILED.")
    sys.exit(1)

