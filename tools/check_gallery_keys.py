import sqlite3

for p in ['instance/book_buddy_dev.sqlite3', 'instance/book_buddy.sqlite3']:
    conn = sqlite3.connect(p)
    cur = conn.cursor()
    rows = cur.execute("SELECT content_key, content_value FROM site_content WHERE content_key LIKE '%gallery%'").fetchall()
    print(p, "gallery keys:", rows)

