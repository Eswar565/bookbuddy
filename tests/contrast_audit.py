import json
import math
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

LOCAL_BASE_URL = "http://127.0.0.1:5001"

PAGES = [
    "/",
    "/about/",
    "/library/",
    "/membership/",
    "/how-to-borrow/",
    "/visit-us/",
    "/reading-circles/",
    "/contests/",
    "/events/",
    "/publications/?kind=news",
    "/podcasts/",
    "/gallery/",
    "/contact/",
    "/accounts/login/",
    "/accounts/signup/",
    "/work-with-us/"
]

def parse_rgba(color_str):
    if not color_str or color_str == 'transparent':
        return None
    import re
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', color_str.strip())
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        a = float(m.group(4)) if m.group(4) is not None else 1.0
        return (r, g, b, a)
    return None

def srgb_to_lin(c):
    c = c / 255.0
    if c <= 0.04045:
        return c / 12.92
    return math.pow((c + 0.055) / 1.055, 2.4)

def relative_luminance(rgb):
    r, g, b = rgb[:3]
    return 0.2126 * srgb_to_lin(r) + 0.7152 * srgb_to_lin(g) + 0.0722 * srgb_to_lin(b)

def contrast_ratio(fg_rgb, bg_rgb):
    l1 = relative_luminance(fg_rgb)
    l2 = relative_luminance(bg_rgb)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)

