from werkzeug.security import check_password_hash
import sqlite3

conn = sqlite3.connect('instance/book_buddy_dev.sqlite3')
h = conn.execute("SELECT password_hash FROM admin_users WHERE email='admin@gmail.com'").fetchone()[0]
for p in ['admin', 'admin123', 'password', 'bookbuddy', 'admin@123', 'adminpass', '123456', 'Admin@123', 'superadmin', 'admin2026', 'library']:
    if check_password_hash(h, p):
        print('Password is:', p)
        break
else:
    print('None of common passwords matched, hash:', h[:30])
conn.close()

