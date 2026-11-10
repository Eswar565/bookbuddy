import os, sqlite3

img_rel = 'media/admin/team/cb6661487f1d9aa03e64561748f739.webp'
print('File exists on disk:', os.path.exists(img_rel))

for db_path in ['instance/book_buddy_dev.sqlite3', 'instance/book_buddy.sqlite3']:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    refs = []
    for t in tables:
        if t == 'team_members': continue
        cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t})").fetchall()]
        for c in cols:
            try:
                matches = cur.execute(f"SELECT COUNT(*) FROM {t} WHERE {c} LIKE ?", ('%cb6661487f1d9aa03e64561748f739%',)).fetchone()[0]
                if matches > 0:
                    refs.append((t, c, matches))
            except Exception:
                pass
    print(db_path, 'other references:', refs)

