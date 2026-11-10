import urllib.request
import urllib.parse
import http.cookiejar
import re
import sys

base_url = "http://127.0.0.1:5001"

forbidden_strings = [
    "Community Podcast",
    "Listen to the Podcast",
    "Stories & Conversations",
    "recording room",
    "Explore Membership",
    "BOOK BUDDY MEMBERSHIP",
    "Membership Details",
    "Membership & Plans"
]

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# Get login page to grab csrf_guard
resp = opener.open(f"{base_url}/accounts/login/")
html = resp.read().decode('utf-8')
csrf_match = re.search(r'name=["\']csrf_guard["\']\s+value=["\']([^"\']+)["\']', html)
csrf_guard = csrf_match.group(1) if csrf_match else ""

# Submit login
login_data = urllib.parse.urlencode({
    'csrf_guard': csrf_guard,
    'email': 'admin@bookbuddy.internal',
    'password': 'admin',
    'next': ''
}).encode('utf-8')

req = urllib.request.Request(f"{base_url}/login/", data=login_data, headers={'User-Agent': 'Mozilla/5.0'})
resp = opener.open(req)
print("Login response URL:", resp.geturl())

urls_to_check = [
    ("/", "Home Page"),
    ("/about/", "About Page"),
    ("/library/", "Library Page"),
    ("/events/", "Events Page"),
    ("/publications/?kind=news", "Publications Newspaper Page"),
    ("/contact/", "Contact Page"),
    ("/admin/dashboard/", "Admin Dashboard"),
    ("/admin/manage/home-sections/", "Admin Home Sections List")
]

all_passed = True
print("\n" + "=" * 70)
print(f"{'Page':<35} | {'Status':<6} | {'Forbidden Found'}")
print("-" * 70)

for path, label in urls_to_check:
    full_url = f"{base_url}{path}"
    req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
    res = opener.open(req)
    content = res.read().decode('utf-8')
    
    found = []
    for s in forbidden_strings:
        if s.lower() in content.lower():
            found.append(s)
            
    status = "FAIL" if found else "PASS"
    if found:
        all_passed = False
    print(f"{label:<35} | {status:<6} | {', '.join(found) if found else 'None (Clean)'}")

print("=" * 70)
if all_passed:
    print("ALL HTML ASSERTIONS PASSED! No forbidden strings found on any page.")
else:
    print("SOME ASSERTIONS FAILED.")
    sys.exit(1)
