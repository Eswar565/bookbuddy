import sqlite3

conn = sqlite3.connect('instance/book_buddy.sqlite3')
cur = conn.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

keywords = [
    'game-hub', 'college-project', 'coding-kids', 'internship', 'skill module',
    'brain twister', 'sharpen your mind', 'innovation lab'
]

matches = []
for table in tables:
    try:
        cols = [c[1] for c in cur.execute(f"PRAGMA table_info({table})").fetchall()]
        for col in cols:
            for kw in keywords:
                q = f"SELECT rowid, {col} FROM {table} WHERE CAST({col} AS TEXT) LIKE ?"
                try:
                    res = cur.execute(q, (f"%{kw}%",)).fetchall()
                    if res:
                        matches.append((table, col, kw, len(res), res[:3]))
                except Exception:
                    pass
    except Exception as e:
        pass

print(f"Total table/col matches found: {len(matches)}")
for m in matches:
    print(m)
conn.close()

