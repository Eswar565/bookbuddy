import sqlite3
import sys

target = sys.argv[1] if len(sys.argv) > 1 else "instance/book_buddy_demo.sqlite3"
con = sqlite3.connect(target)
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
print(f"Tables in database '{target}' ({len(tables)}):")
for t in tables:
    cnt = con.execute(f"SELECT count(*) FROM \"{t}\"").fetchone()[0]
    if cnt > 0:
        print(f"  {t}: {cnt} rows")
con.close()
