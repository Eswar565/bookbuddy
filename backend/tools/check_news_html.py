import urllib.request
import re

html = urllib.request.urlopen('http://127.0.0.1:5001/newspaper/').read().decode('utf-8')
print("Pills found:", re.findall(r'class="bb-media-pill">(.*?)</span>', html))
print("H1 found:", [h.strip() for h in re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.S)])

