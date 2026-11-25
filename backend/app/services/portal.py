"""Library lending, membership, accounts and staff operations.

Single organization per installation. No pretend multi-tenant isolation.
All new mutations are CSRF checked, permission checked and transactional.
"""
from __future__ import annotations
import csv, hashlib, hmac, io, json, os, re, secrets, smtplib, sqlite3, time
from datetime import datetime, timedelta, date, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from email.message import EmailMessage
from functools import wraps
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from flask import abort, request, session, redirect, flash, render_template, jsonify, send_file, Response, url_for
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from accounts import years_old, academic_label, age_matches

ROLES={'super_admin','org_admin','librarian','support'}

def resolve_timezone(name):
    """Use IANA rules, with a current India/UTC fallback if tzdata is absent."""
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name in {'Asia/Kolkata', 'Asia/Calcutta'}:
            return timezone(timedelta(hours=5, minutes=30), 'IST')
        if name in {'UTC', 'Etc/UTC'}:
            return timezone.utc
        raise

def today(): return datetime.now(resolve_timezone('Asia/Kolkata')).date()
def paise(value):
    try:
        amount=Decimal(str(value))
        if not amount.is_finite() or amount<0 or amount>1000000: raise ValueError()
        return int((amount*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    except (InvalidOperation,ValueError): abort(400,'Enter a valid amount between 0 and 1,000,000.')
def integer(value, low=0, high=100000):
    try: n=int(value)
    except (ValueError,TypeError): abort(400,'Enter a valid whole number.')
    if n<low or n>high: abort(400,'Number is outside the permitted range.')
    return n
def textfield(name,limit=200,required=False):
    value=request.form.get(name,'').strip()
    if len(value)>limit or (required and not value): abort(400,f'Check {name.replace("_"," ")}.')
    return value

def install_release17(app,db,render,admin,root):
    if os.environ.get('BOOK_BUDDY_MULTITENANT')=='1':raise RuntimeError('This release supports one organization per installation. Shared database multi-tenancy is disabled.')
    is_vercel = os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None
    default_private = Path('/tmp/private') if is_vercel else root/'instance'/'private'
    private=Path(os.environ.get('BOOK_BUDDY_PRIVATE_DIR', default_private)).resolve()
    try:
        private.mkdir(parents=True,exist_ok=True)
    except OSError:
        pass
    app.config['PRIVATE_DIR17']=private
    app.config['PUBLIC_ENDPOINTS17']={'home_calendar10','reset_finish17','membership_webhook17','razorpay_webhook_v9','save_subscriber','capture_lead','contact_submit','healthz16','account_reset_password','account_reset_password_short'}
    with app.app_context():
        c=db()
        additions={
          'admin_users':{'role':"TEXT NOT NULL DEFAULT 'super_admin'",'is_active':'INTEGER NOT NULL DEFAULT 1'},
          'users':{'email_verified':'INTEGER NOT NULL DEFAULT 0','session_version':'INTEGER NOT NULL DEFAULT 0'},
          'books':{'isbn':"TEXT NOT NULL DEFAULT ''",'publisher':"TEXT NOT NULL DEFAULT ''",'edition':"TEXT NOT NULL DEFAULT ''",'archived':'INTEGER NOT NULL DEFAULT 0'},
          'lending_plans':{
              'duration_days':'INTEGER NOT NULL DEFAULT 30','loan_days':'INTEGER NOT NULL DEFAULT 14','renewal_limit':'INTEGER NOT NULL DEFAULT 1','fine_daily_paise':'INTEGER NOT NULL DEFAULT 0','learning_access':'INTEGER NOT NULL DEFAULT 1','ai_access':'INTEGER NOT NULL DEFAULT 0',
              'tier':"TEXT NOT NULL DEFAULT ''",'tagline':"TEXT NOT NULL DEFAULT ''",'badge':"TEXT NOT NULL DEFAULT ''",'benefits':"TEXT NOT NULL DEFAULT ''",'total_books':'INTEGER NOT NULL DEFAULT 0'
          },
          'lending_loans':{
              'copy_id':'INTEGER REFERENCES copies17(id)','return_requested_at':"TEXT NOT NULL DEFAULT ''",'renewals':'INTEGER NOT NULL DEFAULT 0','fine_daily_paise':'INTEGER NOT NULL DEFAULT 0',
              'request_id':'INTEGER REFERENCES lending_requests(id)','delivery_mode':"TEXT NOT NULL DEFAULT ''",'delivery_address':"TEXT NOT NULL DEFAULT ''",'contact_phone':"TEXT NOT NULL DEFAULT ''"
          },
          'lending_subscriptions':{
              'duration_snapshot':'INTEGER NOT NULL DEFAULT 0','learning_snapshot':'INTEGER NOT NULL DEFAULT 1','ai_snapshot':'INTEGER NOT NULL DEFAULT 0',
              'child_name':"TEXT NOT NULL DEFAULT ''",'child_dob':"TEXT NOT NULL DEFAULT ''",'student_grade':"TEXT NOT NULL DEFAULT ''",'parent_name':"TEXT NOT NULL DEFAULT ''",'email':"TEXT NOT NULL DEFAULT ''",'phone':"TEXT NOT NULL DEFAULT ''",
              'service_mode':"TEXT NOT NULL DEFAULT 'offline'",'delivery_fee':'REAL NOT NULL DEFAULT 0','address_flat':"TEXT NOT NULL DEFAULT ''",'address_street':"TEXT NOT NULL DEFAULT ''",'address_city':"TEXT NOT NULL DEFAULT ''",'address_state':"TEXT NOT NULL DEFAULT ''",'address_pincode':"TEXT NOT NULL DEFAULT ''",'address_country':"TEXT NOT NULL DEFAULT 'India'",'referral_code':"TEXT NOT NULL DEFAULT ''"
          },
        }
        c.execute("""
        CREATE TABLE IF NOT EXISTS lending_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            subscription_id INTEGER NOT NULL REFERENCES lending_subscriptions(id),
            delivery_mode TEXT NOT NULL DEFAULT 'offline',
            delivery_address TEXT NOT NULL DEFAULT '',
            contact_phone TEXT NOT NULL DEFAULT '',
            contact_name TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Requested',
            admin_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        for table,fields in additions.items():
            have={r[1] for r in c.execute('PRAGMA table_info('+table+')')}
            for name,definition in fields.items():
                if name not in have:c.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')
        schema_path = root / 'schema.sql'
        if not schema_path.exists():
            schema_path = root.parent / 'schema.sql'
        if not schema_path.exists():
            schema_path = root.parent.parent / 'schema.sql'
        c.executescript(schema_path.read_text())
        if not c.execute("SELECT 1 FROM schema_updates WHERE version='v17'").fetchone():
            c.execute('UPDATE lending_plans SET duration_days=MAX(1,months*30)')
            c.execute('UPDATE lending_subscriptions SET book_limit_snapshot=(SELECT book_limit FROM lending_plans WHERE id=lending_subscriptions.plan_id) WHERE book_limit_snapshot=0')
            for b in c.execute('SELECT id,stock FROM books').fetchall():
                for n in range(max(0,b['stock'])):
                    c.execute('INSERT INTO copies17(book_id,barcode) VALUES(?,?)',(b['id'],f'BB-{b["id"]:06d}-{n+1:04d}'))
            for loan in c.execute("SELECT id,book_id FROM lending_loans WHERE status='Issued'").fetchall():
                copy=c.execute("INSERT INTO copies17(book_id,barcode,status) VALUES(?,?,'Borrowed')",(loan['book_id'],f'BB-LEGACY-LOAN-{loan["id"]}')).lastrowid
                c.execute('UPDATE lending_loans SET copy_id=? WHERE id=?',(copy,loan['id']))
            c.execute("INSERT INTO schema_updates VALUES('v17')")
        c.commit()

        # Seed membership plans (6 rows: tier x duration) only if missing
        if c.execute("SELECT COUNT(*) FROM lending_plans WHERE tier!=''").fetchone()[0] == 0:
            benefits_text = "Online Portal Access\nAcademic Worksheets\nThe Book Buddy Times\nBeyond School Activities\nGames\nContribute to Magazine"
            default_plans = [
                ('Solo Explorer - 2 Months', 2, 60, 'Solo Explorer', 'Summer Special', '', 800.0, 2, 8, benefits_text, '2 Months Summer Special membership for 1 reader (2 books at a time).', 1, 'Membership', 14, 1),
                ('Family Pack / Elite - 2 Months', 2, 60, 'Family Pack / Elite', 'Summer Special', '', 1400.0, 4, 16, benefits_text, '2 Months Summer Special membership for family (4 books at a time).', 1, 'Membership', 14, 1),
                ('Solo Explorer - 3 Months', 3, 90, 'Solo Explorer', 'Regular', '', 1100.0, 2, 12, benefits_text, '3 Months Regular membership for 1 reader (2 books at a time).', 1, 'Membership', 14, 1),
                ('Family Pack / Elite - 3 Months', 3, 90, 'Family Pack / Elite', 'Regular', '', 2000.0, 4, 24, benefits_text, '3 Months Regular membership for family (4 books at a time).', 1, 'Membership', 14, 1),
                ('Solo Explorer - 9 Months', 9, 270, 'Solo Explorer', 'Academic Year', 'BEST VALUE', 3000.0, 2, 36, benefits_text, '9 Months Academic Year membership for 1 reader (2 books at a time).', 1, 'Membership', 14, 1),
                ('Family Pack / Elite - 9 Months', 9, 270, 'Family Pack / Elite', 'Academic Year', 'BEST VALUE', 5500.0, 4, 72, benefits_text, '9 Months Academic Year membership for family (4 books at a time).', 1, 'Membership', 14, 1),
            ]
            for p in default_plans:
                c.execute('''INSERT INTO lending_plans(name, months, duration_days, tier, tagline, badge, amount, book_limit, total_books, benefits, description, is_active, kind, loan_days, renewal_limit)
                             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', p)
            c.commit()

        # Seed site_content defaults for delivery and service modes if missing
        delivery_defaults = {
            'membership_delivery_fee_monthly': '350',
            'membership_delivery_area': 'Gandhi Nagar, Saligramam and surrounding areas (within 5 km)',
            'membership_delivery_day': 'Fixed pick-up & drop on designated weekday (e.g. Saturday)',
            'membership_pickup_address': 'Gandhi Nagar, Saligramam, Chennai',
        }
        for k, v in delivery_defaults.items():
            c.execute("INSERT OR IGNORE INTO site_content(content_key, content_value) VALUES(?, ?)", (k, v))
        c.commit()

    with app.app_context():
        db().executescript("""DROP TRIGGER IF EXISTS new_book_inventory17;""")
        db().commit()
    with app.app_context():
        c=db()
        if next(r for r in c.execute('PRAGMA table_info(lending_loans)') if r['name']=='subscription_id')['notnull']:
            c.commit()
            c.execute('PRAGMA foreign_keys=OFF')
            try:
                c.execute('BEGIN IMMEDIATE')
                definition=c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='lending_loans'").fetchone()[0]
                definition=re.sub(r'CREATE TABLE(?: IF NOT EXISTS)? ["`]?lending_loans["`]?', 'CREATE TABLE lending_loans18', definition, count=1, flags=re.I)
                definition=re.sub(r'(subscription_id\s+INTEGER)\s+NOT NULL', r'\1', definition, flags=re.I)
                objects=[r[0] for r in c.execute("SELECT sql FROM sqlite_master WHERE tbl_name='lending_loans' AND type IN ('index','trigger') AND sql IS NOT NULL")]
                c.execute(definition)
                columns=','.join('"'+r['name']+'"' for r in c.execute('PRAGMA table_info(lending_loans)'))
                c.execute(f'INSERT INTO lending_loans18 ({columns}) SELECT {columns} FROM lending_loans')
                c.execute('DROP TABLE lending_loans')
                c.execute('ALTER TABLE lending_loans18 RENAME TO lending_loans')
                for sql in objects:c.execute(sql)
                if c.execute('PRAGMA foreign_key_check').fetchone():raise RuntimeError('Loan migration found inconsistent references; changes rolled back.')
                c.commit()
            except Exception:
                c.rollback();raise
            finally:c.execute('PRAGMA foreign_keys=ON')
        c.execute("UPDATE auth_tokens17 SET used=1 WHERE purpose='verify'")
        c.execute("UPDATE mail_queue17 SET status='Cancelled' WHERE subject='BookBuddy account verify' AND status='Pending'")
        c.commit()
    from management import MODELS,BOOLS
    MODELS['books']=('Books','books','title author isbn publisher edition collection age_group language price stock description image_path is_active archived audience')
    BOOLS.update({'archived', 'is_active'})

    def rows(sql,args=()): return [dict(r) for r in db().execute(sql,args)]
    def user(): return db().execute('SELECT * FROM users WHERE id=? AND is_active=1',(session.get('user_id'),)).fetchone()
    def staff():
        return db().execute('SELECT * FROM admin_users WHERE id=? AND is_active=1',(session.get('admin_id'),)).fetchone()
    def privileged(): return bool(staff() and staff()['role'] in {'super_admin','org_admin'})
    def require_staff(*roles):
        a=staff()
        if not a:abort(401,'Sign in with your staff account.')
        if a['role'] not in {'super_admin','org_admin',*roles}:abort(403,'Your staff role cannot access this operation.')
        return a
    def require_user():
        u=user()
        if not u:abort(401,'Sign in to continue.')
        if not u['dob']:abort(403,'Complete your profile first.')
        if (years_old(u['dob'],today()) or 0)<18 and not u['guardian_verified']:abort(403,'Guardian approval is required.')
        return u
    def sub(uid):
        return db().execute("""SELECT s.*,p.name,p.loan_days,p.renewal_limit,p.fine_daily_paise,
            s.book_limit_snapshot AS book_limit
            FROM lending_subscriptions s JOIN lending_plans p ON p.id=s.plan_id
            WHERE s.user_id=? AND s.status IN ('Active','Scheduled') AND s.starts_on<=? AND s.expires_on>=? ORDER BY s.expires_on DESC LIMIT 1""",(uid,today().isoformat(),today().isoformat())).fetchone()
    def borrowing_policy(uid):
        active=sub(uid)
        if active:return dict(active)
        return {'id':None, 'book_limit':int(os.environ.get('ACCOUNT_BOOK_LIMIT','2')),
                'loan_days':int(os.environ.get('ACCOUNT_LOAN_DAYS','14')), 'renewal_limit':1,
                'fine_daily_paise':0}
    def audit(action): db().execute('INSERT INTO admin_audit(admin_id,action) VALUES(?,?)',(session.get('admin_id'),action[:1000]))
    def notify(uid,title,body='',url='/members/dashboard/',dedupe=None):
        result=db().execute('INSERT OR IGNORE INTO notifications17(user_id,title,body,url,dedupe) VALUES(?,?,?,?,?)',(uid,title,body,url,dedupe))
        if result.rowcount and os.environ.get('EMAIL_NOTIFICATIONS')=='1':
            recipient=db().execute('SELECT email FROM users WHERE id=? AND is_active=1',(uid,)).fetchone()
            if recipient:queue_mail(recipient['email'],title,body+'\n'+os.environ.get('PUBLIC_BASE_URL','').rstrip('/')+url)
    def page(template,title,**kw):return render('portal/'+template,'account',page_title=title,**kw)
    def desk(template,title,**kw):
        from management import MODELS
        return render_template('workspace/portal/'+template+'.html',title=title,active='v17',admin=dict(staff()),models=MODELS,**kw)
    def limit(bucket,max_count=30,seconds=60):
        key=hashlib.sha256(bucket.encode()).hexdigest();now=int(time.time())
        db().execute('INSERT INTO rate_limits17(bucket,count,expires_at) VALUES(?,1,?) ON CONFLICT(bucket) DO UPDATE SET count=CASE WHEN expires_at<? THEN 1 ELSE count+1 END,expires_at=CASE WHEN expires_at<? THEN excluded.expires_at ELSE expires_at END',(key,now+seconds,now,now))
        result=db().execute('SELECT count FROM rate_limits17 WHERE bucket=?',(key,)).fetchone()[0]
        db().commit()
        if result>max_count:abort(429,'Too many requests. Please try again later.')

    @app.before_request
    def policy17():
        path=request.path
        if path=='/members/verify-email/' or path.startswith('/accounts/verify/'):abort(404)
        if path.strip('/').split('/')[0].startswith(('game','legacy')) or request.endpoint=='log_play':abort(404)
        if session.get('admin_id') and not staff():session.pop('admin_id',None)
        if session.get('user_id'):
            current=user()
            if not current or session.get('auth_version',0)!=current['session_version']:
                session.clear()
                return redirect('/accounts/login/')
        if request.method=='POST' and path in {'/accounts/login/','/account/login/','/login/','/admin/login/','/accounts/signup/','/account/signup/','/signup/','/accounts/password/reset/','/account/password/reset/'}:
            auth_limit = 5 if os.environ.get('DEMO_MODE','0').strip().lower() in ('1','true','yes','on') else 20
            limit('auth:'+str(request.remote_addr),auth_limit,300)
        if path in {'/admin/manage/plans/','/admin/lending-plans/'} and request.method=='GET': return redirect('/admin/plans17/')
        if path=='/admin/manage/memberships/' and request.method=='GET': return redirect('/admin/membership-desk/')
        if path=='/plans-legacy/':return redirect('/membership-options/')
        if path.startswith('/membership/request/') and request.method=='POST':abort(409,'Choose a current plan from Membership options.')
        if request.method=='POST' and path.startswith(('/admin/manage/plans/','/admin/manage/memberships/','/admin/lending-plans/')):abort(409,'Use Plans & promotions or Membership approvals to update subscriptions.')
        if path.startswith('/admin/') and path not in {'/admin/login/','/admin/logout/'} and staff():
            role=staff()['role']
            if role not in {'super_admin','org_admin'}:
                allowed={'librarian':('/admin/library-center/','/admin/library17/','/admin/lending/','/admin/support17/','/admin/manage/books/'), 'instructor':('/admin/support17/',), 'support':('/admin/support17/',)}.get(role,())
                if path=='/admin/dashboard/':return redirect({'librarian':'/admin/library17/','instructor':'/admin/support17/','support':'/admin/support17/'}.get(role, '/admin/support17/'))
                if not path.startswith(allowed) and path!='/admin/password/':abort(403,'Your staff role cannot access this section.')
        if path.startswith(('/media/users/','/media/interns/','/media/resumes/','/static/resumes/')) and not privileged():abort(404)
        # Deny raw legacy media documents unless entitled; new files are outside public directories.
        if path.startswith(('/media/','/static/uploads/')) and Path(path).suffix.lower() not in {'.png','.jpg','.jpeg','.webp','.gif','.svg','.ico','.css','.js','.woff','.woff2','.ttf'}:
            if not staff():
                u=require_user()
                if not sub(u['id']):abort(403,'An active membership is needed for this resource.')
    hooks=app.before_request_funcs[None];hooks.remove(policy17);hooks.insert(0,policy17)
    # Validate CSRF before any legacy dispatcher can process a POST.
    secure=next(f for f in hooks if f.__name__=='secure_mutations');hooks.remove(secure);hooks.insert(0,secure)

    @app.context_processor
    def context17():
        u=user();a=staff()
        from management import MODELS
        return {'models':MODELS,'staff_role17':a['role'] if a else '', 'notifications_count17': db().execute('SELECT COUNT(*) FROM notifications17 WHERE user_id=? AND is_read=0',(u['id'],)).fetchone()[0] if u else 0,'today17':today().isoformat(), 'borrowing_policy18':borrowing_policy(u['id']) if u else None}

    @app.after_request
    def headers17(response):
        response.headers.setdefault('Referrer-Policy','strict-origin-when-cross-origin')
        response.headers.setdefault('X-Frame-Options','SAMEORIGIN')
        response.headers.setdefault('Permissions-Policy','camera=(), microphone=(self), geolocation=()')
        if session.get('user_id') or session.get('admin_id'):response.headers['Cache-Control']='private, no-store'
        return response

    for error_code in (400,401,403,409,413,429,503):
        def friendly_error(error):
            if request.path.startswith('/api/') or request.is_json or request.accept_mimetypes.best=='application/json':
                return jsonify(ok=False, error={"code": f"HTTP_{error.code}", "message": getattr(error, "description", str(error))}), error.code
            return page('error', {400:'Check your request',401:'Sign in to continue',403:'Access required',409:'Action could not be completed',413:'File too large',429:'Please try again shortly',503:'Service temporarily unavailable'}.get(error.code,'Request error'),message=error.description,error_code=error.code),error.code
        app.register_error_handler(error_code,friendly_error)

    def sync_stock(book_id):
        available=db().execute("SELECT COUNT(*) FROM copies17 WHERE book_id=? AND status='Available'",(book_id,)).fetchone()[0]
        db().execute('UPDATE books SET stock=?,available_copies=? WHERE id=?',(available,available,book_id))
    def loan_request(book_id):
        u=require_user();c=db();c.execute('BEGIN IMMEDIATE')
        s=borrowing_policy(u['id']);b=c.execute('SELECT * FROM books WHERE id=? AND archived=0',(book_id,)).fetchone()
        if not b:abort(404)
        if not age_matches(b['age_group'],years_old(u['dob'],today())):abort(403,'Choose an age-appropriate book.')
        if c.execute("SELECT 1 FROM lending_loans WHERE user_id=? AND book_id=? AND status IN ('Requested','Issued')",(u['id'],book_id)).fetchone():abort(409,'You already have an active request or loan for this title.')
        count=c.execute("SELECT COUNT(*) FROM lending_loans WHERE user_id=? AND status IN ('Requested','Issued')",(u['id'],)).fetchone()[0]
        if count>=s['book_limit']:abort(409,'Your borrowing limit has been reached.')
        queue=c.execute("SELECT * FROM reservations17 WHERE book_id=? AND status='Waiting' ORDER BY id LIMIT 1",(book_id,)).fetchone()
        available=c.execute("SELECT COUNT(*) FROM copies17 WHERE book_id=? AND status='Available'",(book_id,)).fetchone()[0]
        pending=c.execute("SELECT COUNT(*) FROM lending_loans WHERE book_id=? AND status='Requested'",(book_id,)).fetchone()[0]
        if available<=pending or (queue and queue['user_id']!=u['id']):
            c.execute('INSERT OR IGNORE INTO reservations17(user_id,book_id) VALUES(?,?)',(u['id'],book_id));c.commit()
            flash('Added to the reservation queue. Your position is shown in My library.','success')
        else:
            c.execute('INSERT INTO lending_loans(user_id,book_id,subscription_id,fine_daily_paise) VALUES(?,?,?,?)',(u['id'],book_id,s['id'],s['fine_daily_paise']))
            c.execute("UPDATE reservations17 SET status='Fulfilled' WHERE user_id=? AND book_id=? AND status='Waiting'",(u['id'],book_id));c.commit();flash('Book requested. The library will confirm collection.','success')
        c.execute("INSERT OR IGNORE INTO admin_notifications(kind,title,body,url,source_key) VALUES('borrowing','Book request received',?,'/admin/lending/',?)",(u['name']+' · '+b['title'],'borrow:'+str(u['id'])+':'+str(book_id)+':'+secrets.token_hex(6)));c.commit()
        return redirect('/members/library/')
    app.view_functions['request_book16']=loan_request

    def loan_action(loan_id):
        a=require_staff('librarian');action=textfield('action');c=db();c.execute('BEGIN IMMEDIATE')
        loan=c.execute('SELECT * FROM lending_loans WHERE id=?',(loan_id,)).fetchone()
        if not loan:abort(404)
        note=textfield('admin_note',600)
        if action=='issue' and loan['status']=='Requested':
            s=borrowing_policy(loan['user_id'])
            borrower=c.execute('SELECT * FROM users WHERE id=? AND is_active=1',(loan['user_id'],)).fetchone()
            if not borrower or not borrower['dob'] or ((years_old(borrower['dob'],today()) or 0)<18 and not borrower['guardian_verified']):abort(409,'Member profile or guardian approval is incomplete.')
            count=c.execute("SELECT COUNT(*) FROM lending_loans WHERE user_id=? AND status='Issued'",(loan['user_id'],)).fetchone()[0]
            if count>=s['book_limit']:abort(409,'Borrowing limit reached.')
            raw=request.form.get('due_date','') or (today()+timedelta(days=s['loan_days'])).isoformat()
            try:due=date.fromisoformat(raw)
            except ValueError:abort(400,'Invalid due date.')
            if not today()<due<=today()+timedelta(days=s['loan_days']):abort(400,'Due date must fit the permitted loan period.')
            copy=c.execute("SELECT id FROM copies17 WHERE book_id=? AND status='Available' ORDER BY id LIMIT 1",(loan['book_id'],)).fetchone()
            if not copy:abort(409,'No available physical copy.')
            c.execute("UPDATE copies17 SET status='Borrowed' WHERE id=?",(copy['id'],))
            c.execute("UPDATE lending_loans SET status='Issued',copy_id=?,issued_at=?,due_date=?,issued_by=?,admin_note=? WHERE id=?",(copy['id'],today().isoformat(),due.isoformat(),a['id'],note,loan_id))
        elif action in {'return','lost','damaged'} and loan['status']=='Issued':
            state={'return':'Available','lost':'Lost','damaged':'Damaged'}[action]
            c.execute('UPDATE copies17 SET status=? WHERE id=?',(state,loan['copy_id']))
            c.execute("UPDATE lending_loans SET status=?,returned_at=?,returned_by=?,admin_note=? WHERE id=?",('Returned' if action=='return' else state,today().isoformat(),a['id'],note,loan_id))
            days=max(0,(today()-date.fromisoformat(loan['due_date'])).days)
            fine=days*loan['fine_daily_paise']
            if fine:c.execute('INSERT INTO fines17(loan_id,amount_paise,reason) VALUES(?,?,?)',(loan_id,fine,f'{days} overdue days'))
            if action!='return':
                replacement=paise(request.form.get('replacement_amount','0'))
                if replacement:c.execute('INSERT INTO fines17(loan_id,amount_paise,reason) VALUES(?,?,?)',(loan_id,replacement,state+' replacement charge'))
            queue=c.execute("SELECT user_id FROM reservations17 WHERE book_id=? AND status='Waiting' ORDER BY id LIMIT 1",(loan['book_id'],)).fetchone()
            if queue and state=='Available':notify(queue[0],'A reserved title is available','Open My library to request the book.','/members/library/')
        elif action=='reject' and loan['status']=='Requested':
            c.execute("UPDATE lending_loans SET status='Rejected',admin_note=? WHERE id=?",(note,loan_id))
        elif action=='cancel' and loan['status']=='Requested':
            c.execute("UPDATE lending_loans SET status='Cancelled',admin_note=? WHERE id=?",(note,loan_id))
        else:abort(409,'This action is not valid for the current loan state.')
        if loan['request_id']:
            rem = c.execute("SELECT COUNT(*) FROM lending_loans WHERE request_id=? AND status='Requested'", (loan['request_id'],)).fetchone()[0]
            if rem == 0:
                issued_cnt = c.execute("SELECT COUNT(*) FROM lending_loans WHERE request_id=? AND status='Issued'", (loan['request_id'],)).fetchone()[0]
                new_req_status = 'Issued' if issued_cnt > 0 else ('Rejected' if action == 'reject' else 'Cancelled')
                c.execute("UPDATE lending_requests SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_req_status, loan['request_id']))
        sync_stock(loan['book_id']);audit(f'Loan {loan_id}: {action}');notify(loan['user_id'],'Library record updated',f'Loan #{loan_id}: {action}','/members/library/');c.commit()
        flash('Library record updated.','success');return redirect('/admin/lending/')
    app.view_functions['admin_loan_status16']=loan_action

    @app.get('/members/library/')
    def my_library17():
        u=require_user()
        return page('library','My library',loans=rows('SELECT l.*,b.title,c.barcode FROM lending_loans l JOIN books b ON b.id=l.book_id LEFT JOIN copies17 c ON c.id=l.copy_id WHERE l.user_id=? ORDER BY l.id DESC',(u['id'],)),reservations=rows("SELECT r.*,b.title,(SELECT COUNT(*) FROM reservations17 q WHERE q.book_id=r.book_id AND q.status='Waiting' AND q.id<=r.id) position FROM reservations17 r JOIN books b ON b.id=r.book_id WHERE r.user_id=? AND r.status='Waiting'",(u['id'],)),fines=rows('SELECT f.*,b.title FROM fines17 f JOIN lending_loans l ON l.id=f.loan_id JOIN books b ON b.id=l.book_id WHERE l.user_id=?',(u['id'],)))

    @app.post('/members/loans/<int:lid>/renew/')
    def renew17(lid):
        u=require_user();c=db();c.execute('BEGIN IMMEDIATE');s=borrowing_policy(u['id'])
        loan=c.execute("SELECT * FROM lending_loans WHERE id=? AND user_id=? AND status='Issued'",(lid,u['id'])).fetchone()
        if not loan:abort(404)
        if loan['return_requested_at'] or loan['due_date']<today().isoformat() or loan['renewals']>=s['renewal_limit']:abort(409,'Renewal is not eligible. Check return status, due date and renewal limit.')
        if c.execute("SELECT 1 FROM reservations17 WHERE book_id=? AND status='Waiting'",(loan['book_id'],)).fetchone():abort(409,'Another member is waiting for this title.')
        due=(date.fromisoformat(loan['due_date'])+timedelta(days=s['loan_days'])).isoformat()
        c.execute('UPDATE lending_loans SET due_date=?,renewals=renewals+1 WHERE id=?',(due,lid));notify(u['id'],'Book renewed','New due date: '+due,'/members/library/');c.commit()
        flash('Book renewed.','success');return redirect('/members/library/')

    @app.post('/members/loans/<int:lid>/return-request/')
    def return_request18(lid):
        u=require_user();c=db();c.execute('BEGIN IMMEDIATE')
        loan=c.execute("SELECT * FROM lending_loans WHERE id=? AND user_id=? AND status='Issued'",(lid,u['id'])).fetchone()
        if not loan:abort(404)
        if loan['return_requested_at']:abort(409,'Your return request is already awaiting staff confirmation.')
        c.execute('UPDATE lending_loans SET return_requested_at=? WHERE id=?',(today().isoformat(),lid))
        c.execute("INSERT OR IGNORE INTO admin_notifications(kind,title,body,url,source_key) VALUES('borrowing','Book return requested',?,'/admin/lending/',?)",(u['name']+' · Loan #'+str(lid),'return-request:'+str(lid)))
        c.commit();flash('Return requested. Bring the book to the library; staff will confirm receipt.','success')
        return redirect('/members/library/')

    @app.post('/members/reservations/<int:rid>/cancel/')
    def cancel_reservation17(rid):
        u=require_user();db().execute("UPDATE reservations17 SET status='Cancelled' WHERE id=? AND user_id=? AND status='Waiting'",(rid,u['id']));db().commit();return redirect('/members/library/')

    @app.route('/admin/library17/',methods=['GET','POST'])
    def inventory17():
        require_staff('librarian')
        if request.method=='POST':
            action=textfield('action');c=db();c.execute('BEGIN IMMEDIATE')
            if action=='branch' and c.execute('SELECT 1 FROM branches17 WHERE name=?',(textfield('name',100,True),)).fetchone():abort(409,'Branch already exists.')
            if action=='branch':c.execute('INSERT INTO branches17(name,address) VALUES(?,?)',(textfield('name',100,True),textfield('address',500)))
            elif action=='copy':
                bid=integer(request.form.get('book_id'),1);barcode=textfield('barcode',80,True)
                if not c.execute('SELECT 1 FROM books WHERE id=?',(bid,)).fetchone():abort(404)
                branch=integer(request.form.get('branch_id') or 0) or None
                if branch and not c.execute('SELECT 1 FROM branches17 WHERE id=?',(branch,)).fetchone():abort(400,'Unknown branch.')
                if c.execute('SELECT 1 FROM copies17 WHERE barcode=?',(barcode,)).fetchone():abort(409,'Barcode already exists.')
                c.execute('INSERT INTO copies17(book_id,barcode,branch_id,location) VALUES(?,?,?,?)',(bid,barcode,branch,textfield('location',100)));sync_stock(bid)
            elif action=='state':
                copy=c.execute('SELECT * FROM copies17 WHERE id=?',(integer(request.form.get('copy_id'),1),)).fetchone()
                status=textfield('status')
                if not copy:abort(404)
                if copy['status']=='Borrowed' or status not in {'Available','Lost','Damaged','Maintenance'}:abort(409,'Use the lending desk for borrowed copies.')
                c.execute('UPDATE copies17 SET status=? WHERE id=?',(status,copy['id']));sync_stock(copy['book_id'])
            elif action=='fine':
                fine=c.execute('SELECT * FROM fines17 WHERE id=?',(integer(request.form.get('fine_id'),1),)).fetchone();amount=paise(request.form.get('amount','0'))
                if not fine or amount<=0 or amount>fine['amount_paise']-fine['paid_paise']:abort(400,'Invalid fine payment.')
                c.execute('INSERT INTO fine_payments17(fine_id,amount_paise,reference,admin_id) VALUES(?,?,?,?)',(fine['id'],amount,textfield('reference',100,True),staff()['id']))
                c.execute('UPDATE fines17 SET paid_paise=paid_paise+? WHERE id=?',(amount,fine['id']))
            else:abort(400)
            audit('Library inventory: '+action);c.commit();flash('Saved.','success');return redirect('/admin/library17/')
        q=request.args.get('q','')[:100];state=request.args.get('status','');pn=integer(request.args.get('page',1),1)
        copies=rows("SELECT c.*,b.title,br.name AS branch FROM copies17 c JOIN books b ON b.id=c.book_id LEFT JOIN branches17 br ON br.id=c.branch_id WHERE (b.title LIKE ? OR c.barcode LIKE ?) AND (?='' OR c.status=?) ORDER BY c.id DESC LIMIT 51 OFFSET ?",('%'+q+'%','%'+q+'%',state,state,(pn-1)*50))
        return desk('inventory','Library inventory',copies=copies[:50],has_next=len(copies)>50,pn=pn,q=q,status=state,books=rows('SELECT id,title FROM books ORDER BY title'),branches=rows('SELECT * FROM branches17'),fines=rows('SELECT f.*,u.name,b.title FROM fines17 f JOIN lending_loans l ON l.id=f.loan_id JOIN users u ON u.id=l.user_id JOIN books b ON b.id=l.book_id WHERE f.paid_paise<f.amount_paise'))

    for endpoint in ('account_login','account_login_short','account_signup','account_signup_short'):
        original=app.view_functions[endpoint]
        def auth_wrapper(original=original):
            result=original()
            if session.get('user_id'):
                current=user()
                if current:session['auth_version']=current['session_version']
            return result
        app.view_functions[endpoint]=auth_wrapper
    # The /login/ and /signup/ decorators may have their own legacy endpoint names.
    app.view_functions['account_login_short']=app.view_functions['account_login']
    app.view_functions['account_signup_short']=app.view_functions['account_signup']









    def upload(field):
        f=request.files.get(field)
        if not f or not f.filename:return None
        name=secure_filename(f.filename);ext=Path(name).suffix.lower()
        if ext not in {'.pdf','.png','.jpg','.jpeg','.txt','.csv','.docx','.pptx'}:abort(400,'Use PDF, PNG, JPG, TXT, CSV, DOCX or PPTX.')
        blob=f.read(8*1024*1024+1)
        if not blob or len(blob)>8*1024*1024:abort(400,'File must be between 1 byte and 8 MB.')
        if ext=='.pdf' and not blob.startswith(b'%PDF-'):abort(400,'Invalid PDF.')
        if ext in {'.docx','.pptx'} and not blob.startswith(b'PK'):abort(400,'Invalid Office document.')
        if ext in {'.png','.jpg','.jpeg'}:
            from PIL import Image, UnidentifiedImageError
            try:
                with Image.open(io.BytesIO(blob)) as im:im.verify()
            except Exception:abort(400,'Invalid image.')
        if ext in {'.txt','.csv'}:
            try:blob.decode('utf-8')
            except UnicodeError:abort(400,'Text files must use UTF-8.')
        key=secrets.token_hex(24)+ext;(private/key).write_bytes(blob)
        return key,name





    def activate(sid,payment_status,admin_id=None):
        s=db().execute('SELECT s.*,p.duration_days,p.book_limit,p.learning_access,p.ai_access FROM lending_subscriptions s JOIN lending_plans p ON p.id=s.plan_id WHERE s.id=?',(sid,)).fetchone()
        if not s:abort(404)
        if s['status'] in {'Active','Scheduled'}:return
        if s['status']!='Pending':abort(409,'Membership is no longer pending.')
        last=db().execute("SELECT MAX(expires_on) FROM lending_subscriptions WHERE user_id=? AND status IN ('Active','Scheduled') AND expires_on>=?",(s['user_id'],today().isoformat())).fetchone()[0]
        start=date.fromisoformat(last)+timedelta(days=1) if last else today()
        duration=s['duration_snapshot'] or s['duration_days'];end=start+timedelta(days=duration-1)
        db().execute("UPDATE lending_subscriptions SET status=?,starts_on=?,expires_on=?,payment_status=?,approved_by=?,book_limit_snapshot=?,learning_snapshot=?,ai_snapshot=? WHERE id=?",('Scheduled' if start>today() else 'Active',start.isoformat(),end.isoformat(),payment_status,admin_id,s['book_limit_snapshot'],s['learning_snapshot'],s['ai_snapshot'],sid))
        notify(s['user_id'],'Membership confirmed',f'Valid {start} to {end}.','/members/dashboard/')

    def request_plan(plan_id):
        u=user()
        if not u:
            flash('Please log in or sign up to complete your subscription.','info')
            next_url=f'/membership/?plan_id={plan_id}'
            return redirect(url_for('account_login',next=next_url))
        c=db();c.execute('BEGIN IMMEDIATE')
        p=c.execute('SELECT * FROM lending_plans WHERE id=? AND is_active=1',(plan_id,)).fetchone()
        if not p:
            c.rollback();abort(404,'Selected plan not found.')
        pd=dict(p)

        service_mode=request.form.get('service_mode','offline').strip().lower()
        if service_mode not in {'offline','online'}:service_mode='offline'

        ud=dict(u) if u else {}
        child_name=textfield('child_name',150) or ud.get('name','')
        child_dob=textfield('child_dob',20) or ud.get('dob','')
        student_grade=textfield('student_grade',50)
        parent_name=textfield('parent_name',150) or ud.get('guardian_name','') or ud.get('name','')
        email=textfield('email',150) or ud.get('email','')
        phone=textfield('phone',50) or ud.get('phone','')

        address_flat=textfield('address_flat',255)
        address_street=textfield('address_street',255)
        address_city=textfield('address_city',100) or 'Chennai'
        address_state=textfield('address_state',100) or 'Tamil Nadu'
        address_pincode=textfield('address_pincode',20)
        address_country='India'
        referral_code=textfield('referral_code',50)

        # Server validation
        if service_mode=='online' and (not address_flat or not address_street or not address_pincode):
            c.rollback();flash('Please provide your complete delivery address for doorstep delivery.','danger')
            return redirect(f'/membership/?plan_id={plan_id}')

        settings_fee=c.execute("SELECT content_value FROM site_content WHERE content_key='membership_delivery_fee_monthly'").fetchone()
        try: monthly_rate=float(settings_fee[0]) if settings_fee and settings_fee[0] else 350.0
        except ValueError: monthly_rate=350.0

        months=int(pd.get('months') or max(1,pd['duration_days']//30))
        delivery_fee=(monthly_rate * months) if service_mode=='online' else 0.0
        base_amount=float(pd['amount'])
        amount=paise(base_amount + delivery_fee)

        coupon=None;code=textfield('coupon',50)
        if code:
            coupon=c.execute("SELECT * FROM coupons17 WHERE code=? AND is_active=1 AND (expires_on='' OR expires_on>=?)",(code,today().isoformat())).fetchone()
            if not coupon:c.rollback();abort(400,'Coupon is invalid or expired.')
            used=c.execute('SELECT COUNT(*) FROM coupon_uses17 WHERE coupon_id=?',(coupon['id'],)).fetchone()[0]
            if coupon['max_uses'] and used>=coupon['max_uses']:c.rollback();abort(409,'Coupon usage limit reached.')
            amount=(amount*(100-coupon['percent'])+50)//100

        total_final = amount / 100

        # Update user's profile with contact / DOB if missing
        c.execute("""UPDATE users SET
            phone=CASE WHEN (phone IS NULL OR phone='') AND ?!='' THEN ? ELSE phone END,
            dob=CASE WHEN (dob IS NULL OR dob='') AND ?!='' THEN ? ELSE dob END,
            guardian_name=CASE WHEN (guardian_name IS NULL OR guardian_name='') AND ?!='' THEN ? ELSE guardian_name END
            WHERE id=?""", (phone,phone,child_dob,child_dob,parent_name,parent_name,u['id']))

        existing=c.execute("SELECT id FROM lending_subscriptions WHERE user_id=? AND status='Pending' ORDER BY id DESC LIMIT 1",(u['id'],)).fetchone()
        if existing:
            sid=existing[0]
            c.execute("""UPDATE lending_subscriptions SET
                plan_id=?,amount=?,delivery_fee=?,service_mode=?,child_name=?,child_dob=?,
                student_grade=?,parent_name=?,email=?,phone=?,address_flat=?,address_street=?,
                address_city=?,address_state=?,address_pincode=?,address_country=?,referral_code=?,
                duration_snapshot=?,book_limit_snapshot=?,learning_snapshot=?,ai_snapshot=?
                WHERE id=?""", (
                    plan_id,total_final,delivery_fee,service_mode,child_name,child_dob,
                    student_grade,parent_name,email,phone,address_flat,address_street,
                    address_city,address_state,address_pincode,address_country,referral_code,
                    pd['duration_days'],pd['book_limit'],pd['learning_access'],pd['ai_access'],sid
                ))
        else:
            sid=c.execute("""INSERT INTO lending_subscriptions(
                user_id,plan_id,amount,delivery_fee,service_mode,child_name,child_dob,
                student_grade,parent_name,email,phone,address_flat,address_street,
                address_city,address_state,address_pincode,address_country,referral_code,
                duration_snapshot,book_limit_snapshot,learning_snapshot,ai_snapshot
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                u['id'],plan_id,total_final,delivery_fee,service_mode,child_name,child_dob,
                student_grade,parent_name,email,phone,address_flat,address_street,
                address_city,address_state,address_pincode,address_country,referral_code,
                pd['duration_days'],pd['book_limit'],pd['learning_access'],pd['ai_access']
            )).lastrowid

        if coupon:c.execute('INSERT OR IGNORE INTO coupon_uses17 VALUES(?,?)',(coupon['id'],sid))
        if total_final==0:activate(sid,'Free plan')
        c.commit();return redirect(f'/members/billing/{sid}/')
    app.view_functions['request_plan16']=request_plan

    @app.route('/membership/subscribe/',methods=['POST'])
    def membership_subscribe():
        pid=integer(request.form.get('plan_id',0),1)
        return request_plan(pid)

    def subscription_review(sub_id):
        a=require_staff();c=db();c.execute('BEGIN IMMEDIATE');s=c.execute('SELECT * FROM lending_subscriptions WHERE id=?',(sub_id,)).fetchone()
        if not s:abort(404)
        action=textfield('action');note=textfield('admin_note',600)
        if action=='approve':
            if c.execute("SELECT 1 FROM payments17 WHERE subscription_id=? AND order_id IS NOT NULL AND status IN ('Pending','Failed')",(sub_id,)).fetchone():abort(409,'An online order exists. Reconcile it before recording an offline payment.')
            if s['amount']>0 and request.form.get('payment_status')!='Paid - confirmed by staff':abort(400,'Confirm the actual offline payment before activation.')
            activate(sub_id,'Paid - confirmed by staff' if s['amount'] else 'Free plan',a['id'])
        elif action=='reject' and s['status']=='Pending':
            if c.execute("SELECT 1 FROM payments17 WHERE subscription_id=? AND order_id IS NOT NULL",(sub_id,)).fetchone():abort(409,'A payment order exists. Reconcile it before rejecting the request.')
            c.execute("UPDATE lending_subscriptions SET status='Rejected',admin_note=? WHERE id=?",(note,sub_id));c.execute('DELETE FROM coupon_uses17 WHERE subscription_id=?',(sub_id,))
        elif action in {'suspend','cancel'} and s['status'] in {'Active','Scheduled'}:
            if not note:abort(400,'Record a reason for this change.')
            c.execute('UPDATE lending_subscriptions SET status=?,admin_note=? WHERE id=?',('Suspended' if action=='suspend' else 'Cancelled',note,sub_id))
        else:abort(409,'Invalid membership transition.')
        audit(f'Membership {sub_id}: {action}');notify(s['user_id'],'Membership updated',action,'/members/dashboard/');c.commit();flash('Membership updated.','success');return redirect('/admin/membership-desk/')
    app.view_functions['review_subscription16']=subscription_review

    @app.route('/admin/plans17/',methods=['GET','POST'])
    def plans_admin17():
        require_staff()
        if request.method=='POST':
            action=textfield('action')
            if action=='coupon':
                code=textfield('code',50,True).upper();expiry=textfield('expires_on',10)
                if expiry:
                    try:date.fromisoformat(expiry)
                    except ValueError:abort(400,'Invalid expiry date.')
                if db().execute('SELECT 1 FROM coupons17 WHERE code=?',(code,)).fetchone():abort(409,'Coupon code already exists.')
                db().execute('INSERT INTO coupons17(code,percent,max_uses,expires_on) VALUES(?,?,?,?)',(code,integer(request.form.get('percent'),1,100),integer(request.form.get('max_uses',0)),expiry))
            elif action=='settings':
                for k in ['membership_delivery_fee_monthly','membership_delivery_area','membership_delivery_day','membership_pickup_address']:
                    if k in request.form:
                        db().execute('INSERT INTO site_content(content_key,content_value) VALUES(?,?) ON CONFLICT(content_key) DO UPDATE SET content_value=excluded.content_value',(k, request.form[k].strip()))
                audit('Membership delivery settings updated');db().commit();flash('Delivery and service settings saved.','success');return redirect('/admin/plans17/')
            else:
                pid=integer(request.form.get('id') or 0);name=textfield('name',150,True);days=integer(request.form.get('duration_days',30),1,3650)
                tier=textfield('tier',100);tagline=textfield('tagline',100);badge=textfield('badge',50)
                total_books=integer(request.form.get('total_books',0),0,1000)
                months=integer(request.form.get('months',max(1,days//30)),1,36)
                benefits=textfield('benefits',4000)
                values=(name,days,integer(request.form.get('book_limit',2),0,100),paise(request.form.get('amount',0))/100,integer(request.form.get('loan_days',14),1,365),integer(request.form.get('renewal_limit',1),0,10),paise(request.form.get('fine_daily',0)),0,0,textfield('description',2000),int(request.form.get('is_active')=='1'),tier,tagline,badge,total_books,months,benefits)
                duplicate=db().execute('SELECT 1 FROM lending_plans WHERE name=? AND id!=?',(name,pid)).fetchone()
                if duplicate:abort(409,'Another plan has that name.')
                if pid:
                    result=db().execute('UPDATE lending_plans SET name=?,duration_days=?,book_limit=?,amount=?,loan_days=?,renewal_limit=?,fine_daily_paise=?,learning_access=?,ai_access=?,description=?,is_active=?,tier=?,tagline=?,badge=?,total_books=?,months=?,benefits=? WHERE id=?',(*values,pid))
                    if not result.rowcount:abort(404)
                else:db().execute("INSERT INTO lending_plans(name,duration_days,book_limit,amount,loan_days,renewal_limit,fine_daily_paise,learning_access,ai_access,description,is_active,tier,tagline,badge,total_books,months,benefits,kind) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'Membership')",values)
            audit('Membership configuration: '+action);db().commit();flash('Saved.','success');return redirect('/admin/plans17/')
        edit=db().execute('SELECT * FROM lending_plans WHERE id=?',(integer(request.args.get('edit',0)),)).fetchone()
        settings_map={r['content_key']:r['content_value'] for r in db().execute('SELECT * FROM site_content').fetchall()}
        return desk('plans','Plans & promotions',plans=rows('SELECT * FROM lending_plans ORDER BY months, amount, id'),edit=dict(edit) if edit else {},coupons=rows('SELECT * FROM coupons17 ORDER BY id DESC'),settings=settings_map)

    def render_membership_page():
        c=db()
        plans_raw=[dict(r) for r in c.execute('SELECT * FROM lending_plans WHERE is_active=1 ORDER BY months ASC, amount ASC, id ASC').fetchall()]
        settings_map={r['content_key']:r['content_value'] for r in c.execute('SELECT * FROM site_content').fetchall()}

        delivery_fee_monthly=350
        try: delivery_fee_monthly=int(float(settings_map.get('membership_delivery_fee_monthly','350')))
        except ValueError: pass
        delivery_area=settings_map.get('membership_delivery_area','Gandhi Nagar, Saligramam and surrounding areas (within 5 km)')
        delivery_day=settings_map.get('membership_delivery_day','Fixed pick-up & drop on designated weekday (e.g. Saturday)')
        pickup_address=settings_map.get('membership_pickup_address','Gandhi Nagar, Saligramam, Chennai')

        # Group by duration months (e.g. 2, 3, 9)
        months_set=[]
        for p in plans_raw:
            m=p.get('months') or max(1,p['duration_days']//30)
            if m not in months_set:months_set.append(m)
        months_set.sort()

        duration_groups=[]
        for m in months_set:
            group_plans=[p for p in plans_raw if (p.get('months') or max(1,p['duration_days']//30))==m]
            solo=next((p for p in group_plans if 'solo' in (p.get('tier') or '').lower()), None)
            if not solo:solo=next((p for p in group_plans if p.get('book_limit')==2), group_plans[0] if group_plans else None)

            family=next((p for p in group_plans if any(k in (p.get('tier') or '').lower() for k in ['family','elite'])), None)
            if not family:family=next((p for p in group_plans if p.get('book_limit')==4), group_plans[-1] if len(group_plans)>1 else None)

            tagline=next((p['tagline'] for p in group_plans if p.get('tagline')), ('Summer Special' if m==2 else 'Regular' if m==3 else 'Academic Year'))
            badge=next((p['badge'] for p in group_plans if p.get('badge')), ('BEST VALUE' if m==9 else ''))
            benefits_raw=next((p['benefits'] for p in group_plans if p.get('benefits')), '')
            if not benefits_raw:
                benefits_list=['Online Portal Access','Academic Worksheets','The Book Buddy Times','Beyond School Activities','Games','Contribute to Magazine']
            else:
                benefits_list=[b.strip() for b in benefits_raw.split('\n') if b.strip()]

            duration_groups.append({
                'months': m,
                'label': f'{m} Months',
                'tagline': tagline,
                'badge': badge,
                'is_best_value': bool(badge and 'best' in badge.lower()) or (m==9),
                'solo_plan': solo,
                'family_plan': family,
                'solo_price': int(solo['amount']) if solo else 0,
                'family_price': int(family['amount']) if family else 0,
                'solo_books': (solo.get('total_books') or (8 if m==2 else 12 if m==3 else 36)) if solo else 0,
                'family_books': (family.get('total_books') or (16 if m==2 else 24 if m==3 else 72)) if family else 0,
                'benefits': benefits_list,
                'plans': group_plans,
            })

        import json
        plans_json=json.dumps([{
            'id': p['id'],
            'name': p['name'],
            'months': p.get('months') or max(1,p['duration_days']//30),
            'tier': p.get('tier') or ('Family Pack / Elite' if p['book_limit']>2 else 'Solo Explorer'),
            'amount': float(p['amount']),
            'book_limit': p['book_limit'],
            'total_books': p.get('total_books') or 0,
            'tagline': p.get('tagline') or '',
            'badge': p.get('badge') or '',
        } for p in plans_raw])

        current_u=user()
        return render('membership','library',
                      duration_groups=duration_groups,
                      plans=plans_raw,
                      plans_json=plans_json,
                      delivery_fee_monthly=delivery_fee_monthly,
                      delivery_area=delivery_area,
                      delivery_day=delivery_day,
                      pickup_address=pickup_address,
                      prefill_user=dict(current_u) if current_u else None,
                      page_title='Membership & Plans | Book Buddy')

    app.add_url_rule('/membership/', 'membership_page', render_membership_page, methods=['GET'])
    app.view_functions['membership']=render_membership_page

    @app.route('/members/billing/<int:sid>/',methods=['GET','POST'])
    def billing17(sid):
        u=require_user();s=db().execute('SELECT s.*,p.name FROM lending_subscriptions s JOIN lending_plans p ON p.id=s.plan_id WHERE s.id=? AND s.user_id=?',(sid,u['id'])).fetchone()
        if not s:abort(404)
        if request.method=='POST':
            if s['status']!='Pending':return redirect(f'/members/billing/{sid}/')
            from payments import razorpay_request
            c=db();c.execute('BEGIN IMMEDIATE')
            payment=c.execute('SELECT * FROM payments17 WHERE subscription_id=? ORDER BY id DESC LIMIT 1',(sid,)).fetchone()
            if not payment:
                try:order=razorpay_request('POST','orders',{'amount':paise(s['amount']),'currency':'INR','receipt':f'BB-M-{sid}','notes':{'subscription_id':str(sid)}})
                except RuntimeError as e:c.rollback();flash(str(e),'danger');return redirect(f'/members/billing/{sid}/')
                if not isinstance(order,dict) or not re.fullmatch(r'order_[A-Za-z0-9]+',str(order.get('id',''))) or order.get('amount')!=paise(s['amount']) or order.get('currency')!='INR':
                    c.rollback();flash('Could not prepare a valid payment order. Please try again.','danger');return redirect(f'/members/billing/{sid}/')
                c.execute('INSERT INTO payments17(subscription_id,order_id,amount_paise) VALUES(?,?,?)',(sid,order['id'],paise(s['amount'])))
            c.commit();return redirect(f'/members/billing/{sid}/')
        payment=db().execute('SELECT * FROM payments17 WHERE subscription_id=? ORDER BY id DESC LIMIT 1',(sid,)).fetchone()
        return page('billing','Membership billing',subscription=dict(s),payment=dict(payment) if payment else None,key=os.environ.get('RAZORPAY_KEY_ID',''))

    def settle(order_id,payment):
        c=db();c.execute('BEGIN IMMEDIATE');p=c.execute('SELECT * FROM payments17 WHERE order_id=?',(order_id,)).fetchone()
        if not p:abort(404)
        if payment.get('status')!='captured' or payment.get('order_id')!=order_id or payment.get('amount')!=p['amount_paise'] or payment.get('currency')!='INR' or not re.fullmatch(r'pay_[A-Za-z0-9]+',str(payment.get('id',''))):abort(400,'Payment has not been captured with the expected amount and currency.')
        if p['status'] in {'Paid','Refunded'}:
            if p['payment_id']!=payment['id']:abort(409,'Payment does not match the recorded transaction.')
            c.rollback();return
        if c.execute('SELECT 1 FROM payments17 WHERE payment_id=? AND id!=?',(payment['id'],p['id'])).fetchone():abort(409,'Payment already reconciled.')
        c.execute("UPDATE payments17 SET status='Paid',payment_id=? WHERE id=?",(payment['id'],p['id']));activate(p['subscription_id'],'Paid - Razorpay');c.commit()

    @app.post('/members/billing/<int:sid>/verify/')
    def verify_payment17(sid):
        u=require_user();p=db().execute('SELECT p.* FROM payments17 p JOIN lending_subscriptions s ON s.id=p.subscription_id WHERE s.id=? AND s.user_id=? ORDER BY p.id DESC LIMIT 1',(sid,u['id'])).fetchone()
        if not p:abort(404)
        pid=textfield('razorpay_payment_id',100);secret=os.environ.get('RAZORPAY_KEY_SECRET','');signature=textfield('razorpay_signature',100)
        expected=hmac.new(secret.encode(),(p['order_id']+'|'+pid).encode(),hashlib.sha256).hexdigest()
        if not secret or not re.fullmatch(r'pay_[A-Za-z0-9]+',pid) or not hmac.compare_digest(expected,signature):abort(400,'Invalid payment signature.')
        from payments import razorpay_request
        try:payment=razorpay_request('GET','payments/'+pid)
        except RuntimeError:abort(503,'Payment confirmation is delayed. Please check this page again shortly.')
        settle(p['order_id'],payment);return redirect(f'/members/billing/{sid}/')

    @app.post('/payments/membership/webhook/')
    def membership_webhook17():
        secret=os.environ.get('RAZORPAY_MEMBERSHIP_WEBHOOK_SECRET','');raw=request.get_data()
        expected=hmac.new(secret.encode(),raw,hashlib.sha256).hexdigest()
        if not secret or not hmac.compare_digest(expected,request.headers.get('X-Razorpay-Signature','')):abort(400,'Invalid webhook signature.')
        data=request.get_json(silent=True)
        if not isinstance(data,dict) or not isinstance(data.get('payload',{}),dict):abort(400,'Invalid webhook payload.')
        event=data.get('event','');payload=data.get('payload',{})
        payment_block=payload.get('payment',{})
        if not isinstance(payment_block,dict):abort(400,'Invalid payment payload.')
        payment=payment_block.get('entity',{})
        if not isinstance(payment,dict):abort(400,'Invalid payment entity.')
        if event in {'payment.captured','order.paid'}:
            # The same Razorpay account may also send event orders to this endpoint.
            if db().execute('SELECT 1 FROM payments17 WHERE order_id=?',(payment.get('order_id'),)).fetchone():settle(payment.get('order_id'),payment)
        elif event=='payment.failed':
            db().execute("UPDATE payments17 SET status='Failed' WHERE order_id=? AND status!='Paid'",(payment.get('order_id'),));db().commit()
        elif event=='refund.processed':
            refund_block=payload.get('refund',{})
            if not isinstance(refund_block,dict) or not isinstance(refund_block.get('entity',{}),dict):abort(400,'Invalid refund payload.')
            refund=refund_block.get('entity',{});c=db();c.execute('BEGIN IMMEDIATE')
            p=c.execute('SELECT * FROM payments17 WHERE payment_id=?',(refund.get('payment_id'),)).fetchone()
            # Only a verified full refund revokes benefits automatically; partial refunds need staff review.
            if p and refund.get('amount')==p['amount_paise']:
                c.execute("UPDATE payments17 SET status='Refunded' WHERE id=?",(p['id'],));c.execute("UPDATE lending_subscriptions SET status='Cancelled',payment_status='Refunded' WHERE id=?",(p['subscription_id'],))
            c.commit()
        return jsonify(received=True)

    @app.get('/members/notifications/')
    def notifications17():
        u=require_user();return page('notifications','Notifications',items=rows('SELECT * FROM notifications17 WHERE user_id=? ORDER BY id DESC LIMIT 100',(u['id'],)))
    @app.post('/members/notifications/read/')
    def notifications_read17():
        u=require_user();db().execute('UPDATE notifications17 SET is_read=1 WHERE user_id=?',(u['id'],));db().commit();return redirect('/members/notifications/')

    def conversation(cid):
        conv=db().execute('SELECT c.*,u.name,a.name staff_name FROM conversations17 c JOIN users u ON u.id=c.user_id LEFT JOIN admin_users a ON a.id=c.assigned_id WHERE c.id=?',(cid,)).fetchone()
        if not conv:abort(404)
        a=staff();u=user()
        if a:
            if not privileged() and not (a['role']=='support' or conv['assigned_id']==a['id']):abort(403)
        elif not u or (conv['user_id']!=u['id'] and not db().execute('SELECT 1 FROM conversation_members17 WHERE conversation_id=? AND user_id=?',(cid,u['id'])).fetchone()):abort(404)
        return conv

    @app.route('/members/support/',methods=['GET','POST'])
    def support17():
        u=require_user()
        if request.method=='POST':
            limit('ticket:'+str(u['id']),5,3600)
            cid=db().execute('INSERT INTO conversations17(user_id,subject,category) VALUES(?,?,?)',(u['id'],textfield('subject',200,True),textfield('category',50) or 'Support')).lastrowid
            db().execute('INSERT INTO messages17(conversation_id,sender_user,body) VALUES(?,?,?)',(cid,u['id'],textfield('message',5000,True)));db().commit();return redirect(f'/members/support/{cid}/')
        return page('support','Human support',conversations=rows('SELECT * FROM conversations17 WHERE user_id=? OR id IN (SELECT conversation_id FROM conversation_members17 WHERE user_id=?) ORDER BY id DESC',(u['id'],u['id'])))

    @app.route('/members/support/<int:cid>/',methods=['GET','POST'])
    @app.route('/admin/support17/<int:cid>/',methods=['GET','POST'])
    def conversation17(cid):
        conv=conversation(cid);a=staff();u=user()
        if request.method=='POST':
            limit('chat:'+('a'+str(a['id']) if a else 'u'+str(u['id'])),30,60)
            action=textfield('action')
            if action=='status':
                require_staff('support');status=textfield('status')
                if status not in {'Open','Closed','Escalated'}:abort(400)
                assigned=integer(request.form.get('assigned_id') or 0) or None
                if assigned and not db().execute('SELECT 1 FROM admin_users WHERE id=? AND is_active=1',(assigned,)).fetchone():abort(400,'Unknown staff member.')
                db().execute('UPDATE conversations17 SET status=?,assigned_id=? WHERE id=?',(status,assigned,cid));audit(f'Support conversation {cid}: {status}')
            elif action=='report':
                if not u:abort(403)
                db().execute("UPDATE conversations17 SET status='Escalated' WHERE id=?",(cid,));notify(u['id'],'Conversation reported','The support team will review your report.','/members/support/')
            else:
                if conv['status']=='Closed':abort(409,'This conversation is closed. Open a new support request.')
                body=textfield('message',5000);attachment=upload('attachment')
                if not body and not attachment:abort(400,'Enter a message or attach a file.')
                key,name=attachment or ('','')
                db().execute('INSERT INTO messages17(conversation_id,sender_user,sender_admin,body,file_key,file_name) VALUES(?,?,?,?,?,?)',(cid,None if a else u['id'],a['id'] if a else None,body,key,name))
                if a:
                    recipients={conv['user_id']} | {r[0] for r in db().execute('SELECT user_id FROM conversation_members17 WHERE conversation_id=?',(cid,))}
                    for recipient in recipients:notify(recipient,'Support replied',conv['subject'],f'/members/support/{cid}/')
            db().commit();return redirect(('/admin/support17/' if a else '/members/support/')+str(cid)+'/')
        messages=rows('SELECT m.*,a.name admin_name,u.name user_name FROM messages17 m LEFT JOIN admin_users a ON a.id=m.sender_admin LEFT JOIN users u ON u.id=m.sender_user WHERE m.conversation_id=? ORDER BY m.id',(cid,))
        kw=dict(conversation=dict(conv),messages=messages,is_staff=bool(a),staff_options=rows('SELECT id,name FROM admin_users WHERE is_active=1') if a else [])
        return desk('chat','Human support',**kw) if a else page('chat','Human support',**kw)

    @app.route('/members/support/<int:cid>/feed/',methods=['GET','POST'])
    @app.route('/admin/support17/<int:cid>/feed/',methods=['GET','POST'])
    def chat_feed17(cid):
        conv=conversation(cid);a=staff();actor='a'+str(a['id']) if a else 'u'+str(user()['id']);now=int(time.time())
        if request.method=='POST':
            db().execute('INSERT INTO presence17 VALUES(?,?,?,?) ON CONFLICT(conversation_id,actor) DO UPDATE SET last_seen=excluded.last_seen,typing_until=excluded.typing_until',(cid,actor,now,now+5 if request.form.get('typing')=='1' else 0))
            db().execute("UPDATE messages17 SET read_at=CURRENT_TIMESTAMP WHERE conversation_id=? AND read_at='' AND "+('sender_user IS NOT NULL' if a else 'sender_admin IS NOT NULL'),(cid,));db().commit()
        after=integer(request.args.get('after',0));q=request.args.get('q','')[:100]
        messages=rows('SELECT m.id,m.body,m.file_name,m.sender_user,m.sender_admin,m.created_at,m.read_at,a.name admin_name,u.name user_name FROM messages17 m LEFT JOIN admin_users a ON a.id=m.sender_admin LEFT JOIN users u ON u.id=m.sender_user WHERE conversation_id=? AND m.id>? AND m.body LIKE ? ORDER BY m.id LIMIT 100',(cid,after,'%'+q+'%'))
        peers=rows('SELECT last_seen,typing_until FROM presence17 WHERE conversation_id=? AND actor!=?',(cid,actor))
        return jsonify(messages=messages,online=any(p['last_seen']>now-20 for p in peers),typing=any(p['typing_until']>now for p in peers),read_through=db().execute("SELECT COALESCE(MAX(id),0) FROM messages17 WHERE conversation_id=? AND read_at!=''",(cid,)).fetchone()[0],status=conv['status'])

    @app.get('/members/support/files/<int:mid>/')
    @app.get('/admin/support17/files/<int:mid>/')
    def chat_file17(mid):
        m=db().execute('SELECT * FROM messages17 WHERE id=?',(mid,)).fetchone()
        if not m or not m['file_key']:abort(404)
        conversation(m['conversation_id']);return send_file(private/m['file_key'],as_attachment=True,download_name=m['file_name'],max_age=0)


    @app.get('/admin/support17/')
    def support_admin17():
        a=require_staff('support','instructor','librarian');q=request.args.get('q','')[:100];status=request.args.get('status','')
        return desk('support','Support conversations',q=q,status=status,conversations=rows("SELECT c.*,u.name,u.email,a.name staff_name FROM conversations17 c JOIN users u ON u.id=c.user_id LEFT JOIN admin_users a ON a.id=c.assigned_id WHERE (?=1 OR c.assigned_id=?) AND (?='' OR c.status=?) AND (c.subject LIKE ? OR u.name LIKE ?) ORDER BY c.id DESC LIMIT 100",(int(privileged() or a['role']=='support'),a['id'],status,status,'%'+q+'%','%'+q+'%')))


    def queue_mail(recipient,subject,body):db().execute('INSERT INTO mail_queue17(recipient,subject,body) VALUES(?,?,?)',(recipient,subject,body))
    def token_email(u,purpose):
        if os.environ.get('DEMO_MODE','0').strip().lower() in ('1','true','yes','on'):
            abort(503,'Account email links are not configured in demo mode. Please contact the library.')
        raw=secrets.token_urlsafe(32);hashed=hashlib.sha256(raw.encode()).hexdigest();db().execute('INSERT INTO auth_tokens17 VALUES(?,?,?,?,0)',(hashed,u['id'],purpose,int(time.time())+3600))
        base=os.environ.get('PUBLIC_BASE_URL','').rstrip('/')
        if not base.startswith('https://'):abort(503,'Account email links are not configured. Please contact the library.')
        path='/accounts/password/new/' if purpose=='reset' else '/accounts/verify/'
        queue_mail(u['email'],'BookBuddy account '+purpose,'Open this one-time link within 60 minutes:\n'+base+path+raw+'/\nIf you did not request this, ignore this email.')
    def reset_request17():
        if request.method=='POST':
            email=textfield('email',254,True).lower();u=db().execute('SELECT * FROM users WHERE email=? AND is_active=1',(email,)).fetchone()
            if u:token_email(u,'reset');db().commit()
            flash('If this email matches an account, password reset instructions will be sent.','info');return redirect('/accounts/password/reset/')
        return page('reset','Reset your password',finish=False)
    app.view_functions['account_reset_password']=reset_request17;app.view_functions['account_reset_password_short']=reset_request17

    @app.route('/accounts/password/new/<token>/',methods=['GET','POST'])
    def reset_finish17(token):
        hashed=hashlib.sha256(token.encode()).hexdigest();t=db().execute("SELECT * FROM auth_tokens17 WHERE token_hash=? AND purpose='reset' AND used=0 AND expires_at>?",(hashed,int(time.time()))).fetchone()
        if not t:abort(400,'This link has expired or has already been used.')
        if request.method=='POST':
            password=request.form.get('password','')
            if not 12<=len(password)<=128 or password!=request.form.get('confirm_password'):abort(400,'Use a matching password of 12–128 characters.')
            c=db();c.execute('BEGIN IMMEDIATE');changed=c.execute('UPDATE auth_tokens17 SET used=1 WHERE token_hash=? AND used=0 AND expires_at>?',(hashed,int(time.time())))
            if changed.rowcount!=1:abort(409,'This reset link has already been used.')
            c.execute('UPDATE users SET password_hash=?,session_version=session_version+1 WHERE id=?',(generate_password_hash(password),t['user_id']));c.execute("UPDATE auth_tokens17 SET used=1 WHERE user_id=? AND purpose='reset'",(t['user_id'],));c.commit();session.clear();flash('Password changed. Sign in with your new password.','success');return redirect('/accounts/login/')
        return page('reset','Choose a new password',finish=True)

    @app.route('/admin/staff17/',methods=['GET','POST'])
    def staff_admin17():
        a=require_staff()
        if a['role']!='super_admin':abort(403,'Only the platform owner manages staff roles.')
        if request.method=='POST':
            sid=integer(request.form.get('id') or 0);role=textfield('role');name=textfield('name',150,True);email=textfield('email',254,True).lower()
            if role not in ROLES or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):abort(400,'Invalid role or email.')
            enabled=int(request.form.get('is_active')=='1')
            if sid==a['id'] and (role!='super_admin' or not enabled):abort(400,'You cannot remove your own platform-owner access.')
            if db().execute('SELECT 1 FROM admin_users WHERE email=? AND id!=?',(email,sid)).fetchone():abort(409,'This staff email is already in use.')
            if sid:
                db().execute('UPDATE admin_users SET role=?,name=?,email=?,is_active=? WHERE id=?',(role,name,email,enabled,sid))
            else:
                password=request.form.get('password','')
                if not 12<=len(password)<=128:abort(400,'Staff passwords must be 12–128 characters.')
                db().execute('INSERT INTO admin_users(email,name,password_hash,role,is_active) VALUES(?,?,?,?,?)',(email,name,generate_password_hash(password),role,enabled))
            audit(f'Staff role update: {email} / {role}');db().commit();flash('Staff account saved.','success');return redirect('/admin/staff17/')
        return desk('staff','Staff & permissions',people=rows('SELECT id,name,email,role,is_active FROM admin_users ORDER BY id'),roles=sorted(ROLES))

    @app.get('/admin/reports17/')
    def reports17():
        require_staff();counts={name:db().execute(sql).fetchone()[0] for name,sql in {
            'Members':'SELECT COUNT(*) FROM users','Available copies':"SELECT COUNT(*) FROM copies17 WHERE status='Available'",'Active loans':"SELECT COUNT(*) FROM lending_loans WHERE status='Issued'",'Overdue loans':"SELECT COUNT(*) FROM lending_loans WHERE status='Issued' AND due_date<'"+today().isoformat()+"'",'Open support':"SELECT COUNT(*) FROM conversations17 WHERE status!='Closed'"}.items()}
        financial=db().execute("SELECT COALESCE(SUM(amount),0) total FROM lending_subscriptions WHERE payment_status IN ('Paid - Razorpay','Paid - confirmed by staff')").fetchone()[0]
        audits=rows('SELECT l.*,a.name FROM admin_audit l LEFT JOIN admin_users a ON a.id=l.admin_id ORDER BY l.id DESC LIMIT 100')
        if request.args.get('export')=='loans':
            output=io.StringIO();writer=csv.writer(output);writer.writerow(['Loan','Member','Book','Barcode','Status','Issued','Due','Returned'])
            for r in db().execute('SELECT l.id,u.name,b.title,c.barcode,l.status,l.issued_at,l.due_date,l.returned_at FROM lending_loans l JOIN users u ON u.id=l.user_id JOIN books b ON b.id=l.book_id LEFT JOIN copies17 c ON c.id=l.copy_id ORDER BY l.id DESC'):
                writer.writerow([("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v) for v in r])
            return Response(output.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=bookbuddy-loans.csv'})
        return desk('reports','Reports & audit',counts=counts,revenue=financial,audits=audits,mail=rows('SELECT status,COUNT(*) count FROM mail_queue17 GROUP BY status'))

    @app.cli.command('maintenance')
    def maintenance17():
        c=db();day=today().isoformat()
        c.execute("UPDATE lending_subscriptions SET status='Expired' WHERE status IN ('Active','Scheduled') AND expires_on<?",(day,))
        c.execute("UPDATE lending_subscriptions SET status='Active' WHERE status='Scheduled' AND starts_on<=? AND expires_on>=?",(day,day))
        for l in c.execute("SELECT l.*,b.title FROM lending_loans l JOIN books b ON b.id=l.book_id WHERE l.status='Issued' AND l.due_date<=?",((today()+timedelta(days=2)).isoformat(),)).fetchall():
            notify(l['user_id'],'Book return reminder',l['title']+' is due '+l['due_date'],'/members/library/',f'loan:{l["id"]}:{day}')
        for s in c.execute("SELECT * FROM lending_subscriptions WHERE status='Active' AND expires_on<=?",((today()+timedelta(days=7)).isoformat(),)).fetchall():
            notify(s['user_id'],'Membership renewal reminder','Your membership ends '+s['expires_on'],'/membership-options/',f'renew:{s["id"]}:{day}')
        c.execute('DELETE FROM rate_limits17 WHERE expires_at<?',(int(time.time()),));c.execute('DELETE FROM auth_tokens17 WHERE expires_at<?',(int(time.time())-86400,));c.commit();print('Expiry checks and deduplicated reminders completed.')

    @app.cli.command('send-mail')
    def send_mail17():
        if os.environ.get('DEMO_MODE','0').strip().lower() in ('1','true','yes','on'):
            raise RuntimeError('Email sending is not configured in demo mode.')
        # Exactly one message per cron invocation: comfortably below a 100/hour host cap.
        host=os.environ.get('SMTP_HOST','');sender=os.environ.get('SMTP_FROM','')
        if not host or not sender:raise RuntimeError('Configure SMTP_HOST and SMTP_FROM first.')
        c=db();c.execute('BEGIN IMMEDIATE');m=c.execute("SELECT * FROM mail_queue17 WHERE status='Pending' AND attempts<5 ORDER BY id LIMIT 1").fetchone()
        if not m:c.rollback();print('No pending mail.');return
        c.execute("UPDATE mail_queue17 SET status='Sending',attempts=attempts+1 WHERE id=?",(m['id'],));c.commit()
        msg=EmailMessage();msg['From']=sender;msg['To']=m['recipient'];msg['Subject']=m['subject'];msg.set_content(m['body'])
        try:
            import ssl
            port=int(os.environ.get('SMTP_PORT','587'));tls=ssl.create_default_context()
            smtp=smtplib.SMTP_SSL(host,port,timeout=20,context=tls) if port==465 else smtplib.SMTP(host,port,timeout=20)
            with smtp:
                if port!=465:smtp.starttls(context=tls)
                if os.environ.get('SMTP_USERNAME'):smtp.login(os.environ['SMTP_USERNAME'],os.environ.get('SMTP_PASSWORD',''))
                smtp.send_message(msg)
            c.execute("UPDATE mail_queue17 SET status='Sent' WHERE id=?",(m['id'],));print('One queued message sent.')
        except Exception:
            c.execute("UPDATE mail_queue17 SET status=CASE WHEN attempts>=5 THEN 'Failed' ELSE 'Pending' END WHERE id=?",(m['id'],));print('Mail delivery failed; inspect SMTP configuration.')
        c.commit()

    @app.cli.command('backup')
    def backup17():
        default_backup = Path('/tmp/backups') if is_vercel else root/'instance'/'backups'
        destination=Path(os.environ.get('BOOK_BUDDY_BACKUP_DIR', default_backup))
        try:
            destination.mkdir(parents=True,exist_ok=True)
        except OSError:
            pass
        path=destination/('bookbuddy-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.sqlite3')
        with sqlite3.connect(path) as output:db().backup(output)
        path.chmod(0o600);print('Database backup created:',path)

    def home17():
        return render('home','home')
    app.view_functions['index']=home17
    @app.context_processor
    def dashboard_extras17():
        u=user()
        if not u:return {}
        return {'account_borrowing18':borrowing_policy(u['id'])}

    app.extensions['bookbuddy17']={'sub':sub,'settle':settle}
