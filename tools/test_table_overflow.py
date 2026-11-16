import asyncio
from playwright.async_api import async_playwright

async def test_viewports():
    viewports = [1920, 1366, 1024, 768, 390]
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for w in viewports:
            page = await browser.new_page(viewport={'width': w, 'height': 900})
            await page.goto('http://127.0.0.1:5000/membership/', wait_until='networkidle')
            
            result = await page.evaluate('''() => {
                const errs = [];
                const rows = document.querySelectorAll('.bb-compare-table tr');
                rows.forEach((r, rowIdx) => {
                    const cells = r.querySelectorAll('th, td');
                    if (cells.length > 1) {
                        const feat = cells[0];
                        const plan1 = cells[1];
                        const featRect = feat.getBoundingClientRect();
                        const plan1Rect = plan1.getBoundingClientRect();
                        
                        // Check all children of feat
                        const children = feat.querySelectorAll('*');
                        children.forEach(ch => {
                            const chRect = ch.getBoundingClientRect();
                            if (chRect.right > plan1Rect.left + 1) {
                                errs.push(`Row ${rowIdx} <${ch.className}> overlaps next col: childRight=${chRect.right.toFixed(1)}, nextColLeft=${plan1Rect.left.toFixed(1)}`);
                            }
                            if (ch.scrollWidth > ch.clientWidth + 1) {
                                errs.push(`Row ${rowIdx} <${ch.className}> scrollWidth=${ch.scrollWidth} > clientWidth=${ch.clientWidth}`);
                            }
                        });
                    }
                });
                const table = document.querySelector('.bb-compare-table');
                const featCol = document.querySelector('.bb-col-feature');
                return {
                    errors: errs,
                    tableWidth: table ? table.offsetWidth : 0,
                    featWidth: featCol ? featCol.offsetWidth : 0,
                };
            }''')
            print(f"Viewport {w}px: tableWidth={result['tableWidth']}px, featWidth={result['featWidth']}px, errors={len(result['errors'])}")
            for e in result['errors']:
                print(f"   [FAIL] {e}")
            await browser.close()
            browser = await p.chromium.launch()

asyncio.run(test_viewports())

