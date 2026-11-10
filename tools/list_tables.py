import sqlite3

con = sqlite3.connect("instance/book_buddy_dev.sqlite3")
tables = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print([t[0] for t in tables])

