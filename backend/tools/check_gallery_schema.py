import sqlite3

for db in ['book_buddy_dev.sqlite3', 'book_buddy.sqlite3']:
    conn = sqlite3.connect(f'instance/{db}')
    row = conn.execute("SELECT sql FROM sqlite_master WHERE name='gallery_items'").fetchone()
    print(db, ":", row[0])
