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
    
    info = page.evaluate("""
        () => {
            const link = Array.from(document.querySelectorAll('a')).find(a => a.innerText.includes('Homepage content'));
            const style = window.getComputedStyle(link);
            return {
                text: link.innerText,
                color: style.color,
                bg: style.backgroundColor,
                parentBg: window.getComputedStyle(link.parentElement).backgroundColor,
                sidebarBg: window.getComputedStyle(document.querySelector('aside#admin-sidebar')).backgroundColor
            };
        }
    """)
    print('Home-sections link:', info)
    browser.close()

