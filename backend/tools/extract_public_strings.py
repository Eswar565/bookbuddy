import requests
from bs4 import BeautifulSoup
import sqlite3

con = sqlite3.connect("instance/book_buddy_dev.sqlite3")
con.row_factory = sqlite3.Row

# Load site_content
content_rows = con.execute("SELECT content_key, content_value FROM site_content").fetchall()
site_content = {r["content_key"]: r["content_value"] for r in content_rows}

# Load homepage_sections
hp_rows = con.execute("SELECT * FROM homepage_sections").fetchall()
hp_sections = [dict(r) for r in hp_rows]

# Load site_navigation
nav_rows = con.execute("SELECT * FROM site_navigation WHERE is_active=1").fetchall()
nav_items = [dict(r) for r in nav_rows]

resp = requests.get("http://127.0.0.1:5001/")
soup = BeautifulSoup(resp.text, "html.parser")

print("--- HEADER LINKS ---")
for a in soup.select("header a, nav a"):
    text = a.get_text(strip=True)
    href = a.get("href")
    if text:
        print(f"Header Link: '{text}' -> {href}")

print("\n--- HERO SECTION ---")
hero = soup.select_one(".bb8-hero")
if hero:
    eyebrow = hero.select_one(".bb8-eyebrow")
    l1 = hero.select_one(".bb8-hero-line1")
    l2 = hero.select_one(".bb8-hero-line2")
    p = hero.select_one(".bb8-hero-text")
    ctas = hero.select(".bb8-hero-cta a")
    print("Eyebrow:", eyebrow.get_text(strip=True) if eyebrow else None)
    print("Line 1:", l1.get_text(strip=True) if l1 else None)
    print("Line 2:", l2.get_text(strip=True) if l2 else None)
    print("Paragraph:", p.get_text(strip=True) if p else None)
    for c in ctas:
        print("CTA:", c.get_text(strip=True), "->", c.get("href"))

print("\n--- COMMUNITY SECTION ---")
comm = soup.select_one("#community")
if comm:
    print("Heading:", comm.select_one(".bb8-section-title").get_text(strip=True) if comm.select_one(".bb8-section-title") else None)
    print("Subtext:", comm.select_one(".bb8-section-subtext").get_text(strip=True) if comm.select_one(".bb8-section-subtext") else None)
    for card in comm.select(".bb8-event-card"):
        tag = card.select_one(".bb8-card-tag")
        title = card.select_one(".bb8-card-title")
        sched = card.select_one(".bb8-card-schedule")
        desc = card.select_one(".bb8-card-desc")
        btn = card.select_one("a")
        print("  Event Card:", tag.get_text(strip=True) if tag else None, "|", title.get_text(strip=True) if title else None, "|", sched.get_text(strip=True) if sched else None)
        print("    Desc:", desc.get_text(strip=True) if desc else None)
        print("    Btn:", btn.get_text(strip=True) if btn else None, "->", btn.get("href") if btn else None)

print("\n--- PUBLICATIONS SECTION ---")
pubs = soup.select_one("#publications")
if pubs:
    print("Heading:", pubs.select_one(".bb8-section-title").get_text(strip=True) if pubs.select_one(".bb8-section-title") else None)
    print("Subtext:", pubs.select_one(".bb8-section-subtext").get_text(strip=True) if pubs.select_one(".bb8-section-subtext") else None)
    for card in pubs.select(".bb8-pub-card"):
        img = card.select_one("img")
        tag = card.select_one(".bb8-card-tag")
        title = card.select_one(".bb8-pub-title")
        desc = card.select_one(".bb8-pub-desc")
        btn = card.select_one("a")
        print("  Pub Card:")
        print("    Img:", img.get("src") if img else None, "alt:", img.get("alt") if img else None)
        print("    Tag:", tag.get_text(strip=True) if tag else None)
        print("    Title:", title.get_text(strip=True) if title else None)
        print("    Desc:", desc.get_text(strip=True) if desc else None)
        print("    Btn:", btn.get_text(strip=True) if btn else None, "->", btn.get("href") if btn else None)

print("\n--- REVIEWS SECTION ---")
rev = soup.select_one("#reviews")
if rev:
    print("Heading:", rev.select_one(".bb8-section-title").get_text(strip=True) if rev.select_one(".bb8-section-title") else None)
    print("Rating:", rev.select_one(".bb8-rating-number").get_text(strip=True) if rev.select_one(".bb8-rating-number") else None)
    print("Count:", rev.select_one(".bb8-rating-count").get_text(strip=True) if rev.select_one(".bb8-rating-count") else None)
    for q in rev.select(".bb8-quote-card"):
        text = q.select_one(".bb8-quote-text")
        author = q.select_one(".bb8-quote-author")
        print("  Quote:", text.get_text(strip=True) if text else None, "by", author.get_text(strip=True) if author else None)
    rev_btn = rev.select_one(".bb8-reviews-card > a")
    print("Review CTA:", rev_btn.get_text(strip=True) if rev_btn else None, "->", rev_btn.get("href") if rev_btn else None)

print("\n--- OTHER SECTIONS ---")
for sec in soup.select("main > section"):
    sec_id = sec.get("id")
    if sec_id not in ("community", "publications", "reviews") and "bb8-hero" not in sec.get("class", []):
        print("Other Section ID:", sec_id, "Title:", sec.select_one(".bb8-section-title").get_text(strip=True) if sec.select_one(".bb8-section-title") else None)

print("\n--- FOOTER ---")
footer = soup.select_one("footer")
if footer:
    brand_p = footer.select_one(".bb8-footer-brand p")
    print("Footer Bio:", brand_p.get_text(strip=True) if brand_p else None)
    cols = footer.select(".bb8-footer-col")
    for col in cols:
        h3 = col.select_one("h3")
        print("  Col:", h3.get_text(strip=True) if h3 else None)
        for li in col.select("li a"):
            print("    Link:", li.get_text(strip=True), "->", li.get("href"))
        for p in col.select("p"):
            print("    P:", p.get_text(separator=" ", strip=True))
    bot = footer.select_one(".bb8-footer-bottom")
    if bot:
        print("Footer Bottom Copy:", bot.select_one("span").get_text(strip=True) if bot.select_one("span") else None)
        for a in bot.select("a"):
            print("Footer Bottom Link:", a.get_text(strip=True), "->", a.get("href"))

