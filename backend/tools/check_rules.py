from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    page.goto("http://127.0.0.1:5001/admin/login/")
    page.fill('input[name="email"]', "admin@gmail.com")
    page.fill('input[name="password"]', "admin123")
    page.click('button[type="submit"]')
    page.wait_for_url("**/admin/**")
    page.goto("http://127.0.0.1:5001/admin/manage/home-sections/")
    
    rules = page.evaluate("""
        () => {
            const link = Array.from(document.querySelectorAll('a')).find(a => a.innerText.includes('Homepage content'));
            const matched = [];
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.selectorText && link.matches(rule.selectorText)) {
                            if (rule.style.backgroundColor) {
                                matched.push({
                                    sheet: sheet.href,
                                    selector: rule.selectorText,
                                    bg: rule.style.backgroundColor,
                                    important: rule.style.getPropertyPriority('background-color')
                                });
                            }
                        }
                    }
                } catch(e) {}
            }
            return matched;
        }
    """)
    for r in rules:
        print(r)
    browser.close()

