import sqlite3

for db in ['book_buddy_dev.sqlite3', 'book_buddy.sqlite3']:
    conn = sqlite3.connect(f'instance/{db}')
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM homepage_sections WHERE section_key='publications'").fetchone()
    if row:
        print(db, "Current publications row:", dict(row))
        conn.execute("UPDATE homepage_sections SET url='/newspaper/' WHERE section_key='publications'")
        conn.commit()
    conn.close()

