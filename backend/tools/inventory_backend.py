import sqlite3
import re

conn = sqlite3.connect('instance/book_buddy_dev.sqlite3')
cur = conn.cursor()

tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
mem_related = [t for t in tables if any(k in t.lower() for k in ['member', 'plan', 'sub', 'loan', 'lending', 'borrow'])]
pub_related = [t for t in tables if any(k in t.lower() for k in ['podcast', 'pub'])]

print("--- MEMBERSHIP / LENDING TABLES ---")
for t in mem_related:
    count = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t})").fetchall()]
    print(f"Table '{t}' ({count} rows): {', '.join(cols)}")

print("\n--- PUBLICATIONS / PODCAST TABLES ---")
for t in pub_related:
    count = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t})").fetchall()]
    print(f"Table '{t}' ({count} rows): {', '.join(cols)}")
    if t == 'publications':
        kinds = cur.execute("SELECT kind, count(*) FROM publications GROUP BY kind").fetchall()
        print("  Publication kinds:", kinds)

# Triggers related to membership or notifications
triggers = cur.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'").fetchall()
print("\n--- TRIGGERS ---")
for name, sql in triggers:
    if any(k in name.lower() for k in ['member', 'plan', 'notify', 'order']):
        print(f"Trigger {name}")

