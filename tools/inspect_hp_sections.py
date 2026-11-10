import sqlite3

for db_path in ["instance/book_buddy_dev.sqlite3", "instance/book_buddy.sqlite3"]:
    print(f"\n=== {db_path} ===")
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM homepage_sections ORDER BY position, id").fetchall()
    for r in rows:
        d = dict(r)
        print(f"ID: {d['id']:2d} | pos: {d.get('position', 0):2d} | key: {d['section_key']:12s} | active: {d['is_active']} | title: {d['title']}")
        print(f"      kicker: {d.get('kicker')} | highlight: {d.get('highlight')}")
        print(f"      btn1: {d.get('button_label')} -> {d.get('url')} | btn2: {d.get('button2_label')} -> {d.get('button2_url')}")
        print(f"      img: {d.get('image_path')} | alt: {d.get('image_alt')}")

