import urllib.request
import re

try:
    with urllib.request.urlopen('http://localhost:5001/gallery/') as resp:
        status = resp.status
        html = resp.read().decode('utf-8')
        print(f"Status: {status}")
        print("Capturing Moments in HTML:", "Capturing Moments, Creating Memories" in html)
        print("Our Gallery in HTML:", "Our Gallery" in html)
        print("Tile count:", len(re.findall(r'class="[^"]*bb-gallery-tile[^"]*"', html)))
        print("Captions present:", "bb-gallery-caption" in html or "<figcaption" in html)
        print("Missing 'demo' item:", "demo" not in html)
except Exception as e:
    print("Error:", e)

