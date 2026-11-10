"""Administrator-owned homepage sections and catalogue audiences."""
from management import MODELS, NUMBERS, LONG

def install_site_design(app,db):
    with app.app_context():
        db().execute('''CREATE TABLE IF NOT EXISTS homepage_sections (id INTEGER PRIMARY KEY, section_key TEXT UNIQUE NOT NULL, title TEXT NOT NULL, kicker TEXT DEFAULT '', description TEXT DEFAULT '', image_path TEXT DEFAULT '', image_alt TEXT DEFAULT '', button_label TEXT DEFAULT '', url TEXT DEFAULT '', position INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1)''')
        if 'audience' not in {r[1] for r in db().execute('PRAGMA table_info(books)')}:
            db().execute("ALTER TABLE books ADD COLUMN audience TEXT NOT NULL DEFAULT 'all'")
            db().execute("UPDATE books SET audience='kids' WHERE lower(age_group) LIKE '%kid%' OR lower(age_group) LIKE '%child%'")
            db().execute("UPDATE books SET audience='adult' WHERE lower(age_group) LIKE '%adult%' OR age_group='18+'");
        if not db().execute("SELECT 1 FROM schema_updates WHERE version='homepage-admin-v5'").fetchone():
            defaults=[
            ('hero','A new chapter starts here.','YOUR COMMUNITY LIBRARY','Find a book to love, join a reading circle and make room for new ideas.','/static/img/art/01-hero-readers.png','Readers enjoying a book','Explore the library','/library/',0),
            ('collection','Find your next favourite.','ON OUR SHELVES','Discover books for children and adults, in the languages you love.','/static/img/art/02-book-shelves.png','Illustrated library shelves','Browse all books','/library/',10),
            ('community','Stories are better together.','OUR READING COMMUNITY','Meet fellow readers, share your perspective and discover something new.','/static/img/art/04-reading-circle.png','Reading circle illustration','Join a reading circle','/reading-circles/',20),
            ('membership','Make reading part of your everyday.','LIBRARY MEMBERSHIP','Choose a membership and enjoy more stories, ideas and discoveries.','/static/img/art/05-membership-card.png','Library membership illustration','Explore membership','/membership-options/',30),
            ('media','Fresh voices. New perspectives.','THE COMMUNITY EDIT','Explore newspapers, magazines and podcasts. Discover free editions and member reading.','/static/img/art/06-magazine.png','Magazine illustration','Explore media','/publications/',40),
            ('visit','Your community, one page at a time.','COME SAY HELLO','Visit the library, ask a question or share your next great reading idea.','/static/img/art/03-contact-envelope.png','Community illustration','Contact the library','/contact/',50)]
            for key,title,kicker,desc,img,alt,label,url,pos in defaults:
                db().execute('INSERT OR IGNORE INTO homepage_sections(section_key,title,kicker,description,image_path,image_alt,button_label,url,position) VALUES(?,?,?,?,?,?,?,?,?)',(key,title,kicker,desc,img,alt,label,url,pos))
            db().execute("INSERT INTO schema_updates(version) VALUES('homepage-admin-v5')")
        if 'highlight' not in {r[1] for r in db().execute('PRAGMA table_info(homepage_sections)')}:
            db().execute("ALTER TABLE homepage_sections ADD COLUMN highlight TEXT NOT NULL DEFAULT ''")
        if not db().execute("SELECT 1 FROM schema_updates WHERE version='official-brand-v7'").fetchone():
            for key,value in {
                'contact_phone':'+91 9080759312',
                'contact_email':'bookbuddy.edu@gmail.com',
                'contact_address':'MK Complex 2nd floor Chennai Hot Puffs upstairs, K.Pudur, Madurai, Tamil Nadu 625007'
            }.items():
                db().execute('INSERT INTO site_content(content_key,content_value) VALUES(?,?) ON CONFLICT(content_key) DO UPDATE SET content_value=excluded.content_value',(key,value))
            db().execute("UPDATE homepage_sections SET title=?,highlight=?,kicker=?,description=?,button_label=? WHERE section_key='hero'",('A book today.','A bigger world tomorrow.','READ. DISCOVER. BELONG.','Find stories for every age, explore Tamil, English and Hindi books, and connect with a community that loves to read.','Find your next read'))
            db().execute("INSERT INTO schema_updates(version) VALUES('official-brand-v7')")
        if not db().execute("SELECT 1 FROM schema_updates WHERE version='madurai-address-v2'").fetchone():
            db().execute("UPDATE site_content SET content_value=? WHERE content_key='contact_address'",
                         ('MK Complex 2nd floor Chennai Hot Puffs upstairs, K.Pudur, Madurai, Tamil Nadu 625007',))
            db().execute("INSERT INTO schema_updates(version) VALUES('madurai-address-v2')")
        if not db().execute("SELECT 1 FROM schema_updates WHERE version='brand-art-v8'").fetchone():
            mapping = {
                'hero-readers': '/static/img/art/01-hero-readers.png',
                'bookbuddy-hero': '/static/img/art/01-hero-readers.png',
                'library-shelf': '/static/img/art/02-book-shelves.png',
                'book-shelves': '/static/img/art/02-book-shelves.png',
                'reading-circle': '/static/img/art/04-reading-circle.png',
                'membership': '/static/img/art/05-membership-card.png',
                'magazine': '/static/img/art/06-magazine.png',
                'newspaper': '/static/img/art/07-newspaper.png',
                'podcast': '/static/img/art/08-podcast.png',
                'gallery': '/static/img/art/09-gallery.png',
                'contest': '/static/img/art/10-contest.png',
                'contact': '/static/img/art/03-contact-envelope.png',
                'about': '/static/img/art/11-about-library.png',
            }
            rows = db().execute("SELECT id, image_path FROM homepage_sections WHERE image_path LIKE '/static/img/storybook/%'").fetchall()
            for row in rows:
                row_id = row[0]
                old_path = row[1]
                for key, new_path in mapping.items():
                    if key in old_path:
                        db().execute("UPDATE homepage_sections SET image_path=? WHERE id=?", (new_path, row_id))
                        break
            db().execute("INSERT INTO schema_updates(version) VALUES('brand-art-v8')")
        if not db().execute("SELECT 1 FROM schema_updates WHERE version='live-theme-v8'").fetchone():
            v8_sections = [
                ('hero', 'Books, Learning & Skills', 'BOOK BUDDY', 'With our curated library and story-based academic support, we help you master the skills textbooks alone can\'t teach.', '/static/img/brand/bookbuddy-official-logo.png', 'Book Buddy', '', '', 1, 1, 'All Under One Roof'),
                ('community', 'Join Our Community: Online or In-Person', 'COMMUNITY & EVENTS', 'Two ways to plug in: walk into our Saligramam room, or join a live session from anywhere.', '/static/img/art/04-reading-circle.png', 'Reading community', 'RSVP via WhatsApp', 'https://wa.me/919080759312', 2, 1, ''),
                ('publications', 'The Book Buddy Times & More', 'PUBLICATIONS', 'Our monthly newspaper and podcast — written by the community, for the community.', '/static/img/art/07-newspaper.png', 'The Book Buddy Times', 'Read the Newspaper', '/publications/?kind=news', 3, 1, 'Issue #5 is here'),
                ('reviews', 'Verified Ratings on Google Maps', 'Google Reviews', '120+ verified community ratings from students, parents, and readers.', '/static/img/art/05-membership-card.png', 'Google Reviews', 'Review us on Google', 'https://maps.google.com/?q=Book+Buddy+Library', 4, 1, '4.9'),
            ]
            for key, title, kicker, desc, img, alt, label, url, pos, act, high in v8_sections:
                db().execute('''INSERT INTO homepage_sections(section_key, title, kicker, description, image_path, image_alt, button_label, url, position, is_active, highlight)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(section_key) DO UPDATE SET
                    title=excluded.title, kicker=excluded.kicker, description=excluded.description,
                    button_label=excluded.button_label, url=excluded.url, position=excluded.position,
                    is_active=excluded.is_active, highlight=excluded.highlight''',
                (key, title, kicker, desc, img, alt, label, url, pos, act, high))
            for k, val in {
                'google_rating': '4.9',
                'google_review_count': '120+ Reviews',
                'google_review_url': 'https://maps.google.com/?q=Book+Buddy+Library',
                'hero_secondary_button_label': 'Weekly Book Delivery',
                'hero_secondary_button_url': '/membership/'
            }.items():
                db().execute("INSERT INTO site_content(content_key, content_value) VALUES (?, ?) ON CONFLICT(content_key) DO UPDATE SET content_value=excluded.content_value", (k, val))
            db().execute("INSERT INTO schema_updates(version) VALUES('live-theme-v8')")
        # Ensure retired sections are removed from active databases
        db().execute("DELETE FROM homepage_sections WHERE lower(section_key) IN ('challenges', 'innovation', 'membership', 'visit', 'collection', 'media', 'footer')")
        db().execute("UPDATE homepage_sections SET button_label='Contact Us', url='/contact/' WHERE section_key='hero' AND (button_label='Weekly Book Delivery' OR url LIKE '%membership%')")
        db().execute("DELETE FROM site_navigation WHERE group_name='footer_useful' AND (label='Membership & Plans' OR url LIKE '%membership%')")
        db().commit()
    MODELS['home-sections']=('Homepage content & images','homepage_sections','section_key title highlight kicker description image_path image_alt button_label url button2_label button2_url position is_active')
    name,table,fields=MODELS['books']
    if 'audience' not in fields.split():MODELS['books']=(name,table,fields+' audience')
    NUMBERS.add('position');LONG.add('description')
    @app.context_processor
    def homepage_content():
        rows=[dict(r) for r in db().execute('SELECT * FROM homepage_sections WHERE is_active=1 ORDER BY position,id')]
        sec_map = {r['section_key']: r for r in rows}
        return {
            'homepage_sections': rows,
            'homepage_hero': sec_map.get('hero') or next((r for r in rows if r['section_key']=='hero'), None),
            'homepage_map': sec_map
        }
