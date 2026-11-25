import sqlite3

dbs = ['instance/book_buddy_dev.sqlite3', 'instance/book_buddy.sqlite3']

for db_path in dbs:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO site_content (content_key, content_value) VALUES ('gallery_pill', 'Our Gallery')")
    cur.execute("INSERT OR IGNORE INTO site_content (content_key, content_value) VALUES ('gallery_heading', 'Capturing Moments, Creating Memories')")
    
    # Check if thumbnail_path column exists in gallery_items
    cur.execute("PRAGMA table_info(gallery_items)")
    cols = [c[1] for c in cur.fetchall()]
    if 'thumbnail_path' not in cols:
        cur.execute("ALTER TABLE gallery_items ADD COLUMN thumbnail_path TEXT DEFAULT ''")
        print(f"[{db_path}] Added thumbnail_path column to gallery_items")
        
    conn.commit()
    conn.close()
    print(f"[{db_path}] Seeded gallery_pill and gallery_heading")

