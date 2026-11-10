import sqlite3

def run_migration(db_path):
    print(f"=== Migrating {db_path} ===")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. site_navigation table
    cur.execute('''CREATE TABLE IF NOT EXISTS site_navigation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT NOT NULL,
        label TEXT NOT NULL,
        url TEXT NOT NULL,
        position INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )''')
    
    # Check if site_navigation has rows; if not, seed defaults
    nav_count = cur.execute('SELECT COUNT(*) FROM site_navigation').fetchone()[0]
    if nav_count == 0:
        default_nav = [
            # Header nav
            ('header', 'Home', '/', 10, 1),
            ('header', 'About', '/about/', 20, 1),
            ('header', 'Library', '/library/', 30, 1),
            ('header', 'Events', '/events/', 40, 1),
            ('header', 'Media', '/publications/?kind=news', 50, 1),
            ('header', 'Contact', '/contact/', 60, 1),
            # Footer useful links
            ('footer_useful', 'Library Catalogue', '/library/', 10, 1),
            ('footer_useful', 'Membership & Plans', '/membership/', 20, 1),
            ('footer_useful', 'Monthly Magazine', '/publications/?kind=magazine', 30, 1),
            ('footer_useful', 'Newspaper', '/publications/?kind=news', 40, 1),
            # Footer bottom links
            ('footer_bottom', 'Our story', '/about/', 10, 1),
            ('footer_bottom', 'Contact', '/contact/', 20, 1),
            ('footer_bottom', 'Collaborate', '/work-with-us/', 30, 1),
        ]
        cur.executemany(
            'INSERT INTO site_navigation (group_name, label, url, position, is_active) VALUES (?, ?, ?, ?, ?)',
            default_nav
        )
        print(f"  Seeded {len(default_nav)} navigation links.")
    else:
        print(f"  site_navigation already has {nav_count} rows.")

    # 2. partner_submissions table
    cur.execute('''CREATE TABLE IF NOT EXISTS partner_submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT DEFAULT '',
        organisation TEXT DEFAULT '',
        proposal_type TEXT DEFAULT 'Partner',
        message TEXT NOT NULL,
        status TEXT DEFAULT 'New',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    print("  Ensured partner_submissions table exists.")
    
    # Add a sample partner submission if empty
    p_count = cur.execute('SELECT COUNT(*) FROM partner_submissions').fetchone()[0]
    if p_count == 0:
        cur.execute('''INSERT INTO partner_submissions (full_name, email, phone, organisation, proposal_type, message, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            ('Kavitha Sundaram', 'kavitha@readershub.org', '+91 98401 23456', 'Readers Hub Chennai', 'Reading Circle Partner',
             'We would love to co-host monthly reading circles and donate curated bilingual book bundles.', 'New')
        )
        print("  Seeded sample partner submission.")

    # 3. Add button2_label and button2_url to homepage_sections if missing
    col_info = [r[1] for r in cur.execute('PRAGMA table_info(homepage_sections)').fetchall()]
    if 'button2_label' not in col_info:
        cur.execute("ALTER TABLE homepage_sections ADD COLUMN button2_label TEXT DEFAULT ''")
        print("  Added button2_label to homepage_sections.")
    if 'button2_url' not in col_info:
        cur.execute("ALTER TABLE homepage_sections ADD COLUMN button2_url TEXT DEFAULT ''")
        print("  Added button2_url to homepage_sections.")

    # 4. Clean out obsolete sections and ensure exact 5 homepage sections in order
    cur.execute("DELETE FROM homepage_sections WHERE section_key IN ('challenges', 'innovation', 'heroffff', 'collection', 'media', 'visit', 'membership')")
    
    sections = [
        ('hero', 'Books, Stories & Ideas', 'BOOK BUDDY',
         "With our curated library and story-based academic support, we help you master the skills textbooks alone can't teach.",
         '/static/img/brand/bookbuddy-official-logo.png', 'Book Buddy Logo',
         'Weekly Book Delivery', '/membership/', 10, 1, 'All Under One Roof',
         'Explore the Library', '/library/'),
        ('community', 'Join Our Community: Online or In-Person', 'COMMUNITY & EVENTS',
         'Two ways to plug in: walk into our Saligramam room, or join a live session from anywhere.',
         '/static/img/art/04-reading-circle.png', 'Reading Community',
         'RSVP via WhatsApp', 'https://wa.me/919080759312', 20, 1, '', '', ''),
        ('publications', 'The Book Buddy Times & More', 'PUBLICATIONS',
         'Our monthly newspaper and podcast — written by the community, for the community.',
         '/static/img/art/07-newspaper.png', 'Newspaper Cover',
         'Read the Newspaper', '/publications/?kind=news', 30, 1, 'Issue #5 is here', '', ''),
        ('reviews', 'Verified Ratings on Google Maps', 'Google Reviews',
         '120+ verified community ratings from students, parents, and readers.',
         '/static/img/art/05-membership-card.png', 'Google Reviews Badge',
         'Review us on Google', 'https://maps.google.com/?q=Book+Buddy+Library', 40, 1, '4.9', '', ''),
        ('footer', 'Footer & Library Details', 'BOOK BUDDY FOOTER',
         'A welcoming lending library for discovering books, fostering curiosity, and connecting with community.',
         '/static/img/brand/bookbuddy-official-logo.png', 'Book Buddy Official Logo',
         'Explore Membership', '/membership/', 50, 1, '', '', '')
    ]
    
    for key, title, kicker, desc, img, alt, b1_label, b1_url, pos, act, high, b2_label, b2_url in sections:
        cur.execute('''INSERT INTO homepage_sections
            (section_key, title, kicker, description, image_path, image_alt, button_label, url, position, is_active, highlight, button2_label, button2_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(section_key) DO UPDATE SET
                title=excluded.title, kicker=excluded.kicker, description=excluded.description,
                image_path=excluded.image_path, image_alt=excluded.image_alt,
                button_label=excluded.button_label, url=excluded.url,
                position=excluded.position, is_active=excluded.is_active,
                highlight=excluded.highlight, button2_label=excluded.button2_label,
                button2_url=excluded.button2_url''',
            (key, title, kicker, desc, img, alt, b1_label, b1_url, pos, act, high, b2_label, b2_url)
        )
    print("  Ensured 5 homepage sections seeded in exact order (hero, community, publications, reviews, footer).")

    # 5. Seed detailed content keys in site_content
    detailed_content = {
        # Hero
        'hero_kicker': 'BOOK BUDDY',
        'hero_line1': 'Books, Stories & Ideas',
        'hero_line2': 'All Under One Roof',
        'hero_text': "With our curated library and story-based academic support, we help you master the skills textbooks alone can't teach.",
        'hero_primary_button_label': 'Explore the Library',
        'hero_primary_button_url': '/library/',
        'hero_secondary_button_label': 'Weekly Book Delivery',
        'hero_secondary_button_url': '/membership/',

        # Community & Events
        'comm_kicker': 'COMMUNITY & EVENTS',
        'comm_title': 'Join Our Community: Online or In-Person',
        'comm_text': 'Two ways to plug in: walk into our Saligramam room, or join a live session from anywhere.',
        'comm_whatsapp_btn': 'RSVP via WhatsApp',
        'comm_whatsapp_url': 'https://wa.me/919080759312',
        'comm_card1_tag': 'In-Library',
        'comm_card1_title': 'The Sunday Reading Circle',
        'comm_card1_schedule': 'Every Sunday · 6:00 PM – 8:00 PM',
        'comm_card1_desc': 'Join parents and kids for Pomodoro-style reading sprints, team-building games, and collaborative learning.',
        'comm_card1_btn': 'RSVP via WhatsApp',
        'comm_card1_url': 'https://wa.me/919080759312',
        'comm_card2_tag': 'Live Online',
        'comm_card2_title': 'Virtual Storytelling Sessions',
        'comm_card2_schedule': 'Weekly · Zoom',
        'comm_card2_desc': 'Interactive, narrative-driven sessions focused on imagination, voice expression, and communication skills.',
        'comm_card2_btn': 'View Schedule',
        'comm_card2_url': '/reading-circles/',

        # Publications
        'pub_kicker': 'PUBLICATIONS',
        'pub_title': 'The Book Buddy Times & More',
        'pub_text': 'Our monthly newspaper and podcast — written by the community, for the community.',
        'pub_news_img': '/static/img/art/07-newspaper.png',
        'pub_news_tag': 'Issue #5 is here',
        'pub_news_title': 'Our 3-year reading roadmap — stories and young reviewer features.',
        'pub_news_desc': "This month: how we're expanding library collections, reading tips from educators, and comic strips from our Friday reading circle.",
        'pub_news_btn': 'Read the Newspaper',
        'pub_news_url': '/publications/?kind=news',
        'pub_pod_img': '/static/img/art/08-podcast.png',
        'pub_pod_tag': 'Community Podcast',
        'pub_pod_title': 'Stories & Conversations from Book Buddy',
        'pub_pod_desc': 'Listen to student reviews, author chats, and weekly storytelling episodes directly from our recording room.',
        'pub_pod_btn': 'Listen to the Podcast',
        'pub_pod_url': '/podcasts/',

        # Reviews
        'reviews_kicker': 'Google Reviews',
        'reviews_title': 'Verified Ratings on Google Maps',
        'google_rating': '4.9',
        'google_review_count': '120+ Verified Reviews',
        'google_review_url': 'https://maps.google.com/?q=Book+Buddy+Library',
        'reviews_btn': 'Review us on Google',
        'reviews_quote1_text': 'An amazing library and community space. Kids love the reading circles and storytelling sessions!',
        'reviews_quote1_author': 'Priya R.',
        'reviews_quote2_text': 'Best curated collection in Chennai. The delivery service and book recommendations are wonderful.',
        'reviews_quote2_author': 'Karthik S.',
        'reviews_quote3_text': 'Warm atmosphere, knowledgeable mentors, and a great place for readers of all ages.',
        'reviews_quote3_author': 'Ananya M.',

        # Footer
        'footer_logo_img': '/static/img/brand/bookbuddy-official-logo.png',
        'footer_bio': 'A welcoming lending library for discovering books, fostering curiosity, and connecting with community.',
        'footer_hours_heading': 'Working Hours',
        'footer_hours_days': 'Tuesday – Sunday:\n10:00 AM – 1:00 PM\n4:30 PM – 8:30 PM',
        'footer_hours_closed': 'Monday:\nClosed',
        'contact_phone': '+91 9080759312',
        'contact_email': 'bookbuddy.edu@gmail.com',
        'contact_address': 'MK Complex 2nd floor Chennai Hot Puffs upstairs, K.Pudur, Madurai, Tamil Nadu 625007',
        'footer_copyright': 'Copyright © 2026 by bookbuddy. All Rights Reserved.'
    }
    
    for k, v in detailed_content.items():
        cur.execute('''INSERT INTO site_content (content_key, content_value) VALUES (?, ?)
            ON CONFLICT(content_key) DO UPDATE SET content_value=excluded.content_value''', (k, v))
    print(f"  Seeded {len(detailed_content)} site_content values.")

    # 6. Notifications trigger for partner submissions
    cur.execute("DROP TRIGGER IF EXISTS notify10_partner_submissions")
    cur.execute('''CREATE TRIGGER IF NOT EXISTS notify10_partner_submissions AFTER INSERT ON partner_submissions
    WHEN (SELECT value FROM app_flags WHERE key='notifications_enabled')='1'
    BEGIN
        INSERT OR IGNORE INTO admin_notifications(kind,title,body,url,source_key)
        VALUES ('partners', 'New partner enquiry', NEW.full_name || ' · ' || NEW.organisation, '/admin/manage/partners/' || NEW.id || '/', 'partner_submissions:' || NEW.id);
    END;''')
    print("  Created notify10_partner_submissions trigger.")

    conn.commit()
    conn.close()
    print("Migration finished.\n")

if __name__ == '__main__':
    for p in ['instance/book_buddy.sqlite3', 'instance/book_buddy_dev.sqlite3']:
        run_migration(p)

