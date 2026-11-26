from playwright.sync_api import sync_playwright
import os, sys

mode = sys.argv[1] if len(sys.argv) > 1 else "before"
target_url = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:5000/"

out_dir = "screenshots_footer"
os.makedirs(out_dir, exist_ok=True)

viewports = [
    (1920, 1080),
    (1366, 768),
    (768, 1024),
    (390, 844)
]

print(f"--- Measuring {mode} footer at {target_url} ---")
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    for w, h in viewports:
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(target_url, wait_until="networkidle")
        footer = page.locator("footer")
        box = footer.bounding_box()
        h_val = round(box["height"], 1) if box else 0
        print(f"Viewport {w}x{h}: footer height = {h_val}px")
        footer.screenshot(path=f"{out_dir}/{mode}_footer_{w}.png")
        page.screenshot(path=f"{out_dir}/{mode}_full_{w}.png", full_page=True)
        page.close()
    browser.close()
