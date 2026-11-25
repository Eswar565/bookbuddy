"""Playwright browser tests for Library Borrow Cart & Modal interactions."""

import pytest
from playwright.sync_api import sync_playwright

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE_URL = "http://127.0.0.1:5000/library/"


@pytest.fixture(scope="module")
def browser_context():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=EDGE_PATH, headless=True)
        yield browser
        browser.close()


def test_borrow_cart_full_acceptance_flow(browser_context):
    page = browser_context.new_page()
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: console_errors.append(str(exc)))

    try:
        # Start fresh with a logged-in user with plan (user_id=1, limit=2)
        page.goto(f"{BASE_URL}?test_user_id=1")
        page.evaluate("() => localStorage.removeItem('bb_cart')")
        page.reload()

        # Check unavailable books have no Add button
        unavail_pills = page.locator(".bb-avail-pill.is-unavailable")
        assert unavail_pills.count() > 0, "Expected at least one unavailable book pill"
        # Confirm that cards with is-unavailable pill have NO .btn-cart-add button
        for i in range(unavail_pills.count()):
            card = unavail_pills.nth(i).locator("xpath=ancestor::article[contains(@class, 'bb-book-card')]")
            assert card.locator("[data-add-to-cart]").count() == 0

        # Find available Add buttons
        add_btns = page.locator(".btn-cart-add.js-cart-btn")
        assert add_btns.count() >= 2, "Need at least 2 available books to test"

        btn1 = add_btns.nth(0)
        btn2 = add_btns.nth(1)

        title1 = btn1.get_attribute("data-title")
        title2 = btn2.get_attribute("data-title")
        assert title1, "Book 1 data-title attribute must not be empty"
        assert title2, "Book 2 data-title attribute must not be empty"

        # 1. Click Add on 2 books
        btn1.click()
        page.wait_for_timeout(300)
        assert btn1.locator(".cart-btn-label").text_content().strip() == "Added"
        assert btn1.get_attribute("aria-pressed") == "true"
        assert "is-in-cart" in (btn1.get_attribute("class") or "")

        badge = page.locator("#bb-filter-cart-badge")
        assert badge.is_visible()
        assert badge.text_content().strip() == "1"

        btn2.click()
        page.wait_for_timeout(300)
        assert btn2.locator(".cart-btn-label").text_content().strip() == "Added"
        assert btn2.get_attribute("aria-pressed") == "true"
        assert badge.text_content().strip() == "2"

        # 2. Open Checkout modal and verify both books listed
        checkout_btn = page.locator("#bb-filter-checkout-btn")
        checkout_btn.click()
        page.wait_for_timeout(300)

        modal = page.locator("#bb-checkout-modal")
        assert modal.is_visible()
        modal_items = modal.locator(".bb-modal-item")
        assert modal_items.count() == 2

        modal_text = modal.locator("#bb-modal-items-list").text_content()
        assert title1 in modal_text
        assert title2 in modal_text

        # 3. Reload the page -> state persists
        page.reload()
        page.wait_for_timeout(300)
        badge = page.locator("#bb-filter-cart-badge")
        assert badge.text_content().strip() == "2"

        # Buttons on reloaded page still show "Added"
        btn1 = page.locator(f"[data-add-to-cart][data-title='{title1}']")
        btn2 = page.locator(f"[data-add-to-cart][data-title='{title2}']")
        assert btn1.locator(".cart-btn-label").text_content().strip() == "Added"
        assert btn2.locator(".cart-btn-label").text_content().strip() == "Added"

        # 4. Navigate to page 2 of catalogue -> badge still shows 2
        page.goto(f"{BASE_URL}?page=2&test_user_id=1")
        page.wait_for_timeout(300)
        badge = page.locator("#bb-filter-cart-badge")
        assert badge.text_content().strip() == "2"

        # Open modal on page 2 and confirm both titles are listed
        page.locator("#bb-filter-checkout-btn").click()
        page.wait_for_timeout(300)
        modal_text_p2 = page.locator("#bb-modal-items-list").text_content()
        assert title1 in modal_text_p2
        assert title2 in modal_text_p2

        # 5. Click X in the modal -> the book is removed, badge becomes 1
        remove_btns = page.locator(".js-remove-modal-item")
        assert remove_btns.count() == 2
        remove_btns.first.click()
        page.wait_for_timeout(300)

        assert badge.text_content().strip() == "1"
        assert page.locator(".bb-modal-item").count() == 1

        # Close modal
        page.locator("#bb-modal-close-btn").click()
        page.wait_for_timeout(200)

        # Back to page 1
        page.goto(f"{BASE_URL}?test_user_id=1")
        page.wait_for_timeout(300)

        btn1 = page.locator(f"[data-add-to-cart][data-title='{title1}']")
        btn2 = page.locator(f"[data-add-to-cart][data-title='{title2}']")
        # First book returned to "Add", second book still shows "Added"
        assert btn1.locator(".cart-btn-label").text_content().strip() == "Add"
        assert btn1.get_attribute("aria-pressed") == "false"
        assert btn2.locator(".cart-btn-label").text_content().strip() == "Added"

        # 6. Click "Added" on card 2 -> book 2 is removed
        btn2.click()
        page.wait_for_timeout(300)
        assert btn2.locator(".cart-btn-label").text_content().strip() == "Add"
        assert badge.is_hidden() or badge.text_content().strip() == "0"
        cart_empty = page.evaluate("() => localStorage.getItem('bb_cart')")
        assert cart_empty in ("[]", None, "")

        # 7. Plan limit enforcement: Add 2 books (reaches limit of 2)
        btn1.click()
        page.wait_for_timeout(200)
        btn2.click()
        page.wait_for_timeout(200)
        assert badge.text_content().strip() == "2"

        # Try to add a 3rd book
        btn3 = add_btns.nth(2)
        btn3.click()
        page.wait_for_timeout(300)

        toast = page.locator("#bb-cart-toast")
        assert toast.is_visible()
        assert "allows 2 books" in toast.text_content()
        # 3rd book must NOT be added
        assert btn3.locator(".cart-btn-label").text_content().strip() == "Add"
        assert badge.text_content().strip() == "2"

        # 8. Verify no console errors occurred
        assert len(console_errors) == 0, f"Encountered console errors: {console_errors}"

    finally:
        page.close()
