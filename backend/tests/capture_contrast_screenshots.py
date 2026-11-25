from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = Path(r"C:\Users\Eswar\.gemini\antigravity\brain\8987ac8c-1fef-4599-b5b9-515703e201de")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

targets = [
    ("hero_buttons", ".bb8-hero-cta"),
    ("publications_buttons", "#publications .bb8-pub-actions"),
    ("reviews_button", "#reviews .bb8-reviews-card"),
    ("footer", "footer.bb8-footer")
]

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 900})
    page.goto("http://127.0.0.1:5001/", wait_until="networkidle")
    
    for name, selector in targets:
        loc = page.locator(selector).first
        if loc.count() > 0:
            out_path = ARTIFACT_DIR / f"contrast_after_{name}.png"
            loc.screenshot(path=str(out_path))
            print(f"Captured {name} -> {out_path}")
        else:
            print(f"Selector not found: {selector}")
            
    browser.close()
print("Screenshots captured successfully.")

