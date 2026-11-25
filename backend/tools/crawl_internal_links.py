import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from collections import deque
import sys

base_url = "http://127.0.0.1:5001"
start_url = f"{base_url}/"

visited = set()
queue = deque([start_url])
errors = []
checked_count = 0

print(f"Starting link crawl from {start_url} ...")

while queue and checked_count < 200:
    url = queue.popleft()
    if url in visited:
        continue
    visited.add(url)
    checked_count += 1
    
    # Don't follow logout or admin delete/destructive paths during simple crawl
    if any(x in url for x in ['/logout', '/delete', '/drop', '/remove']):
        continue

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req)
        status = res.getcode()
        content_type = res.headers.get('Content-Type', '')
        
        if status >= 400:
            errors.append((url, status))
            print(f"FAIL: {url} returned {status}")
            continue
            
        if 'text/html' in content_type:
            html = res.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:') or href.startswith('tel:'):
                    continue
                parsed = urllib.parse.urljoin(url, href)
                if parsed.startswith(base_url) and parsed not in visited:
                    queue.append(parsed)
    except urllib.error.HTTPError as e:
        errors.append((url, e.code))
        print(f"HTTP ERROR: {url} -> {e.code}")
    except Exception as e:
        errors.append((url, str(e)))
        print(f"ERROR: {url} -> {e}")

print(f"\nCrawl finished. Visited {checked_count} URLs.")
if errors:
    print(f"Encountered {len(errors)} errors:")
    for u, err in errors:
        print(f"  {u}: {err}")
    sys.exit(1)
else:
    print("ALL INTERNAL LINKS CRAWLED CLEANLY WITH 0 ERRORS!")

