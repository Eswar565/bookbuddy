import asyncio
import json
from playwright.async_api import async_playwright

async def inspect_reference():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        try:
            print("Navigating to https://book-buddy.in/visit-us/ ...")
            await page.goto('https://book-buddy.in/visit-us/', wait_until='networkidle', timeout=30000)
        except Exception as e:
            print(f"Navigation error: {e}")
            try:
                await page.goto('https://book-buddy.in/visit-us/', wait_until='domcontentloaded', timeout=30000)
            except Exception as e2:
                print(f"Fallback error: {e2}")
        
        # Take full page screenshot
        await page.screenshot(path=r'C:\Users\Eswar\.gemini\antigravity\brain\55804cdc-1d82-42cb-b917-b8bdc6583efd\reference_visit_us_1920.png', full_page=True)
        print("Captured full page screenshot to reference_visit_us_1920.png")
        
        # Extract structure and all sections
        info = await page.evaluate('''() => {
            const sections = [];
            // find main content
            const main = document.querySelector('main') || document.body;
            
            // Look for headings and section tags
            const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4'));
            const headingList = headings.map(h => ({
                tag: h.tagName,
                text: h.innerText.trim(),
                className: h.className,
                parentTag: h.parentElement ? h.parentElement.tagName : null,
                parentClass: h.parentElement ? h.parentElement.className : null
            }));
            
            // Check library tour specifically
            const tourElements = Array.from(document.querySelectorAll('*')).filter(el => 
                (el.innerText && el.innerText.toLowerCase().includes('library tour')) ||
                (el.className && typeof el.className === 'string' && el.className.toLowerCase().includes('tour'))
            );
            const tourDetails = tourElements.map(el => ({
                tag: el.tagName,
                className: el.className,
                text: el.innerText ? el.innerText.slice(0, 200) : '',
                html: el.outerHTML.slice(0, 300)
            }));
            
            // Extract all direct children of main
            const mainChildren = Array.from(main.children).map(c => ({
                tag: c.tagName,
                className: c.className,
                id: c.id,
                text: c.innerText ? c.innerText.slice(0, 150) : ''
            }));
            
            return {
                title: document.title,
                headingList,
                tourDetails,
                mainChildren
            };
        }''')
        
        with open(r'C:\Users\Eswar\.gemini\antigravity\brain\55804cdc-1d82-42cb-b917-b8bdc6583efd\reference_visit_us_info.json', 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2)
            
        print("Page Title:", info['title'])
        print("\nHeadings found:")
        for h in info['headingList']:
            print(f"  <{h['tag']}> {h['text']} (class: {h['className']})")
            
        print("\nMain children:")
        for mc in info['mainChildren']:
            print(f"  <{mc['tag']} class='{mc['className']}'>: {mc['text'].replace(chr(10), ' ')[:80]}")
            
        print("\nTour details:")
        for td in info['tourDetails']:
            print(f"  <{td['tag']} class='{td['className']}'>: {td['text'].replace(chr(10), ' ')[:100]}")
            
        await browser.close()

asyncio.run(inspect_reference())

