import urllib.request
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

# We need session cookie for admin
import urllib.parse
import http.cookiejar

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# Login to admin
login_data = urllib.parse.urlencode({'email': 'admin@bookbuddy.internal', 'password': 'admin'}).encode('utf-8')
try:
    req = urllib.request.Request(f"{base_url}/accounts/login/", data=login_data, headers={'User-Agent': 'Mozilla/5.0'})
    resp = opener.open(req)
except Exception as e:
    print(f"Login attempt 1: {e}")

# Check with admin session
results = []
all_passed = True

print(f"{'Page':<35} | {'Status':<6} | {'Forbidden Found'}")
print("-" * 65)

for path, label in urls_to_check:
    full_url = f"{base_url}{path}"
    try:
        req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
        res = opener.open(req)
        html = res.read().decode('utf-8')
        
        found = []
        for s in forbidden_strings:
            if s.lower() in html.lower():
                found.append(s)
        
        status = "FAIL" if found else "PASS"
        if found:
            all_passed = False
        print(f"{label:<35} | {status:<6} | {', '.join(found) if found else 'None (Clean)'}")
        results.append((label, path, status, found))
    except Exception as e:
        print(f"{label:<35} | ERROR  | {e}")
        all_passed = False

if all_passed:
    print("\nALL HTML ASSERTIONS PASSED! No forbidden strings found.")
else:
    print("\nSOME ASSERTIONS FAILED.")
    sys.exit(1)

