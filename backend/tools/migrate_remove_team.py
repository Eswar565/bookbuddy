import sqlite3
import os

dbs = ['instance/book_buddy_dev.sqlite3', 'instance/book_buddy.sqlite3']

print("=== Running Migration: Remove Team ===")

for db_path in dbs:
    if not os.path.exists(db_path):
        continue
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check site_content for team_heading
    cur.execute("DELETE FROM site_content WHERE content_key IN ('team_heading', 'team_members')")
    deleted_content = cur.rowcount
    
    # Check if team_members table exists
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    table_dropped = False
    if 'team_members' in tables:
        cur.execute("DROP TABLE team_members")
        table_dropped = True
        
    conn.commit()
    conn.close()
    print(f"[{db_path}] Deleted site_content rows: {deleted_content}, Dropped team_members table: {table_dropped}")

# Delete unreferenced team photo
photo_path = os.path.join('media', 'admin', 'team', 'cb6661487f1d9aa03e64561748f739.webp')
if os.path.exists(photo_path):
    os.remove(photo_path)
    print(f"Deleted unreferenced team photo: {photo_path}")
    team_dir = os.path.join('media', 'admin', 'team')
    if os.path.exists(team_dir) and not os.listdir(team_dir):
        os.rmdir(team_dir)
        print(f"Removed empty directory: {team_dir}")
else:
    print("No team photo found on disk to delete.")

print("Migration completed successfully!")

