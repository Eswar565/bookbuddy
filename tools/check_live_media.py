import urllib.request
import re

urls = [
    'https://book-buddy.in/newspaper/',
    'https://book-buddy.in/magazine/',
    'https://book-buddy.in/podcasts/',
    'https://book-buddy.in/podcast/',
    'https://book-buddy.in/publications/?kind=news',
    'https://book-buddy.in/publications/?kind=magazine',
    'https://book-buddy.in/publications/?kind=podcast',
]

headers = {'User-Agent': 'Mozilla/5.0'}

for u in urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"URL: {u} -> Status {resp.status}, final URL: {resp.url}")
            data = resp.read().decode('utf-8', errors='ignore')
            title = re.search(r'<title>(.*?)</title>', data, re.I)
            print(f"  Title: {title.group(1) if title else 'No title'}")
            # Look for h1, header pills, structure
            h1 = re.search(r'<h1[^>]*>(.*?)</h1>', data, re.I | re.S)
            print(f"  H1: {h1.group(1).strip() if h1 else 'No H1'}")
    except Exception as e:
        print(f"URL: {u} -> Error: {e}")

