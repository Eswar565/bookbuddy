import sqlite3

db = sqlite3.connect('instance/book_buddy.sqlite3')
new_addr = "1, Thiruvalluvar St, Thiru Nagar Colony, Gandhi Nagar,\nSaligramam, Chennai, Tamil Nadu 600093"
db.execute("UPDATE site_content SET content_value=? WHERE content_key='contact_address'", (new_addr,))
db.execute("INSERT OR IGNORE INTO schema_updates(version) VALUES('chennai-saligramam-address-v3')")
db.commit()

row = db.execute("SELECT content_value FROM site_content WHERE content_key='contact_address'").fetchone()
print("Updated contact_address in database:", row[0] if row else None)
db.close()

