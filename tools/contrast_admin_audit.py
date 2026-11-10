import math
from playwright.sync_api import sync_playwright

def parse_rgba(rgba_str):
    if not rgba_str: return (0, 0, 0, 1.0)
    import re
    m = re.search(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d\.]+))?', rgba_str)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        a = float(m.group(4)) if m.group(4) is not None else 1.0
        return (r, g, b, a)
    return (0, 0, 0, 1.0)

def composite(fg_rgba, bg_rgb):
    # fg over bg
    r1, g1, b1, a = fg_rgba
    r2, g2, b2 = bg_rgb
    r = int(r1 * a + r2 * (1 - a))
    g = int(g1 * a + g2 * (1 - a))
    b = int(b1 * a + b2 * (1 - a))
    return (r, g, b)

def luminance(r, g, b):
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

def contrast_ratio(rgb1, rgb2):
    l1 = luminance(*rgb1)
    l2 = luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

PAGES = [
    ("Dashboard", "http://127.0.0.1:5001/admin/dashboard/"),
    ("Home Sections", "http://127.0.0.1:5001/admin/manage/home-sections/"),
    ("About Editor", "http://127.0.0.1:5001/admin/about-editor/"),
    ("Library Center", "http://127.0.0.1:5001/admin/library-center/"),
    ("Notifications", "http://127.0.0.1:5001/admin/notifications/"),
    ("Partners", "http://127.0.0.1:5001/admin/manage/partners/"),
    ("Settings", "http://127.0.0.1:5001/admin/settings/"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    # Login
    page.goto("http://127.0.0.1:5001/admin/login/")
    page.fill('input[name="email"]', "admin@gmail.com")
    page.fill('input[name="password"]', "admin123")
    page.click('button[type="submit"]')
    page.wait_for_url("**/admin/**")
    
    total_elements = 0
    failures = []
    
    for label, url in PAGES:
        page.goto(url, wait_until="networkidle")
        elements = page.evaluate("""
            () => {
                const results = [];
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
                while (walker.nextNode()) {
                    const el = walker.currentNode;
                    if (['SCRIPT', 'STYLE', 'SVG', 'PATH', 'NOSCRIPT'].includes(el.tagName)) continue;
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
                    
                    const text = el.innerText ? el.innerText.trim() : '';
                    if (!text || text.length === 0) continue;
                    
                    // Trace backgrounds up the tree
                    const bgStack = [];
                    let cur = el;
                    while (cur) {
                        const bg = window.getComputedStyle(cur).backgroundColor;
                        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                            bgStack.push(bg);
                        }
                        cur = cur.parentElement;
                    }
                    bgStack.push('rgb(245, 246, 250)'); // root tint fallback
                    
                    results.push({
                        tag: el.tagName,
                        text: text.slice(0, 30),
                        color: style.color,
                        bgStack: bgStack,
                        fontSize: parseFloat(style.fontSize),
                        fontWeight: style.fontWeight
                    });
                }
                return results;
            }
        """)
        
        for item in elements:
            total_elements += 1
            fg_rgba = parse_rgba(item['color'])
            
            # Composite background from bottom of stack up to top
            current_bg = (245, 246, 250)
            for bg_str in reversed(item['bgStack']):
                rgba = parse_rgba(bg_str)
                current_bg = composite(rgba, current_bg)
                
            actual_fg = composite(fg_rgba, current_bg)
            ratio = contrast_ratio(actual_fg, current_bg)
            
            is_large = item['fontSize'] >= 18 or (item['fontSize'] >= 14 and int(item['fontWeight'] if item['fontWeight'].isdigit() else 400) >= 700)
            threshold = 3.0 if is_large else 4.5
            
            if ratio < threshold:
                failures.append({
                    "page": label,
                    "tag": item['tag'],
                    "text": item['text'],
                    "color": item['color'],
                    "effectiveBg": f"rgb{current_bg}",
                    "ratio": round(ratio, 2),
                    "threshold": threshold,
                    "fontSize": item['fontSize']
                })
                
    browser.close()
    
    print(f"Audited {total_elements} elements across {len(PAGES)} admin pages.")
    if failures:
        print(f"Found {len(failures)} contrast failures:")
        for f in failures[:10]:
            print(f"  [{f['page']}] <{f['tag']}> '{f['text']}': ratio {f['ratio']}:1 (min {f['threshold']}:1)")
    else:
        print("PERFECT: Zero contrast failures across all tested admin elements (WCAG AA pass)!")
