"""Library membership extensions and shared input validation. No remote reference content."""
import calendar
from datetime import date
from urllib.parse import urlsplit
from management import MODELS, NUMBERS, LONG

IMPORTABLE = {'books', 'events', 'publications', 'pages', 'navigation', 'plans', 'heroes', 'gallery', 'coupons'}

def valid_url(value):
    if not value: return True
    if not isinstance(value, str) or any(ord(c)<32 for c in value) or '\\' in value: return False
    try: uri=urlsplit(value)
    except ValueError: return False
    return (value.startswith('/') and not value.startswith('//')) or (uri.scheme in ('http','https') and bool(uri.hostname) and not uri.username and not uri.password)

def add_months(start, months):
    month=start.month-1+months
    year=start.year+month//12
    month=month%12+1
    return start.replace(year=year,month=month,day=min(start.day,calendar.monthrange(year,month)[1]))

def install_library_core(app,db):
    with app.app_context():
        columns={row[1] for row in db().execute('PRAGMA table_info(plans)')}
        additions={'duration_months':'INTEGER DEFAULT 0', 'books_at_time':'INTEGER DEFAULT 0', 'total_books':'INTEGER DEFAULT 0', 'tagline':"TEXT DEFAULT ''", 'benefits':"TEXT DEFAULT ''", 'family':"TEXT DEFAULT ''", 'seed_key':"TEXT DEFAULT ''"}
        for name,definition in additions.items():
            if name not in columns:
                db().execute(f'ALTER TABLE plans ADD COLUMN {name} {definition}')
        db().commit()
    MODELS['plans']=('Membership plans','plans','title family tagline description price duration_months duration_days books_at_time total_books benefits scopes is_active')
    NUMBERS.update({'duration_months','books_at_time','total_books'})
    LONG.add('benefits')
