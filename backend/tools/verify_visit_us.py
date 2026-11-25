import asyncio
import json
import os
from urllib.parse import unquote
from playwright.async_api import async_playwright

BRAIN_DIR = r"C:\Users\Eswar\.gemini\antigravity\brain\55804cdc-1d82-42cb-b917-b8bdc6583efd"
BASE_URL = "http://127.0.0.1:5000"

async def verify_all():
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # ====================================================================
        # 1. Capture Screenshots and Measure Geometry at 1920, 1366, 768, 390
        # ====================================================================
        print("=== Step 1: Capturing Screenshots & Measuring Geometry ===")
        viewports = [1920, 1366, 768, 390]
        geom_results = {}
        for w in viewports:
            page = await browser.new_page(viewport={'width': w, 'height': 1080})
            await page.goto(f"{BASE_URL}/visit-us/", wait_until='domcontentloaded')
            await page.wait_for_timeout(1000)
            
            # Save screenshot
            ss_path = os.path.join(BRAIN_DIR, f"visit_us_build_{w}.png")
            await page.screenshot(path=ss_path, full_page=True)
            print(f"Captured {w}px screenshot -> {ss_path}")
            
            # Geometry check
            meas = await page.evaluate('''() => {
                const container = document.querySelector('.bb-visit-container');
                const cRect = container ? container.getBoundingClientRect() : null;
                const winWidth = window.innerWidth;
                const leftMargin = cRect ? cRect.left : 0;
                const rightMargin = cRect ? (winWidth - cRect.right) : 0;
                
                const contactCol = document.querySelector('.bb-visit-contact-col');
                const mapCol = document.querySelector('.bb-visit-map-col');
                const contactRect = contactCol ? contactCol.getBoundingClientRect() : null;
                const mapRect = mapCol ? mapCol.getBoundingClientRect() : null;
                
                const cards = Array.from(document.querySelectorAll('.bb-visit-card'));
                const cardWidths = cards.map(c => c.getBoundingClientRect().width);
                
                const hasHScroll = document.documentElement.scrollWidth > window.innerWidth;
                
                return {
                    winWidth,
                    leftMargin,
                    rightMargin,
                    marginDiff: Math.abs(leftMargin - rightMargin),
                    contactTop: contactRect ? contactRect.top : 0,
                    mapTop: mapRect ? mapRect.top : 0,
                    topAlignDiff: contactRect && mapRect ? Math.abs(contactRect.top - mapRect.top) : 0,
                    contactHeight: contactRect ? contactRect.height : 0,
                    mapHeight: mapRect ? mapRect.height : 0,
                    heightDiff: contactRect && mapRect ? Math.abs(contactRect.height - mapRect.height) : 0,
                    cardWidths,
                    hasHScroll
                };
            }''')
            geom_results[w] = meas
            print(f"[{w}px] Margins: L={meas['leftMargin']:.1f}, R={meas['rightMargin']:.1f} (diff={meas['marginDiff']:.1f}px)")
            if w > 900:
                print(f"[{w}px] Desktop Columns: topDiff={meas['topAlignDiff']:.1f}px, contactH={meas['contactHeight']:.1f}px, mapH={meas['mapHeight']:.1f}px (hDiff={meas['heightDiff']:.1f}px)")
            print(f"[{w}px] Horizontal scroll: {meas['hasHScroll']}")
            await page.close()
            
        results['geometry'] = geom_results

        # ====================================================================
        # 2. Text Extraction & Diff Against Specified Strings
        # ====================================================================
        print("\n=== Step 2: Text Verification ===")
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        await page.goto(f"{BASE_URL}/visit-us/", wait_until='domcontentloaded')
        await page.wait_for_timeout(600)
        
        page_texts = await page.evaluate('''() => {
            return {
                eyebrow: document.querySelector('.bb-visit-eyebrow')?.innerText.trim(),
                title: document.querySelector('.bb-visit-title')?.innerText.trim(),
                subtitle: document.querySelector('.bb-visit-subtitle')?.innerText.trim(),
                contactHeading: document.querySelector('#bb-visit-contact-heading')?.innerText.trim(),
                cardTitles: Array.from(document.querySelectorAll('.bb-visit-card-title')).map(el => el.innerText.trim()),
                address: document.querySelector('.bb-visit-address-val')?.innerText.trim(),
                phone: document.querySelector('a[href^="tel:"]')?.innerText.trim(),
                email: document.querySelector('a[href^="mailto:"]')?.innerText.trim(),
                directionsHelper: document.querySelector('.bb-visit-directions-helper')?.innerText.trim(),
                directionsBtn: document.querySelector('.bb-visit-directions-btn')?.innerText.trim(),
                tourEyebrow: document.querySelector('.bb-visit-tour-eyebrow')?.innerText.trim(),
                tourTitle: document.querySelector('.bb-visit-tour-title')?.innerText.trim(),
            };
        }''')
        
        print("Page extracted texts:")
        for k, v in page_texts.items():
            print(f"  {k}: {v}")
            
        assert page_texts['eyebrow'] == "GET IN TOUCH", f"Eyebrow mismatch: {page_texts['eyebrow']}"
        assert page_texts['title'] == "Plan Your Visit", f"Title mismatch: {page_texts['title']}"
        assert "Step into our library and explore a world of books" in page_texts['subtitle']
        assert page_texts['contactHeading'] == "Contact Details"
        assert "Our Library" in page_texts['cardTitles']
        assert "Phone / WhatsApp" in page_texts['cardTitles']
        assert "Email Us" in page_texts['cardTitles']
        assert "Get Directions" in page_texts['cardTitles']
        assert "Thiruvalluvar" in page_texts['address'] and "Saligramam" in page_texts['address']
        assert page_texts['directionsHelper'] == "Enter your starting location for exact routing."
        assert page_texts['directionsBtn'] == "Go"
        print("All visible texts match exact required strings!")
        results['texts'] = page_texts
        await page.close()

        # ====================================================================
        # 3. Test Get Directions in New Tab (with Input & Empty)
        # ====================================================================
        print("\n=== Step 3: Testing Get Directions Action ===")
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        await page.goto(f"{BASE_URL}/visit-us/", wait_until='domcontentloaded')
        await page.wait_for_timeout(600)
        
        # Test A: With input 'T Nagar, Chennai'
        async with page.expect_popup() as popup_info:
            await page.fill('#bb-directions-input', 'T Nagar, Chennai')
            await page.click('.bb-visit-directions-btn')
        popup_a = await popup_info.value
        url_a = popup_a.url
        print("Popup URL with 'T Nagar, Chennai':", url_a)
        assert "maps/dir/" in url_a
        assert "origin=T%20Nagar" in url_a or "origin=T+Nagar" in url_a or "origin=T%20Nagar%2C%20Chennai" in url_a
        assert "destination=" in url_a
        assert "travelmode=driving" in url_a
        await popup_a.close()
        
        # Test B: Empty input
        async with page.expect_popup() as popup_info:
            await page.fill('#bb-directions-input', '')
            await page.click('.bb-visit-directions-btn')
        popup_b = await popup_info.value
        url_b = popup_b.url
        print("Popup URL with empty input:", url_b)
        assert "maps/dir/" in url_b
        assert "origin=" not in url_b
        assert "destination=" in url_b
        await popup_b.close()
        await page.close()
        print("Get Directions actions verified!")

        # ====================================================================
        # 4. Admin Editor Flow & Unified Address Sync Across Pages
        # ====================================================================
        print("\n=== Step 4: Admin Editor Flow & Cross-Page Sync ===")
        context = await browser.new_context(viewport={'width': 1400, 'height': 900})
        page = await context.new_page()
        
        # Log in
        await page.goto(f"{BASE_URL}/admin/login/")
        await page.fill('input[name="email"]', 'admin@example.com')
        await page.fill('input[name="password"]', 'AdminPass123!')
        await page.click('button[type="submit"]')
        await page.wait_for_url('**/admin/dashboard/**')
        print("Logged in, current URL:", page.url)
        
        # Visit editor
        await page.goto(f"{BASE_URL}/admin/visit-us-editor/")
        await page.wait_for_load_state('domcontentloaded')
        await page.wait_for_timeout(500)
        content_ed = await page.content()
        assert "Visit Us Page Configuration" in content_ed, f"Heading missing, title: {await page.title()}"
        assert "Live Page Preview" in content_ed, "Live preview missing"
        print("Admin Visit Us editor loaded with live preview.")
        
        # Update address with a test marker, phone, email
        test_address = "1, Thiruvalluvar St, Thiru Nagar Colony, Gandhi Nagar,\nSaligramam, Chennai, Tamil Nadu 600093 (Gate 2)"
        test_phone = "+91 9080759399"
        test_email = "custom.visit@example.com"
        
        await page.fill('textarea[name="contact_address"]', test_address)
        await page.fill('input[name="contact_phone"]', test_phone)
        await page.fill('input[name="contact_email"]', test_email)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('domcontentloaded')
        await page.wait_for_timeout(500)
        print("Saved updated contact details in admin editor.")
        
        # Check 1: Visit Us page updated
        v_page = await context.new_page()
        await v_page.goto(f"{BASE_URL}/visit-us/")
        v_content = await v_page.content()
        assert "Gate 2" in v_content, "Visit Us page did not show updated address"
        assert test_phone in v_content, "Visit Us page did not show updated phone"
        assert test_email in v_content, "Visit Us page did not show updated email"
        print("Confirmed: Visit Us page updated with new address, phone and email.")
        
        # Check 2: Public Footer updated
        await v_page.goto(f"{BASE_URL}/")
        f_content = await v_page.content()
        assert "Gate 2" in f_content, "Footer did not show updated address"
        assert test_phone in f_content, "Footer did not show updated phone"
        assert test_email in f_content, "Footer did not show updated email"
        print("Confirmed: Public Footer updated with new address, phone and email.")
        
        # Check 3: Contact page updated
        await v_page.goto(f"{BASE_URL}/contact/")
        c_content = await v_page.content()
        assert "Gate 2" in c_content, "Contact page did not show updated address"
        assert test_phone in c_content, "Contact page did not show updated phone"
        assert test_email in c_content, "Contact page did not show updated email"
        print("Confirmed: Contact page updated with new address, phone and email.")
        
        # Revert back to clean address without (Gate 2)
        clean_address = "1, Thiruvalluvar St, Thiru Nagar Colony, Gandhi Nagar,\nSaligramam, Chennai, Tamil Nadu 600093"
        clean_phone = "+91 9080759312"
        clean_email = "bookbuddy.edu@gmail.com"
        await page.goto(f"{BASE_URL}/admin/visit-us-editor/")
        await page.fill('textarea[name="contact_address"]', clean_address)
        await page.fill('input[name="contact_phone"]', clean_phone)
        await page.fill('input[name="contact_email"]', clean_email)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('domcontentloaded')
        await page.wait_for_timeout(500)
        print("Reverted to clean official address in admin editor.")
        
        await v_page.close()
        await context.close()
        await browser.close()

asyncio.run(verify_all())