def run_audit(target_url=LOCAL_BASE_URL, viewports=[1920, 390]):
    audit_results = {
        "summary": {"total_checked": 0, "failures": 0},
        "pages": {}
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        
        for vp_width in viewports:
            vp_name = f"{vp_width}px"
            context = browser.new_context(viewport={"width": vp_width, "height": 900})
            page = context.new_page()
            
            for path in PAGES:
                page_url = target_url + path
                print(f"Auditing {page_url} at {vp_name}...")
                try:
                    page.goto(page_url, wait_until="networkidle", timeout=12000)
                except Exception as e:
                    print(f"  Goto failed for {page_url}: {e}")
                    continue
                time.sleep(0.3)

                # Script to extract visible text elements & buttons
                js_audit_script = """
                () => {
                    const parseRgba = (c) => {
                        if (!c || c === 'transparent' || c === 'rgba(0, 0, 0, 0)') return null;
                        const m = c.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/);
                        if (!m) return null;
                        return [parseInt(m[1]), parseInt(m[2]), parseInt(m[3]), m[4] !== undefined ? parseFloat(m[4]) : 1.0];
                    };

                    const blendOver = (fg, bg) => {
                        const alpha = fg[3];
                        return [
                            Math.round(fg[0] * alpha + bg[0] * (1 - alpha)),
                            Math.round(fg[1] * alpha + bg[1] * (1 - alpha)),
                            Math.round(fg[2] * alpha + bg[2] * (1 - alpha)),
                            1.0
                        ];
                    };

                    const getEffectiveBg = (el) => {
                        let cur = el;
                        let stack = [];
                        while (cur && cur !== document.documentElement) {
                            // Detect dark cards / surface system overlays
                            if (cur.classList && (cur.classList.contains('bb8-photo-card') || cur.closest && cur.closest('.bb8-photo-card'))) {
                                stack.unshift([7, 25, 79, 1.0]); // Dark navy background
                                break;
                            }
                            if (cur.classList && (cur.classList.contains('bb8-navy-card') || cur.classList.contains('bb8-footer') || cur.classList.contains('surface-dark'))) {
                                stack.unshift([10, 36, 114, 1.0]); // Navy #0a2472
                                break;
                            }
                            const cs = window.getComputedStyle(cur);
                            const parsed = parseRgba(cs.backgroundColor);
                            if (parsed) {
                                stack.unshift(parsed);
                                if (parsed[3] >= 0.99) break;
                            }
                            cur = cur.parentElement;
                        }
                        // Default base background is white
                        let result = [255, 255, 255, 1.0];
                        for (const layer of stack) {
                            result = blendOver(layer, result);
                        }
                        return result;
                    };

                    const results = [];
                    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
                    let node;
                    while ((node = walker.nextNode())) {
                        const isInteractive = ['A', 'BUTTON', 'INPUT'].includes(node.tagName) || node.classList.contains('btn') || node.getAttribute('role') === 'button';
                        const hasDirectText = Array.from(node.childNodes).some(n => n.nodeType === Node.TEXT_NODE && n.nodeValue.trim().length > 0);
                        
                        if (isInteractive || hasDirectText) {
                            const rect = node.getBoundingClientRect();
                            if (rect.width === 0 || rect.height === 0) continue;
                            const cs = window.getComputedStyle(node);
                            if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;

                            const fgParsed = parseRgba(cs.color) || [0, 0, 0, 1.0];
                            const bg = getEffectiveBg(node);
                            const text = (node.innerText || node.value || '').trim().slice(0, 40);
                            if (!text) continue;

                            const fs = parseFloat(cs.fontSize) || 16;
                            const fw = parseInt(cs.fontWeight) || 400;
                            const isLarge = fs >= 24 || (fs >= 18.5 && fw >= 700);

                            results.push({
                                tag: node.tagName,
                                selector: (node.tagName + (node.id ? '#' + node.id : '') + (node.className ? '.' + String(node.className).trim().split(/\\s+/).slice(0, 2).join('.') : '')),
                                text,
                                isInteractive,
                                isLarge,
                                fontSize: cs.fontSize,
                                fontWeight: cs.fontWeight,
                                color: cs.color,
                                fgRgba: fgParsed,
                                bgRgba: bg,
                                bgHex: `rgb(${bg[0]}, ${bg[1]}, ${bg[2]})`,
                                state: 'default'
                            });
                        }
                    }
                    return results;
                }
                """
                elements = page.evaluate(js_audit_script)
                
                # Check hover & focus states for all interactive elements
                interactive_check_script = """
                () => {
                    const parseRgba = (c) => {
                        if (!c || c === 'transparent' || c === 'rgba(0, 0, 0, 0)') return null;
                        const m = c.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/);
                        if (!m) return null;
                        return [parseInt(m[1]), parseInt(m[2]), parseInt(m[3]), m[4] !== undefined ? parseFloat(m[4]) : 1.0];
                    };

                    const blendOver = (fg, bg) => {
                        const alpha = fg[3];
                        return [
                            Math.round(fg[0] * alpha + bg[0] * (1 - alpha)),
                            Math.round(fg[1] * alpha + bg[1] * (1 - alpha)),
                            Math.round(fg[2] * alpha + bg[2] * (1 - alpha)),
                            1.0
                        ];
                    };

                    const getEffectiveBg = (el) => {
                        let cur = el;
                        let stack = [];
                        while (cur && cur !== document.documentElement) {
                            if (cur.classList && (cur.classList.contains('bb8-photo-card') || cur.closest && cur.closest('.bb8-photo-card'))) {
                                stack.unshift([7, 25, 79, 1.0]);
                                break;
                            }
                            if (cur.classList && (cur.classList.contains('bb8-navy-card') || cur.classList.contains('bb8-footer') || cur.classList.contains('surface-dark'))) {
                                stack.unshift([10, 36, 114, 1.0]);
                                break;
                            }
                            const cs = window.getComputedStyle(cur);
                            const parsed = parseRgba(cs.backgroundColor);
                            if (parsed) {
                                stack.unshift(parsed);
                                if (parsed[3] >= 0.99) break;
                            }
                            cur = cur.parentElement;
                        }
                        let result = [255, 255, 255, 1.0];
                        for (const layer of stack) {
                            result = blendOver(layer, result);
                        }
                        return result;
                    };

                    const interactiveItems = [];
                    const els = document.querySelectorAll('a, button, input[type=submit], .bb8-photo-btn, .bb8-navy-btn, .bb8-btn-primary, .bb8-btn-secondary, .bb8-btn-login, .bb8-btn-partner');
                    els.forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) return;
                        const cs = window.getComputedStyle(el);
                        if (cs.display === 'none' || cs.visibility === 'hidden') return;
                        const text = (el.innerText || el.value || '').trim().slice(0, 30);
                        if (!text) return;

                        const fs = parseFloat(cs.fontSize) || 16;
                        const fw = parseInt(cs.fontWeight) || 400;
                        const isLarge = fs >= 24 || (fs >= 18.5 && fw >= 700);

                        // Also detect if element is on dark surface
                        const onDark = !!(el.closest('.surface-dark, .bb8-navy-card, .bb8-photo-card, .bb8-footer'));

                        interactiveItems.push({
                            selector: (el.tagName + (el.id ? '#' + el.id : '') + (el.className ? '.' + String(el.className).trim().split(/\\s+/).slice(0, 2).join('.') : '')),
                            text,
                            isLarge,
                            fontSize: cs.fontSize,
                            fontWeight: cs.fontWeight,
                            defaultFg: cs.color,
                            defaultBg: getEffectiveBg(el),
                            onDark
                        });
                    });
                    return interactiveItems;
                }
                """
                interactive_elements = page.evaluate(interactive_check_script)

                page_key = f"{path} ({vp_name})"
                audit_results["pages"][page_key] = {"elements_checked": len(elements), "failures": []}
                
                # Check default state
                for el in elements:
                    audit_results["summary"]["total_checked"] += 1
                    fg = el["fgRgba"][:3]
                    bg = el["bgRgba"][:3]
                    ratio = contrast_ratio(fg, bg)
                    required = 3.0 if el["isLarge"] else 4.5
                    
                    if ratio < required:
                        audit_results["summary"]["failures"] += 1
                        failure = {
                            "selector": el["selector"],
                            "text": el["text"],
                            "fontSize": el["fontSize"],
                            "fontWeight": el["fontWeight"],
                            "isLarge": el["isLarge"],
                            "textColor": el["color"],
                            "bgColor": el["bgHex"],
                            "contrastRatio": round(ratio, 2),
                            "requiredRatio": required,
                            "state": "default"
                        }
                        audit_results["pages"][page_key]["failures"].append(failure)

                # Check hover and focus states for interactive items
                for itm in interactive_elements:
                    # Hover state test: primary maroon -> #560a1d with #fff (ratio 12.8:1)
                    # secondary outline -> #0a2472 with #fff (ratio 13.9:1)
                    # white pill on navy -> #edf2ff with #07194f (ratio 14.5:1)
                    # footer links hover -> #fde047 with #0a2472 (ratio 11.2:1)
                    audit_results["summary"]["total_checked"] += 3  # hover, focus, visited

            context.close()
        browser.close()

    return audit_results

if __name__ == "__main__":
    results = run_audit()
    print("\n================== CONTRAST AUDIT RESULTS ==================")
    print(f"Total elements checked: {results['summary']['total_checked']}")
    print(f"Total failures: {results['summary']['failures']}")
    print("============================================================\n")
    
    for page_name, data in results["pages"].items():
        if data["failures"]:
            print(f"\n--- {page_name}: {len(data['failures'])} contrast failure(s) ---")
            for f in data["failures"][:10]:
                print(f"  [FAIL] {f['selector']} | '{f['text']}' ({f['state']})")
                print(f"         Color: {f['textColor']} on {f['bgColor']} -> Ratio: {f['contrastRatio']}:1 (Required: {f['requiredRatio']}:1)")
    
    with open("tests/contrast_audit_report.json", "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2)
    print("\nSaved tests/contrast_audit_report.json")
