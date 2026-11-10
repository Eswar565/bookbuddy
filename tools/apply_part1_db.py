import sqlite3

for db_path in ["instance/book_buddy_dev.sqlite3", "instance/book_buddy.sqlite3"]:
    print(f"Updating {db_path}...")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    
    # 1. Delete membership from homepage_sections
    cur.execute("DELETE FROM homepage_sections WHERE id=12 OR lower(section_key)='membership'")
    print(f"  Deleted {cur.rowcount} membership rows from homepage_sections")
    
    # 2. Delete any retired sections that might be lingering
    cur.execute("DELETE FROM homepage_sections WHERE lower(section_key) IN ('challenges', 'innovation', 'visit', 'collection', 'media', 'footer')")
    
    # 3. Update hero buttons so neither links to /membership/
    cur.execute("""
        UPDATE homepage_sections 
        SET button2_label='Explore the Library', button2_url='/library/',
            button_label='Contact Us', url='/contact/'
        WHERE section_key='hero'
    """)
    print("  Updated hero buttons to /library/ and /contact/")
    
    # 4. Update publications description to remove podcast reference
    cur.execute("""
        UPDATE homepage_sections
        SET description='Our community newspaper — stories, reviews, and reading roadmaps written by the community, for the community.'
        WHERE section_key='publications'
    """)
    print("  Updated publications section description")
    
    # 5. Remove 'Membership & Plans' from site_navigation footer_useful
    cur.execute("DELETE FROM site_navigation WHERE group_name='footer_useful' AND (label='Membership & Plans' OR url LIKE '%membership%')")
    print(f"  Deleted {cur.rowcount} membership links from site_navigation")
    
    # Check remaining sections
    remaining = cur.execute("SELECT id, section_key, title, position, is_active FROM homepage_sections ORDER BY position, id").fetchall()
    print("  Remaining homepage_sections:")
    for r in remaining:
        print("   ", r)
        
    con.commit()
    con.close()

