import sqlite3

con = sqlite3.connect("instance/book_buddy_dev.sqlite3")
cur = con.execute("SELECT * FROM homepage_sections")
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
print("homepage_sections columns:", cols)
for r in rows:
    d = dict(zip(cols, r))
    print("Section:", d.get("id"), d.get("section_key"), "| Title:", d.get("title"), "| Image:", d.get("image_path"))

