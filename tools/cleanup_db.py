import sqlite3

for path in ['instance/book_buddy.sqlite3', 'instance/book_buddy_dev.sqlite3']:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    # Delete challenges and innovation
    cur.execute("DELETE FROM homepage_sections WHERE section_key IN ('challenges', 'innovation')")
    # Clear hero button_label and url
    cur.execute("UPDATE homepage_sections SET button_label='', url='' WHERE section_key='hero'")
    conn.commit()
    print('Cleaned', path)
    rows = cur.execute('SELECT id, section_key, title, kicker, button_label, url FROM homepage_sections').fetchall()
    for r in rows:
        print('  ', r)
    conn.close()

