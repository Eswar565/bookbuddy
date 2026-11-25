from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = Path(r"C:\Users\Eswar\.gemini\antigravity\brain\8987ac8c-1fef-4599-b5b9-515703e201de")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page_m = browser.new_page(viewport={"width": 390, "height": 844})
    page_m.goto("http://127.0.0.1:5001/", wait_until="networkidle")
    page_m.evaluate("document.getElementById('bb8-hamburger-btn').click()")
    page_m.wait_for_timeout(500)
    page_m.screenshot(path=str(ARTIFACT_DIR / "removal_drawer_open_390.png"))
    browser.close()

print("Mobile drawer screenshot captured.")

