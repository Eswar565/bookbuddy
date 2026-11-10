from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = ctx.new_page()
    page.on("console", lambda msg: print(f"BROWSER LOG: {msg.text}"))
    page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
    page.goto("http://127.0.0.1:5001/newspaper/", wait_until="networkidle")
    
    # Check if script is loaded
    scripts = page.locator("script").all()
    print("Scripts count:", len(scripts))
    for s in scripts:
        src = s.get_attribute("src")
        if src and "bb-media" in src:
            print("Found bb-media script:", src)
            
    btn = page.locator(".bb-newspaper-card .bb-btn-outline").first
    print("Button text:", btn.inner_text())
    print("Button attributes:", btn.get_attribute("data-bb-share"), btn.get_attribute("data-share-url"))
    btn.click()
    page.wait_for_timeout(1000)
    toast = page.locator("#bb-toast")
    print("Toast element count:", toast.count())
    if toast.count() > 0:
        print("Toast class:", toast.get_attribute("class"))
        print("Toast text:", toast.inner_text())
        
    ctx.close()
    browser.close()

