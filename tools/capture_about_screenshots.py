import asyncio
import os
from playwright.async_api import async_playwright

output_dir = r"C:\Users\Eswar\.gemini\antigravity\brain\8987ac8c-1fef-4599-b5b9-515703e201de"
base_url = "http://127.0.0.1:5001"

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome")
        
        # Desktop 1920x1080 - Public About Page
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(f"{base_url}/about/", wait_until="networkidle")
        await page.screenshot(path=os.path.join(output_dir, "about_page_1920.png"), full_page=True)
        
        # Mobile 390x844 - Public About Page
        page_m = await browser.new_page(viewport={"width": 390, "height": 844})
        await page_m.goto(f"{base_url}/about/", wait_until="networkidle")
        await page_m.screenshot(path=os.path.join(output_dir, "about_page_390.png"), full_page=True)
        
        # Desktop 1920x1080 - Admin About Editor
        admin_page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await admin_page.goto(f"{base_url}/admin/login/")
        await admin_page.fill("#email", "admin@gmail.com")
        await admin_page.fill("#password", "admin123")
        await admin_page.click("button[type='submit']")
        await admin_page.wait_for_load_state("networkidle")
        
        # Admin About Editor
        await admin_page.goto(f"{base_url}/admin/about-editor/", wait_until="networkidle")
        await admin_page.screenshot(path=os.path.join(output_dir, "admin_about_editor_1920.png"), full_page=True)
        
        # Admin Page Map
        await admin_page.goto(f"{base_url}/admin/page-map/", wait_until="networkidle")
        await admin_page.screenshot(path=os.path.join(output_dir, "admin_page_map_1920.png"), full_page=True)
        
        await browser.close()
        print("About screenshots captured successfully!")

asyncio.run(capture())

