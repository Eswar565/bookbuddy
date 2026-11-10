from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    page.goto("http://127.0.0.1:5001/admin/login/")
    page.fill('input[name="email"]', "admin@gmail.com")
    page.fill('input[name="password"]', "admin123")
    page.click('button[type="submit"]')
    page.wait_for_url("**/admin/**")
    
    info = page.evaluate("""
        () => {
            const el = document.querySelector('.s29-nav-main');
            const style = window.getComputedStyle(el);
            let bg = style.backgroundColor;
            let parent = el.parentElement;
            while ((!bg || bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') && parent) {
                bg = window.getComputedStyle(parent).backgroundColor;
                parent = parent.parentElement;
            }
            return {
                text: el.innerText,
                color: style.color,
                bg: bg,
                sidebarBg: window.getComputedStyle(document.querySelector('.sidebar')).backgroundColor
            };
        }
    """)
    print(info)
    browser.close()

