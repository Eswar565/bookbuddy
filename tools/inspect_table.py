import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        await page.goto('http://127.0.0.1:5000/membership/', wait_until='networkidle')
        
        table = await page.query_selector('.bb-table-wrapper')
        if table:
            await table.screenshot(path=r'C:\Users\Eswar\.gemini\antigravity\brain\55804cdc-1d82-42cb-b917-b8bdc6583efd\current_table_1920.png')
            print('Saved screenshot to current_table_1920.png')
            
        rows = await page.query_selector_all('.bb-compare-table tr')
        for i, row in enumerate(rows):
            cells = await row.query_selector_all('th, td')
            texts = [await c.inner_text() for c in cells]
            boxes = [await c.bounding_box() for c in cells]
            parts = []
            for t, b in zip(texts, boxes):
                short = t.replace('\n', ' ')[:22]
                if b:
                    parts.append(f"[{short} x={b['x']:.0f} w={b['width']:.0f} r={b['x']+b['width']:.0f}]")
            print(f"Row {i}: " + " ".join(parts))
        
        # Check computed styles of bb-col-feature
        feat = await page.query_selector('.bb-col-feature')
        if feat:
            cs = await page.evaluate('(el) => { const s = window.getComputedStyle(el); return { width: s.width, whiteSpace: s.whiteSpace, overflowWrap: s.overflowWrap, minWidth: s.minWidth }; }', feat)
            print("bb-col-feature computed style:", cs)
            
        # Check title and sub computed style
        sub = await page.query_selector('.bb-row-sub')
        if sub:
            cs_sub = await page.evaluate('(el) => { const s = window.getComputedStyle(el); return { fontSize: s.fontSize, fontWeight: s.fontWeight, whiteSpace: s.whiteSpace, textTransform: s.textTransform }; }', sub)
            print("bb-row-sub computed style:", cs_sub)
            
        await browser.close()

asyncio.run(inspect())

