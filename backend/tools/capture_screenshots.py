import asyncio
import os
from playwright.async_api import async_playwright

output_dir = r"C:\Users\Eswar\.gemini\antigravity\brain\8987ac8c-1fef-4599-b5b9-515703e201de"
base_url = "http://127.0.0.1:5001"

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome")
        
        # Desktop 1920x1080
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(base_url, wait_until="networkidle")
        
        # 1. Publications section 1920
        pub_sec = page.locator("#publications")
        await pub_sec.screenshot(path=os.path.join(output_dir, "publications_1920.png"))
        
        # 2. Spacing between Publications and Reviews 1920
        await page.evaluate("window.scrollTo(0, document.querySelector('#publications').offsetTop - 50)")
        await asyncio.sleep(0.5)
        await page.screenshot(path=os.path.join(output_dir, "section_spacing_1920.png"))
        
        # 3. Footer 1920
        footer = page.locator("footer.bb8-footer")
        await footer.screenshot(path=os.path.join(output_dir, "footer_1920.png"))
        
        # Full homepage 1920
        await page.screenshot(path=os.path.join(output_dir, "homepage_clean_1920.png"), full_page=True)
        
        # Mobile 390x844
        page_m = await browser.new_page(viewport={"width": 390, "height": 844})
        await page_m.goto(base_url, wait_until="networkidle")
        
        # 1. Publications section 390
        pub_sec_m = page_m.locator("#publications")
        await pub_sec_m.screenshot(path=os.path.join(output_dir, "publications_390.png"))
        
        # 2. Section spacing 390
        await page_m.evaluate("window.scrollTo(0, document.querySelector('#publications').offsetTop - 20)")
        await asyncio.sleep(0.5)
        await page_m.screenshot(path=os.path.join(output_dir, "section_spacing_390.png"))
        
        # 3. Footer 390
        footer_m = page_m.locator("footer.bb8-footer")
        await footer_m.screenshot(path=os.path.join(output_dir, "footer_390.png"))
        
        # Admin screenshots - login with admin@gmail.com / admin123
        await page.goto(f"{base_url}/admin/login/")
        await page.fill("#email", "admin@gmail.com")
        await page.fill("#password", "admin123")
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle")
        
        # Admin dashboard with logo
        await page.goto(f"{base_url}/admin/dashboard/", wait_until="networkidle")
        await page.screenshot(path=os.path.join(output_dir, "admin_logo_fixed_1920.png"))
        
        # Admin home-sections list
        await page.goto(f"{base_url}/admin/manage/home-sections/", wait_until="networkidle")
        await page.screenshot(path=os.path.join(output_dir, "admin_sections_list_1920.png"))
        
        await browser.close()
        print("Admin screenshots captured successfully!")

asyncio.run(capture())
