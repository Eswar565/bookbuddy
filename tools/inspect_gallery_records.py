import os, sqlite3
from PIL import Image

conn = sqlite3.connect('instance/book_buddy_dev.sqlite3')
cur = conn.cursor()
rows = cur.execute('SELECT id, title, description, image_path, alt_text, position, is_active FROM gallery_items ORDER BY position, id').fetchall()

print(f"{'ID':<4} | {'Title':<24} | {'File Exists':<11} | {'Dimensions':<12} | {'Test Data Hint':<16} | {'Image Path'}")
print("-" * 100)

for r in rows:
    gid, title, desc, img_path, alt, pos, active = r
    fp = img_path.lstrip('/') if img_path else ""
    exists = os.path.exists(fp)
    dims = "N/A"
    is_test = False
    test_reasons = []
    
    if not exists:
        test_reasons.append("Missing File")
    if title.lower() in ['demo', 'demo1', 'test']:
        test_reasons.append(f"Title '{title}'")
    
    if exists:
        try:
            with Image.open(fp) as img:
                dims = f"{img.width}x{img.height}"
                # check if aspect ratio or content looks like screenshot
        except Exception as e:
            dims = "Corrupt"
            test_reasons.append("Corrupt Image")
            
    test_hint = ", ".join(test_reasons) if test_reasons else "Normal Photo"
    print(f"{gid:<4} | {title:<24} | {str(exists):<11} | {dims:<12} | {test_hint:<16} | {img_path}")

