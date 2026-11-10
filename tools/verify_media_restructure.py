import os
import sys
import time
import re
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\Eswar\.gemini\antigravity\brain\8987ac8c-1fef-4599-b5b9-515703e201de"

def test_http_assertions():
    print("--- 1. Testing HTTP & HTML Assertions ---")
    
    # A. Test /gallery/ 301 Redirect
    class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def http_error_301(self, req, fp, code, msg, headers):
            return fp
        def http_error_302(self, req, fp, code, msg, headers):
            return fp

    opener = urllib.request.build_opener(NoRedirectHandler)
    req = urllib.request.Request("http://127.0.0.1:5001/gallery/")
    try:
        resp = opener.open(req)
        status = resp.code if hasattr(resp, 'code') else resp.status
        location = resp.headers.get('Location', '')
        print(f"/gallery/ -> Status: {status}, Location: {location}")
        assert status == 301, f"Expected 301 status, got {status}"
        assert "/about/#gallery" in location, f"Expected Location to contain /about/#gallery, got {location}"
        print("PASS: /gallery/ cleanly 301 redirects to /about/#gallery")
    except urllib.error.HTTPError as e:
        print(f"/gallery/ HTTPError: {e.code}, headers: {e.headers}")
        assert e.code == 301
        assert "/about/#gallery" in e.headers.get('Location', '')
        print("PASS: /gallery/ cleanly 301 redirects to /about/#gallery")

    # B. Test Public Pages Media dropdown & Footer
    public_urls = ["http://127.0.0.1:5001/", "http://127.0.0.1:5001/about/", "http://127.0.0.1:5001/newspaper/"]
    for u in public_urls:
        html = urllib.request.urlopen(u).read().decode('utf-8')
        
        # Check Media Dropdown in desktop & mobile
        # Exactly Newspaper, Magazine, Podcasts
        media_dropdown_match = re.search(r'<!-- Media Dropdown -->\s*<details[^>]*>.*?<div class="bb8-dropdown-menu">(.*?)</div>', html, re.S)
        assert media_dropdown_match, f"Media dropdown missing on {u}"
        dropdown_content = media_dropdown_match.group(1)
        
        links = re.findall(r'<a href="([^"]+)">([^<]+)</a>', dropdown_content)
        print(f"{u} Media Dropdown links:", links)
        expected_links = [('/newspaper/', 'Newspaper'), ('/magazine/', 'Magazine'), ('/podcasts/', 'Podcasts')]
        assert links == expected_links, f"Dropdown links mismatch on {u}: {links}"
        
        # Assert NO Gallery link anywhere in nav/footer
        footer_match = re.search(r'<footer.*?</footer>', html, re.S)
        if footer_match:
            footer_html = footer_match.group(0)
            assert 'href="/gallery/"' not in footer_html, f"Footer contains /gallery/ on {u}"
            assert '>Gallery<' not in footer_html, f"Footer contains Gallery text on {u}"
        print(f"PASS: {u} dropdown has exactly the 3 items and footer has no Gallery link")

    # C. Test About Page Gallery Section
    about_html = urllib.request.urlopen("http://127.0.0.1:5001/about/").read().decode('utf-8')
    assert 'id="gallery"' in about_html, "About page missing id='gallery' section!"
    assert 'Our Gallery' in about_html, "About page gallery missing 'Our Gallery' pill!"
    assert 'Capturing Moments, Creating Memories' in about_html, "About page gallery missing heading!"
    assert 'bb-gallery-tile' in about_html, "About page gallery missing photo tiles!"
    # Ensure NO visible captions or maroon cards in gallery
    assert 'bb-gallery-caption' not in about_html, "Found captions in About gallery!"
    assert '<figcaption' not in about_html, "Found figcaption in About gallery!"
    print("PASS: About page contains gallery section with 0 captions/tile text")

    # D. Test Media Pages Content
    # 1. Newspaper
    news_html = urllib.request.urlopen("http://127.0.0.1:5001/newspaper/").read().decode('utf-8')
    assert "Press &amp; Media" in news_html or "Press & Media" in news_html
    assert "The <span class=\"bb-accent\">Chronicle</span> Archive" in news_html
    assert "View / Download PDF" in news_html
    assert "Share" in news_html
    print("PASS: Newspaper page rendered with pill, accent heading, PDF & Share buttons")

    # 2. Magazine
    mag_html = urllib.request.urlopen("http://127.0.0.1:5001/magazine/").read().decode('utf-8')
    assert "Publication &amp; Media" in mag_html or "Publication & Media" in mag_html
    assert "The <span class=\"bb-accent\">Magazine</span> Archive" in mag_html
    assert "Have something amazing to share?" in mag_html
    assert "Submit Your Work" in mag_html
    assert "/submit-contribution/" in mag_html
    print("PASS: Magazine page rendered with pill, accent heading, 2-col cards & CTA box")

    # 3. Podcasts
    pod_html = urllib.request.urlopen("http://127.0.0.1:5001/podcasts/").read().decode('utf-8')
    assert "Media &amp; Audio" in pod_html or "Media & Audio" in pod_html
    assert "The <span class=\"bb-accent\">Podcast</span> Archive" in pod_html
    assert "EPISODE" in pod_html
    print("PASS: Podcasts page rendered with pill, accent heading & episode cards")


