import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.goto('https://book-buddy.in/visit-us/', wait_until='networkidle')
    
    sections = page.evaluate('''() => {
        // Find sections between map and footer
        const results = [];
        
        // 1. Tour section
        const tour = document.querySelector('.gallery, [class*="tour"], [class*="glimpse"]') || 
                     Array.from(document.querySelectorAll('div, section')).find(el => el.innerText && el.innerText.includes('A Glimpse Inside Book Buddy'));
        if (tour) {
            results.push({
                name: "Library Tour / Glimpse",
                text: tour.innerText,
                images: Array.from(tour.querySelectorAll('img')).map(img => ({ src: img.src, alt: img.alt })),
                html: tour.outerHTML.slice(0, 500)
            });
        }
        
        // 2. Verified Ratings section
        const ratings = Array.from(document.querySelectorAll('div, section')).find(el => el.innerText && el.innerText.includes('Verified Ratings on Google Maps'));
        if (ratings) {
            results.push({
                name: "Verified Ratings",
                text: ratings.innerText.slice(0, 500),
                images: Array.from(ratings.querySelectorAll('img')).map(img => ({ src: img.src, alt: img.alt })),
                html: ratings.outerHTML.slice(0, 500)
            });
        }
        
        // 3. Testimonials section
        const testimonials = Array.from(document.querySelectorAll('div, section')).find(el => el.innerText && el.innerText.includes('What members Say About Us'));
        if (testimonials) {
            results.push({
                name: "Testimonials",
                text: testimonials.innerText.slice(0, 500),
                images: Array.from(testimonials.querySelectorAll('img')).map(img => ({ src: img.src, alt: img.alt })),
                html: testimonials.outerHTML.slice(0, 500)
            });
        }
        
        return results;
    }''')
    
    for s in sections:
        print("=== Section:", s['name'], "===")
        print("Text snippet:\n", s['text'][:400])
        print("Images count:", len(s['images']))
        for img in s['images'][:4]:
            print("  Image:", img)
            
    browser.close()

