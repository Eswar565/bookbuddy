import os
import sys
import time
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\Eswar\.gemini\antigravity\brain\8987ac8c-1fef-4599-b5b9-515703e201de"

def run_e2e():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        
        # 1. Desktop Test (1920x1080)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        print("Navigating to http://127.0.0.1:5001/gallery/ ...")
        page.goto("http://127.0.0.1:5001/gallery/", wait_until="networkidle")
        
        # Verify Pill & Heading
        pill = page.locator(".bb-gallery-pill").inner_text()
        heading = page.locator(".bb-gallery-heading").inner_text()
        print(f"Pill: '{pill}'")
        print(f"Heading: '{heading}'")
        assert "OUR GALLERY" in pill.upper(), f"Unexpected pill: {pill}"
        assert "Capturing Moments" in heading, f"Unexpected heading: {heading}"
        
        # Verify Tiles
        tiles = page.locator(".bb-gallery-tile")
        count = tiles.count()
        print(f"Rendered gallery tiles count: {count}")
        assert count >= 4, f"Expected at least 4 tiles, found {count}"
        
        # Verify no visible captions or maroon cards
        captions = page.locator("figcaption, .bb-gallery-caption, .gallery-caption")
        assert captions.count() == 0, "Found captions on public gallery page!"
        
        # Check computed styles of first tile
        first_tile = tiles.nth(0)
        tile_box = first_tile.bounding_box()
        print(f"Tile 1 dimensions: {tile_box['width']}x{tile_box['height']} (ratio: {tile_box['width']/tile_box['height']:.2f})")
        # 16/10 ratio is 1.6
        assert 1.5 <= (tile_box['width']/tile_box['height']) <= 1.7, "Tile is not 16:10 aspect ratio!"
        
        # Capture Desktop Screenshot
        desktop_shot = os.path.join(ARTIFACT_DIR, "gallery_desktop_1920.png")
        page.screenshot(path=desktop_shot, full_page=False)
        print(f"Saved desktop screenshot: {desktop_shot}")
        
        # Test Lightbox interaction
        print("Testing lightbox...")
        first_tile.click()
        page.wait_for_selector(".bb-lightbox.is-open", timeout=3000)
        print("Lightbox opened successfully.")
        
        counter = page.locator(".bb-lightbox-counter").inner_text()
        print(f"Lightbox counter: '{counter}'")
        assert "1 /" in counter, f"Unexpected counter: {counter}"
        
        # Capture Lightbox Screenshot
        lightbox_shot = os.path.join(ARTIFACT_DIR, "gallery_lightbox_1920.png")
        page.screenshot(path=lightbox_shot, full_page=False)
        print(f"Saved lightbox screenshot: {lightbox_shot}")
        
        # Click Next
        page.locator(".bb-lightbox-next").click()
        page.wait_for_timeout(300)
        counter2 = page.locator(".bb-lightbox-counter").inner_text()
        print(f"After next button, counter: '{counter2}'")
        assert "2 /" in counter2, f"Unexpected counter after next: {counter2}"
        
        # Test Escape to close
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        is_open = page.locator(".bb-lightbox.is-open").count()
        print(f"Lightbox open after Escape: {is_open == 1}")
        assert is_open == 0, "Lightbox did not close on Escape key!"
        
        context.close()
        
        # 2. Mobile Test (390x844)
        print("\nTesting mobile layout (390x844)...")
        mobile_context = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
        mobile_page = mobile_context.new_page()
        mobile_page.goto("http://127.0.0.1:5001/gallery/", wait_until="networkidle")
        
        mobile_shot = os.path.join(ARTIFACT_DIR, "gallery_mobile_390.png")
        mobile_page.screenshot(path=mobile_shot, full_page=False)
        print(f"Saved mobile screenshot: {mobile_shot}")
        
        mobile_tiles = mobile_page.locator(".bb-gallery-tile")
        print(f"Mobile tiles count: {mobile_tiles.count()}")
        
        mobile_context.close()
        
        # 3. Admin Gallery Manager Test
        print("\nTesting Admin Gallery Manager (/admin/manage/gallery/)...")
        admin_context = browser.new_context(viewport={"width": 1920, "height": 1080})
        admin_page = admin_context.new_page()
        
        # Login
        admin_page.goto("http://127.0.0.1:5001/admin/login/", wait_until="networkidle")
        admin_page.fill('input[name="email"]', "admin@gmail.com")
        admin_page.fill('input[name="password"]', "admin123")
        admin_page.click('button[type="submit"]')
        admin_page.wait_for_url("**/admin/**")
        print("Logged into admin successfully.")
        
        # Navigate to gallery manager
        admin_page.goto("http://127.0.0.1:5001/admin/manage/gallery/", wait_until="networkidle")
        
        # Check elements
        assert admin_page.locator('input[name="gallery_pill"]').count() == 1
        assert admin_page.locator('input[name="gallery_heading"]').count() == 1
        assert admin_page.locator('input[type="file"][multiple]').count() == 1
        print("Settings fields and multi-upload input present.")
        
        admin_shot = os.path.join(ARTIFACT_DIR, "gallery_admin_1920.png")
        admin_page.screenshot(path=admin_shot, full_page=False)
        print(f"Saved admin screenshot: {admin_shot}")
        
        # Navigate to single edit for item 2
        admin_page.goto("http://127.0.0.1:5001/admin/manage/gallery/2/", wait_until="networkidle")
        # Check that title & description inputs are NOT present
        assert admin_page.locator('input[name="title"]').count() == 0
        assert admin_page.locator('textarea[name="description"]').count() == 0
        assert admin_page.locator('input[name="description"]').count() == 0
        assert admin_page.locator('input[name="alt_text"]').count() == 1
        print("Verified single edit has no title/description and has alt_text.")
        
        admin_edit_shot = os.path.join(ARTIFACT_DIR, "gallery_admin_edit_1920.png")
        admin_page.screenshot(path=admin_edit_shot, full_page=False)
        print(f"Saved admin edit screenshot: {admin_edit_shot}")
        
        admin_context.close()
        browser.close()
        print("\nAll E2E checks passed successfully!")

if __name__ == "__main__":
    run_e2e()
