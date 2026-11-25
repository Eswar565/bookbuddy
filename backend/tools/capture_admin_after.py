import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = Path(r"C:\Users\Eswar\.gemini\antigravity\brain\8987ac8c-1fef-4599-b5b9-515703e201de")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

pages_to_capture = [
    ("dashboard", "http://127.0.0.1:5001/admin/dashboard/"),
    ("home_sections_list", "http://127.0.0.1:5001/admin/manage/home-sections/"),
    ("home_sections_edit", "http://127.0.0.1:5001/admin/manage/home-sections/1/"),
    ("books_list", "http://127.0.0.1:5001/admin/manage/books/"),
    ("event_form", "http://127.0.0.1:5001/admin/manage/events/0/"),
    ("users_list", "http://127.0.0.1:5001/admin/manage/members/"),
    ("notifications", "http://127.0.0.1:5001/admin/notifications/"),
    ("about_editor", "http://127.0.0.1:5001/admin/about-editor/"),
    ("settings", "http://127.0.0.1:5001/admin/settings/"),
    ("navigation_list", "http://127.0.0.1:5001/admin/manage/navigation/"),
    ("partners_list", "http://127.0.0.1:5001/admin/manage/partners/"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    
    # 1. Desktop 1920
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    
    # Log in
    page.goto("http://127.0.0.1:5001/admin/login/")
    page.fill('input[name="email"]', "admin@gmail.com")
    page.fill('input[name="password"]', "admin123")
    page.click('button[type="submit"]')
    page.wait_for_url("**/admin/**")
    print("Logged in successfully on desktop.")
    
    for name, url in pages_to_capture:
        try:
            page.goto(url, wait_until="networkidle")
            page.screenshot(path=str(ARTIFACT_DIR / f"admin_after_{name}_1920.png"), full_page=True)
            print(f"Captured after_{name}_1920")
        except Exception as e:
            print(f"Error capturing {name} 1920: {e}")
            
    context.close()
    
    # 2. Mobile 390
    context_m = browser.new_context(viewport={"width": 390, "height": 844})
    page_m = context_m.new_page()
    page_m.goto("http://127.0.0.1:5001/admin/login/")
    page_m.fill('input[name="email"]', "admin@gmail.com")
    page_m.fill('input[name="password"]', "admin123")
    page_m.click('button[type="submit"]')
    page_m.wait_for_url("**/admin/**")
    print("Logged in successfully on mobile.")
    
    for name, url in pages_to_capture:
        try:
            page_m.goto(url, wait_until="networkidle")
            page_m.screenshot(path=str(ARTIFACT_DIR / f"admin_after_{name}_390.png"), full_page=True)
            print(f"Captured after_{name}_390")
        except Exception as e:
            print(f"Error capturing {name} 390: {e}")
            
    context_m.close()
    browser.close()

print("All after screenshots captured successfully.")

