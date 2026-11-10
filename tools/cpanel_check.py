"""Read-only deployment checks (never displays credentials or sends payments)."""
import os,sys,sqlite3
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
root=Path(__file__).resolve().parents[1]
load_dotenv(os.environ.get('BOOK_BUDDY_ENV_FILE',root/'.env'),override=False)
checks=[]
def check(label,ok):checks.append(bool(ok));print(('PASS  ' if ok else 'CHECK ')+label)
check('Python 3.11 or newer',sys.version_info >= (3,11))
check('Production SECRET_KEY supplied',len(os.environ.get('SECRET_KEY',''))>=32)
check('HTTPS session cookies enabled',os.environ.get('COOKIE_SECURE')=='1')
check('Debug disabled',os.environ.get('FLASK_DEBUG','0')=='0')
for key in ('SITE_URL','PUBLIC_BASE_URL'):check(key+' uses your HTTPS domain',os.environ.get(key,'').startswith('https://') and 'example.com' not in os.environ.get(key,''))
for key in ('RAZORPAY_KEY_ID','RAZORPAY_KEY_SECRET','RAZORPAY_WEBHOOK_SECRET','RAZORPAY_MEMBERSHIP_WEBHOOK_SECRET'):check(key+' configured',bool(os.environ.get(key)))
for key in ('BOOK_BUDDY_DATABASE','BOOK_BUDDY_PRIVATE_DIR','BOOK_BUDDY_BACKUP_DIR'):
    value=os.environ.get(key,'');check(key+' is an absolute private path',bool(value) and Path(value).is_absolute() and 'public_html' not in Path(value).parts)
try:
    from passenger_wsgi import application
    from app import get_db
    with application.app_context():
        db=get_db();check('SQLite integrity',db.execute('PRAGMA quick_check').fetchone()[0]=='ok')
    with application.test_client() as client:
        for url in ('/','/library/','/events/','/membership-options/','/admin/login/'):
            check('Passenger app renders '+url,client.get(url).status_code==200)
except Exception as error:
    check('Passenger import and database startup ('+type(error).__name__+')',False)
print('\nNo gateway request or email was sent. Test checkout and HTTPS webhooks on staging before live payments.')
sys.exit(0 if all(checks) else 1)
