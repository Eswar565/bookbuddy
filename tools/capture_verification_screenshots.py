from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = Path(r"C:\Users\Eswar\.gemini\antigravity\brain\8987ac8c-1fef-4599-b5b9-515703e201de")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    
    # 1. Desktop 1920
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto("http://127.0.0.1:5001/", wait_until="networkidle")
    page.screenshot(path=str(ARTIFACT_DIR / "removal_verification_home_1920.png"), full_page=True)
    
    # Header
    page.locator("header.bb8-header").screenshot(path=str(ARTIFACT_DIR / "removal_header_1920.png"))
    # Hero
    page.locator(".bb8-hero").screenshot(path=str(ARTIFACT_DIR / "removal_hero_1920.png"))
    # Footer
    page.locator("footer.bb8-footer").screenshot(path=str(ARTIFACT_DIR / "removal_footer_1920.png"))
    page.close()
    
    # 2. Mobile 390
    page_m = browser.new_page(viewport={"width": 390, "height": 844})
    page_m.goto("http://127.0.0.1:5001/", wait_until="networkidle")
    page_m.screenshot(path=str(ARTIFACT_DIR / "removal_verification_home_390.png"), full_page=True)
    
    # Open mobile drawer to screenshot navigation
    page_m.locator("#bb8-hamburger-btn").click()
    page_m.wait_for_timeout(300)
    page_m.locator("#bb8-drawer").screenshot(path=str(ARTIFACT_DIR / "removal_drawer_390.png"))
    
    page_m.close()
    browser.close()

print("Verification screenshots captured successfully.")

