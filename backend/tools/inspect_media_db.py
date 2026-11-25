import sqlite3

conn = sqlite3.connect('instance/book_buddy_dev.sqlite3')
conn.row_factory = sqlite3.Row

print("--- site_navigation rows ---")
for r in conn.execute("SELECT * FROM site_navigation ORDER BY group_name, position").fetchall():
    print(dict(r))

print("\n--- publications rows ---")
for r in conn.execute("SELECT * FROM publications").fetchall():
    print(dict(r))

conn.close()
