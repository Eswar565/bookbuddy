import asyncio
from playwright.async_api import async_playwright

async def test_admin():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        # 1. Login as admin
        await page.goto('http://127.0.0.1:5000/admin/login/', wait_until='networkidle')
        await page.fill('input[name="email"]', 'admin@example.com')
        await page.fill('input[name="password"]', 'AdminPass123!')
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        
        print("Logged in, current URL:", page.url)
        assert '/admin/' in page.url
        
        # 2. Check /admin/dashboard/
        await page.goto('http://127.0.0.1:5000/admin/dashboard/', wait_until='networkidle')
        print("Dashboard URL:", page.url)
        title = await page.title()
        print("Dashboard Title:", title)
        
        content = await page.content()
        assert "500" not in title
        assert "Something went wrong" not in content
        assert "Your library administration workspace" in content or "Overview" in content
        
        # Save screenshot
        await page.screenshot(path=r'C:\Users\Eswar\.gemini\antigravity\brain\55804cdc-1d82-42cb-b917-b8bdc6583efd\admin_dashboard_verified.png')
        print("Admin dashboard verified and screenshot saved!")
        
        # 3. Test public navbar 'Dashboard' button
        await page.goto('http://127.0.0.1:5000/', wait_until='networkidle')
        dash_btn = await page.query_selector('.bb8-btn-login')
        if dash_btn:
            dash_text = await dash_btn.inner_text()
            print("Public navbar button text:", dash_text)
            await dash_btn.click()
            await page.wait_for_load_state('networkidle')
            print("After clicking Dashboard button URL:", page.url)
            assert '/admin/dashboard/' in page.url or '/admin/' in page.url
            print("Navbar Dashboard button successfully opened admin workspace!")
            
        await browser.close()

asyncio.run(test_admin())
