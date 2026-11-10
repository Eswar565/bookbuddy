import sqlite3

for db_name in ['book_buddy_dev.sqlite3', 'book_buddy.sqlite3']:
    conn = sqlite3.connect(f'instance/{db_name}')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        rows = cur.execute("SELECT * FROM cms_pages").fetchall()
        print(db_name, "cms_pages count:", len(rows))
        for r in rows:
            print("slug:", r['slug'], "title:", r['title'])
    except Exception as e:
        print("Error:", e)