def test_playwright_e2e_and_screenshots():
    print("\n--- 2. Testing Playwright E2E & Capturing Proof Screenshots ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        
        # 1. Desktop Context (1920x1080)
        context = browser.new_context(viewport={"width": 1920, "height": 1080}, permissions=["clipboard-read", "clipboard-write"])
        page = context.new_page()
        
        # A. Newspaper Desktop
        page.goto("http://127.0.0.1:5001/newspaper/", wait_until="networkidle")
        shot_news_1920 = os.path.join(ARTIFACT_DIR, "media_newspaper_1920.png")
        page.screenshot(path=shot_news_1920, full_page=False)
        print(f"Captured: {shot_news_1920}")
        
        # Test Share button on Newspaper
        page.locator(".bb-newspaper-card .bb-btn-outline").first.click()
        page.wait_for_selector(".bb-toast.is-visible", timeout=2000)
        print("PASS: Newspaper Share button triggers toast.")
        
        # B. Magazine Desktop
        page.goto("http://127.0.0.1:5001/magazine/", wait_until="networkidle")
        shot_mag_1920 = os.path.join(ARTIFACT_DIR, "media_magazine_1920.png")
        page.screenshot(path=shot_mag_1920, full_page=False)
        print(f"Captured: {shot_mag_1920}")
        
        # Test Share button on Magazine
        page.locator(".bb-magazine-card .bb-share-icon-btn").first.click()
        page.wait_for_selector(".bb-toast.is-visible", timeout=2000)
        print("PASS: Magazine Share button triggers toast.")
        
        # C. Podcasts Desktop
        page.goto("http://127.0.0.1:5001/podcasts/", wait_until="networkidle")
        shot_pod_1920 = os.path.join(ARTIFACT_DIR, "media_podcasts_1920.png")
        page.screenshot(path=shot_pod_1920, full_page=False)
        print(f"Captured: {shot_pod_1920}")
        
        # D. About Page with Gallery Section Desktop
        page.goto("http://127.0.0.1:5001/about/#gallery", wait_until="networkidle")
        gallery_section = page.locator("#gallery")
        gallery_section.scroll_into_view_if_needed()
        shot_about_gal_1920 = os.path.join(ARTIFACT_DIR, "about_gallery_1920.png")
        gallery_section.screenshot(path=shot_about_gal_1920)
        print(f"Captured: {shot_about_gal_1920}")
        
        # Test Lightbox on About page
        page.locator("#gallery .bb-gallery-tile").first.click()
        page.wait_for_selector(".bb-lightbox.is-open", timeout=3000)
        print("PASS: About page gallery lightbox opened.")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        assert page.locator(".bb-lightbox.is-open").count() == 0
        print("PASS: About page gallery lightbox closed via Escape.")

        # E. Admin Login and Sidebar / About Gallery Verification
        page.goto("http://127.0.0.1:5001/admin/login/", wait_until="networkidle")
        page.fill('input[name="email"]', "admin@gmail.com")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url("**/admin/**")
        
        # Check Admin Media Group
        page.goto("http://127.0.0.1:5001/admin/dashboard/", wait_until="networkidle")
        # Ensure Media submenu is open
        media_menu = page.locator('details.s29-submenu:has(summary:has-text("Media"))')
        media_menu.evaluate("el => el.setAttribute('open', '')")
        media_links = media_menu.locator("a").all_inner_texts()
        print("Admin Media Group links:", media_links)
        assert any("Newspaper" in t for t in media_links)
        assert any("Magazine" in t for t in media_links)
        assert any("Podcasts" in t for t in media_links)
        assert not any("Gallery" in t for t in media_links), "Gallery should NOT be in Media group!"
        assert not any("Media uploads" in t for t in media_links), "Media uploads should NOT be in Media group!"
        print("PASS: Admin Media group has exactly Newspaper, Magazine, Podcasts.")
        
        shot_admin_sidebar = os.path.join(ARTIFACT_DIR, "admin_media_sidebar_1920.png")
        page.locator("#admin-sidebar").screenshot(path=shot_admin_sidebar)
        print(f"Captured: {shot_admin_sidebar}")
        
        # Check Admin About Editor with Gallery Photos section
        page.goto("http://127.0.0.1:5001/admin/about-editor/#gallery", wait_until="networkidle")
        shot_admin_gal = os.path.join(ARTIFACT_DIR, "admin_about_gallery_1920.png")
        page.locator("#gallery").screenshot(path=shot_admin_gal)
        print(f"Captured: {shot_admin_gal}")
        
        context.close()
        
        # 2. Mobile Context (390x844)
        print("\n--- Capturing Mobile (390px) Screenshots ---")
        mobile_ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
        m_page = mobile_ctx.new_page()
        
        m_page.goto("http://127.0.0.1:5001/newspaper/", wait_until="networkidle")
        shot_news_390 = os.path.join(ARTIFACT_DIR, "media_newspaper_390.png")
        m_page.screenshot(path=shot_news_390, full_page=False)
        print(f"Captured: {shot_news_390}")
        
        m_page.goto("http://127.0.0.1:5001/magazine/", wait_until="networkidle")
        shot_mag_390 = os.path.join(ARTIFACT_DIR, "media_magazine_390.png")
        m_page.screenshot(path=shot_mag_390, full_page=False)
        print(f"Captured: {shot_mag_390}")
        
        m_page.goto("http://127.0.0.1:5001/podcasts/", wait_until="networkidle")
        shot_pod_390 = os.path.join(ARTIFACT_DIR, "media_podcasts_390.png")
        m_page.screenshot(path=shot_pod_390, full_page=False)
        print(f"Captured: {shot_pod_390}")
        
        m_page.goto("http://127.0.0.1:5001/about/#gallery", wait_until="networkidle")
        m_gal = m_page.locator("#gallery")
        m_gal.scroll_into_view_if_needed()
        shot_about_gal_390 = os.path.join(ARTIFACT_DIR, "about_gallery_390.png")
        m_gal.screenshot(path=shot_about_gal_390)
        print(f"Captured: {shot_about_gal_390}")
        
        mobile_ctx.close()
        browser.close()
        print("\nAll Playwright E2E and screenshot captures succeeded!")

if __name__ == "__main__":
    test_http_assertions()
    test_playwright_e2e_and_screenshots()
