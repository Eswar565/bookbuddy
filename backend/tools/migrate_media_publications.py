import sqlite3

columns_to_add = [
    ("volume", "TEXT DEFAULT ''"),
    ("issue_number", "TEXT DEFAULT ''"),
    ("badge_label", "TEXT DEFAULT ''"),
    ("episode_label", "TEXT DEFAULT ''"),
    ("position", "INTEGER DEFAULT 0"),
]

for db_name in ['book_buddy_dev.sqlite3', 'book_buddy.sqlite3']:
    conn = sqlite3.connect(f'instance/{db_name}')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check existing columns
    existing = {row['name'] for row in c.execute("PRAGMA table_info(publications)").fetchall()}
    for col, col_type in columns_to_add:
        if col not in existing:
            print(f"Adding column {col} to {db_name}")
            c.execute(f"ALTER TABLE publications ADD COLUMN {col} {col_type}")
            
    # Seed site_content keys
    site_content_seeds = [
        # Newspaper
        ("newspaper_pill", "Press & Media"),
        ("newspaper_heading", "The Chronicle Archive"),
        ("newspaper_accent", "Chronicle"),
        ("newspaper_subtitle", "Exploring the intersection of stories and learning."),
        # Magazine
        ("magazine_pill", "Publication & Media"),
        ("magazine_heading", "The Magazine Archive"),
        ("magazine_accent", "Magazine"),
        ("magazine_subtitle", "Celebrating creativity and community through every page."),
        ("magazine_cta_heading", "Have something amazing to share?"),
        ("magazine_cta_text", "We are always looking for creative stories, artwork, and articles from our young readers. Submit your contribution for a chance to be featured in our next magazine!"),
        ("magazine_cta_btn", "Submit Your Work"),
        # Podcasts
        ("podcast_pill", "Media & Audio"),
        ("podcast_heading", "The Podcast Archive"),
        ("podcast_accent", "Podcast"),
        ("podcast_subtitle", "Exploring the world of stories and learning."),
    ]
    for key, val in site_content_seeds:
        c.execute("""
            INSERT INTO site_content (content_key, content_value)
            VALUES (?, ?)
            ON CONFLICT(content_key) DO NOTHING
        """, (key, val))
        
    # Update sample publications to match real data standards
    # id 5 is news
    c.execute("""
        UPDATE publications SET 
            volume = CASE WHEN volume = '' THEN 'VOLUME 01' ELSE volume END,
            issue_number = CASE WHEN issue_number = '' THEN 'ISSUE 01' ELSE issue_number END,
            edition = CASE WHEN edition = '' OR edition = 'FIrst' THEN 'VOLUME 01 | ISSUE 01' ELSE edition END
        WHERE kind = 'news'
    """)
    # id 1, 2, 3, 4 are magazines
    c.execute("""
        UPDATE publications SET badge_label = 'INTERACTIVE' WHERE id = 1 AND badge_label = ''
    """)
    c.execute("""
        UPDATE publications SET edition = 'October Edition' WHERE id = 2 AND (edition = '' OR edition = 'Special Edition')
    """)
    c.execute("""
        UPDATE publications SET edition = 'September Edition' WHERE id = 3 AND (edition = '' OR edition = 'Special Edition')
    """)
    c.execute("""
        UPDATE publications SET edition = 'August Edition' WHERE id = 4 AND (edition = '' OR edition = 'Special Edition')
    """)
    # id 6 is podcast
    c.execute("""
        UPDATE publications SET 
            episode_label = CASE WHEN episode_label = '' THEN 'EPISODE 01' ELSE episode_label END,
            embed_url = CASE WHEN embed_url = '' THEN 'https://open.spotify.com/episode/7mK9c595oY07G4T94Qk82x' ELSE embed_url END
        WHERE kind = 'podcast'
    """)
    
    # Navigation cleanup:
    # 1. Update site_navigation header and footer links
    # Remove any gallery link from header or footer in site_navigation
    c.execute("DELETE FROM site_navigation WHERE url LIKE '%/gallery%'")
    
    # In footer_useful: ensure we have Newspaper (/newspaper/), Magazine (/magazine/), Podcasts (/podcasts/)
    # Check if footer_useful has newspaper, magazine, podcast
    footer_links = [r['url'] for r in c.execute("SELECT url FROM site_navigation WHERE group_name='footer_useful'").fetchall()]
    print(f"{db_name} existing footer_useful urls:", footer_links)
    
    # Update URLs to the dedicated /newspaper/, /magazine/, /podcasts/
    c.execute("UPDATE site_navigation SET url='/newspaper/', label='Newspaper' WHERE group_name='footer_useful' AND (url LIKE '%news%' OR label LIKE '%Newspaper%')")
    c.execute("UPDATE site_navigation SET url='/magazine/', label='Monthly Magazine' WHERE group_name='footer_useful' AND (url LIKE '%magazine%' OR label LIKE '%Magazine%')")
    
    # If podcasts not in footer_useful, add it
    has_podcasts = c.execute("SELECT 1 FROM site_navigation WHERE group_name='footer_useful' AND (url LIKE '%podcast%' OR label LIKE '%Podcast%')").fetchone()
    if not has_podcasts:
        c.execute("INSERT INTO site_navigation (group_name, label, url, position, is_active) VALUES ('footer_useful', 'Podcasts', '/podcasts/', 50, 1)")
        
    conn.commit()
    conn.close()
    print(f"Migration completed for {db_name}")

