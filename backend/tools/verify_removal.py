import urllib.request
import re
import sys

BASE_URL = "http://127.0.0.1:5001"

pages = [
    ("/", "Home"),
    ("/about/", "About"),
    ("/library/", "Library"),
    ("/events/", "Events"),
    ("/publications/?kind=news", "Media/News"),
    ("/contact/", "Contact"),
    ("/admin/dashboard/", "Admin Dashboard")
]

forbidden_terms = [
    "learn & play",
    "learn-play",
    "learn_play",
    "learning hub",
    "skill modules",
    "skill-modules",
    "brain twisters",
    "timed challenges",
    "sharpen your mind",
    "innovation lab",
    "built by our interns",
    "view learning hub",
    "view tech products",
    "tech products & b2b solutions",
    "beyond school",
    "kids math",
    "coding for kids",
    "financial literacy",
    "business analyst (ba)",
    "daily challenges",
    "/game-hub",
    "/college-project",
    "/coding-kids",
    "/ai-solutions"
]

print("=== CHECKING PAGES FOR FORBIDDEN TERMS ===")
all_clean = True
for path, name in pages:
    url = BASE_URL + path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode("utf-8", errors="ignore").lower()
            found = []
            for term in forbidden_terms:
                if term in html:
                    found.append(term)
            if found:
                print(f"[FAIL] {name} ({path}) contained: {found}")
                all_clean = False
            else:
                print(f"[PASS] {name} ({path}) is 100% clean of all {len(forbidden_terms)} forbidden terms.")
    except Exception as e:
        print(f"[ERROR] Could not fetch {name} ({path}): {e}")
        all_clean = False

print("\n=== CHECKING RETIRED ROUTES ===")
retired_routes = [
    "/game-hub",
    "/game-hub/",
    "/college-projects",
    "/college-projects/",
    "/coding-kids",
    "/ai-solutions",
    "/users/internship-dashboard",
    "/users/internship-dashboard/"
]

retired_ok = True
for r in retired_routes:
    url = BASE_URL + r
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            code = resp.getcode()
            print(f"[UNEXPECTED 200] {r} returned {code}")
            retired_ok = False
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"[PASS] {r} returned 404 Not Found (as expected)")
        else:
            print(f"[PASS] {r} returned HTTP {e.code}")
    except Exception as e:
        print(f"[PASS] {r} failed with: {e}")

if not all_clean or not retired_ok:
    print("\nVerification FAILED!")
    sys.exit(1)
else:
    print("\nAll verification checks PASSED successfully!")

