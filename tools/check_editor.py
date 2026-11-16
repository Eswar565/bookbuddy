import asyncio
from playwright.async_api import async_playwright

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        # Log in
        await page.goto('http://127.0.0.1:5000/admin/login/')
        await page.fill('input[name="email"]', 'admin@example.com')
        await page.fill('input[name="password"]', 'AdminPass123!')
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('domcontentloaded')
        print('After login URL:', page.url)
        
        # Visit editor
        resp = await page.goto('http://127.0.0.1:5000/admin/visit-us-editor/')
        await page.wait_for_load_state('domcontentloaded')
        print('Editor URL:', page.url, 'status:', resp.status)
        content = await page.content()
        print('Title:', await page.title())
        print('Content length:', len(content))
        if resp.status != 200 or 'Visit Us' not in content:
            print('Body snippet:\n', content[:600])
        await browser.close()

asyncio.run(check())

