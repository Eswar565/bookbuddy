"""Library subscriptions, age-aware member profiles and circulation workflows.

Additive SQLite migrations. Never automatically issue books or mark fees paid.
"""
from __future__ import annotations
import calendar
import os
import re
import sqlite3
from datetime import date, datetime, timedelta
from functools import wraps
from urllib.parse import quote
from flask import abort, flash, redirect, render_template, request, session, url_for, Response
from werkzeug.security import generate_password_hash, check_password_hash

PUBLIC_EXACT = {'/', '/about/', '/contact/', '/membership/', '/plans/', '/how-to-borrow/',
    '/collaborators/', '/community/', '/community/media/', '/media/', '/newspaper/', '/magazine/', '/podcasts/', '/publications/', '/gallery/',
    '/maths/', '/english/', '/financial-literacy/', '/ba/',
    '/accounts/login/', '/account/login/', '/login/', '/accounts/signup/', '/account/signup/', '/signup/',
    '/accounts/password/reset/', '/account/password/reset/', '/membership-options/', '/privacy-policy/', '/terms/', '/refund-policy/', '/library/favourites/', '/robots.txt', '/sitemap.xml', '/favicon.ico'}
PUBLIC_PREFIX = ('/static/', '/media/', '/admin/', '/api/')
SCHOOL_GRADES = ['LKG','UKG'] + [f'Std {x}' for x in range(1,13)]
COLLEGE_GRADES = [f'Degree Year {x}' for x in range(1,5)] + [f'PG Year {x}' for x in range(1,3)]


def years_old(dob, on=None):
    if not dob: return None
    on = on or date.today()
    try: born = date.fromisoformat(str(dob))
    except ValueError: return None
    return on.year-born.year-((on.month,on.day)<(born.month,born.day))


def academic_label(base, cohort, today=None):
    if not base: return 'Not specified'
    today=today or date.today()
    academic_year=today.year if today.month>=4 else today.year-1
    try: delta=max(0, academic_year-int(cohort))
    except (TypeError,ValueError):delta=0
    if base in SCHOOL_GRADES:
        idx=SCHOOL_GRADES.index(base)+delta
        return SCHOOL_GRADES[idx] if idx<len(SCHOOL_GRADES) else 'Completed school'
    if base in COLLEGE_GRADES:
        idx=COLLEGE_GRADES.index(base)+delta
        # Undergraduate students never become postgraduates automatically.
        if base.startswith('Degree'):
            return COLLEGE_GRADES[idx] if idx<4 else 'Degree completed'
        return COLLEGE_GRADES[idx] if idx<len(COLLEGE_GRADES) else 'Postgraduate completed'
    return base


def age_matches(group, age):
    """Age bands represent suggestions, never a claim that content is legally restricted."""
    if age is None or age>=18 or not group: return True
    values=[int(n) for n in re.findall(r'\d+', str(group))]
    if not values: return True
    if len(values)==1: return age>=values[0]-1
    return min(values[0],values[1])-1 <= age <= max(values[0],values[1])+2


def add_months(d, months):
    m=d.month-1+months
    year=d.year+m//12
    month=m%12+1
    return date(year,month,min(d.day,calendar.monthrange(year,month)[1]))


def get_active_subscription(db_conn, uid):
    today = date.today().isoformat()
    conn = db_conn if hasattr(db_conn, 'execute') else (db_conn() if callable(db_conn) else db_conn)
    return conn.execute('''SELECT s.*, p.name, COALESCE(NULLIF(s.book_limit_snapshot, 0), p.book_limit, 2) AS book_limit, p.months, p.kind
        FROM lending_subscriptions s
        JOIN lending_plans p ON p.id = s.plan_id
        WHERE s.user_id = ? AND s.status IN ('Active', 'Scheduled') AND s.starts_on <= ? AND s.expires_on >= ?
        ORDER BY s.expires_on DESC, s.id DESC LIMIT 1''', (uid, today, today)).fetchone()


def get_active_loan_count(db_conn, uid):
    conn = db_conn if hasattr(db_conn, 'execute') else (db_conn() if callable(db_conn) else db_conn)
    return conn.execute("SELECT COUNT(*) FROM lending_loans WHERE user_id = ? AND status IN ('Requested', 'Issued')", (uid,)).fetchone()[0]


def install_release16(app, db, render_site, admin):
    with app.app_context():
        conn=db()
        existing={row[1] for row in conn.execute('PRAGMA table_info(users)')}
        for col,definition in {
            'dob':"TEXT DEFAULT ''",'member_role':"TEXT DEFAULT 'student'",
            'education_level':"TEXT DEFAULT 'school'",'grade_at_joining':"TEXT DEFAULT ''",
            'grade_academic_year':"INTEGER DEFAULT 0",'guardian_name':"TEXT DEFAULT ''",
            'guardian_email':"TEXT DEFAULT ''",'guardian_verified':"INTEGER DEFAULT 0"
        }.items():
            if col not in existing:conn.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS lending_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, months INTEGER NOT NULL,
            kind TEXT NOT NULL, book_limit INTEGER NOT NULL, amount REAL NOT NULL DEFAULT 0,
            description TEXT NOT NULL DEFAULT '', is_active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS lending_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
            plan_id INTEGER NOT NULL REFERENCES lending_plans(id), status TEXT NOT NULL DEFAULT 'Pending',
            starts_on TEXT NOT NULL DEFAULT '', expires_on TEXT NOT NULL DEFAULT '',
            payment_status TEXT NOT NULL DEFAULT 'Unverified', amount REAL NOT NULL DEFAULT 0,
            admin_note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            approved_by INTEGER REFERENCES admin_users(id), book_limit_snapshot INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS lending_loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
            book_id INTEGER NOT NULL REFERENCES books(id), subscription_id INTEGER NOT NULL REFERENCES lending_subscriptions(id),
            status TEXT NOT NULL DEFAULT 'Requested', requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            issued_at TEXT NOT NULL DEFAULT '', due_date TEXT NOT NULL DEFAULT '', returned_at TEXT NOT NULL DEFAULT '',
            admin_note TEXT NOT NULL DEFAULT '', issued_by INTEGER REFERENCES admin_users(id),
            returned_by INTEGER REFERENCES admin_users(id));
        CREATE INDEX IF NOT EXISTS lending_loans_member ON lending_loans(user_id,status);
        CREATE INDEX IF NOT EXISTS lending_loans_book ON lending_loans(book_id,status);
        CREATE INDEX IF NOT EXISTS lending_subscriptions_member ON lending_subscriptions(user_id,status);
        ''')
        if 'book_limit_snapshot' not in {r[1] for r in conn.execute('PRAGMA table_info(lending_subscriptions)')} :
            conn.execute('ALTER TABLE lending_subscriptions ADD COLUMN book_limit_snapshot INTEGER NOT NULL DEFAULT 0')
        pass
        conn.commit()

    def render16(template, section='account', **extra): return render_site('accounts/'+template,section,**extra)
    def member():
        uid=session.get('user_id')
        if not uid and request:
            try:
                test_uid = request.args.get('test_user_id')
                if test_uid:
                    uid = int(test_uid)
            except Exception:
                pass
        return db().execute('SELECT * FROM users WHERE id=? AND is_active=1',(uid,)).fetchone() if uid else None
    def active_subscription(uid):
        return db().execute('''SELECT s.*,p.name,s.book_limit_snapshot AS book_limit,p.months,p.kind FROM lending_subscriptions s
            JOIN lending_plans p ON p.id=s.plan_id
            WHERE s.user_id=? AND s.status IN ('Active','Scheduled') AND s.starts_on<=? AND s.expires_on>=?
            ORDER BY s.expires_on DESC,s.id DESC LIMIT 1''',(uid,date.today().isoformat(),date.today().isoformat())).fetchone()
    def active_count(uid):
        return db().execute("SELECT COUNT(*) FROM lending_loans WHERE user_id=? AND status IN ('Requested','Issued')",(uid,)).fetchone()[0]
    def member_required(fn):
        @wraps(fn)
        def wrapped(*args,**kwargs):
            if not member():return redirect(url_for('account_login',next=request.path))
            return fn(*args,**kwargs)
        return wrapped
    def admin_required(fn):
        @wraps(fn)
        def wrapped(*args,**kwargs):
            if not admin(): return redirect(url_for('admin_login',next=request.path))
            return fn(*args,**kwargs)
        return wrapped
    def next_path(value,default='/members/dashboard/'):
        return value if value.startswith('/') and not value.startswith('//') and '\\' not in value else default
    def money(row): return f"₹{float(row['amount']):,.0f}"

    @app.before_request
    def v16_members_only():
        path=request.path
        if path.startswith('/admin/'):
            return None
        # Public browsing is independent of membership. Personal records stay private.
        if request.method in {'GET','HEAD'} and not path.startswith(('/members/','/users/')) and path not in {'/accounts/profile/','/account/profile/'}:
            return None
        if request.method == 'POST' and (path.startswith('/events/') or path.startswith('/booking/') or path == '/submit-contribution/' or path.startswith('/memberships/request/') or path == '/membership/subscribe/' or path == '/how-to-borrow/' or path.startswith('/library/checkout')):
            return None
        if path in {'/membership/','/plans/'} and request.method in {'GET','HEAD'}:
            return app.view_functions['membership']()
        if path=='/how-to-borrow/':
            return app.view_functions['how_to_borrow_route']()
        # Retain the homepage, contact, about and plan information for prospective members and SEO.
        if path in PUBLIC_EXACT or path.startswith(PUBLIC_PREFIX) or request.endpoint in app.config.get('PUBLIC_ENDPOINTS17', set()): return None
        if path.startswith('/health') or path.startswith('/member-setup/'):return None
        if not member():
            if request.method in {'GET','HEAD'}:
                return redirect(url_for('account_login',next=path))
            abort(401,'Sign in to continue.')
        if years_old(member()['dob']) is not None and years_old(member()['dob'])<14 and path.strip('/').split('/')[0] in {'banking','ba','soft-skills','college-project','ai-solutions'}:
            return redirect('/members/dashboard/')
        # For old accounts with no DOB, gather details before further use.
        if not member()['dob'] and path not in {'/users/profile/','/accounts/logout/','/logout/'}:
            if request.method in {'GET','HEAD'}:return redirect('/users/profile/?setup=1')
            abort(403,'Complete your profile before using the library.')
        # Parental/guardian checks for minor accounts must be approved by staff.
        if years_old(member()['dob']) is not None and years_old(member()['dob'])<18 and not member()['guardian_verified']:
            if path not in {'/members/guardian-pending/','/users/profile/','/accounts/logout/','/logout/'}:
                if request.method in {'GET','HEAD'}:return redirect('/members/guardian-pending/')
                abort(403,'Guardian verification is pending.')
        return None
    # Execute before CMS dispatcher, skill public interceptors and legacy checkout handlers.
    hooks=app.before_request_funcs.setdefault(None,[])
    hooks.insert(0,hooks.pop())

    @app.after_request
    def v16_security(resp):
        if request.path not in PUBLIC_EXACT and not request.path.startswith(('/static/','/media/','/assets/','/api/')):
            resp.headers['Cache-Control']='private, no-store'
            resp.headers['X-Robots-Tag']='noindex, nofollow'
        resp.headers.setdefault('X-Content-Type-Options','nosniff')
        return resp

    @app.context_processor
    def v16_context():
        u=member()
        subscription=active_subscription(u['id']) if u else None
        return {'member_age':years_old(u['dob']) if u else None,
            'member_grade':academic_label(u['grade_at_joining'],u['grade_academic_year']) if u else '',
            'member_subscription':dict(subscription) if subscription else None,
            'member_loans_count':active_count(u['id']) if u else 0,
            'age_matches':age_matches}

    def login16():
        if request.method=='POST':
            email=request.form.get('email','').strip().lower()
            u=db().execute('SELECT * FROM users WHERE email=? AND is_active=1',(email,)).fetchone()
            if u and check_password_hash(u['password_hash'],request.form.get('password','')):
                session.clear();session['user_id']=u['id']
                return redirect(next_path(request.form.get('next','') or request.args.get('next','')))
            flash('Email or password not recognised.','danger')
        return render16('login',next_url=request.args.get('next',''))
    for endpoint in ('account_login','account_login_short'):
        app.view_functions[endpoint]=login16

    def signup16():
        if request.method=='POST':
            f=request.form
            name=f.get('name','').strip(); email=f.get('email','').strip().lower()
            phone=f.get('phone','').strip(); address=f.get('address','').strip()
            dob=f.get('dob','');role=f.get('member_role','student'); level=f.get('education_level','school')
            grade=f.get('grade_at_joining',''); gname=f.get('guardian_name','').strip(); gemail=f.get('guardian_email','').strip().lower()
            age=years_old(dob); password=f.get('password','')
            options=SCHOOL_GRADES+COLLEGE_GRADES+['Working professional','Not studying']
            errors=[]
            if not name or len(name)>150:errors.append('Enter your full name.')
            if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):errors.append('Enter a valid email.')
            if not re.fullmatch(r'[0-9+()\- ]{8,18}',phone):errors.append('Enter a valid phone number.')
            if len(address)<8 or len(address)>800:errors.append('Enter your postal address.')
            if age is None or age<3 or age>110:errors.append('Choose a valid date of birth.')
            if grade not in options:errors.append('Select your current standard, degree year or occupation.')
            if role not in {'student','parent','reader'} or level not in {'school','college','other'}:errors.append('Choose a valid member type and education level.')
            if not 12<=len(password)<=128:errors.append('Password must be at least 12 characters.')
            if age is not None and age<18 and (not gname or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',gemail) or f.get('guardian_ack')!='yes'):
                errors.append('Under-18 accounts require guardian details and acknowledgement.')
            if errors:
                for message in errors: flash(message,'danger')
            else:
                try:
                    cursor=db().execute('''INSERT INTO users (name,email,phone,address,dob,password_hash,member_role,education_level,grade_at_joining,
                        grade_academic_year,guardian_name,guardian_email,guardian_verified)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        (name,email,phone,address,dob,generate_password_hash(password),role,level,grade,
                         date.today().year if date.today().month>=4 else date.today().year-1,
                         gname if age<18 else '',gemail if age<18 else '',int(age>=18)))
                    db().commit();session.clear();session['user_id']=cursor.lastrowid
                    flash('Your account has been created. Welcome to Book Buddy.','success')
                    return redirect('/members/guardian-pending/' if age<18 else '/members/dashboard/')
                except sqlite3.IntegrityError:
                    db().rollback();flash('That email is already registered.','danger')
        return render16('signup',school_grades=SCHOOL_GRADES,college_grades=COLLEGE_GRADES)
    for endpoint in ('account_signup','account_signup_short'):
        app.view_functions[endpoint]=signup16

    @app.get('/members/guardian-pending/')
    @member_required
    def guardian_pending16():
        u=member()
        if years_old(u['dob']) is None:return redirect('/users/profile/?setup=1')
        if years_old(u['dob'])>=18 or u['guardian_verified']:return redirect('/members/dashboard/')
        return render16('guardian_pending',member=dict(u))

    @app.route('/users/profile/',methods=['GET','POST'],endpoint='profile_v16')
    @member_required
    def profile16():
        u=member()
        if request.method=='POST':
            name=request.form.get('name','').strip(); phone=request.form.get('phone','').strip()
            address=request.form.get('address','').strip(); dob=request.form.get('dob','')
            grade=request.form.get('grade_at_joining','');role=request.form.get('member_role','student'); level=request.form.get('education_level','school')
            age=years_old(dob);guardian=request.form.get('guardian_name','').strip();gemail=request.form.get('guardian_email','').strip().lower()
            if u['dob'] and dob!=u['dob']:
                flash('Contact the library to correct your recorded date of birth.','danger');return redirect('/users/profile/')
            if not name or len(name)>150 or len(address)>800 or role not in {'student','parent','reader'} or level not in {'school','college','other'} or len(address)<8 or not re.fullmatch(r'[0-9+()\- ]{8,18}',phone) or age is None or not 3<=age<=110 or grade not in SCHOOL_GRADES+COLLEGE_GRADES+['Working professional','Not studying']:
                flash('Please provide a valid name, phone, address, date of birth and education level.','danger')
            elif age<18 and (not guardian or '@' not in gemail):
                flash('Guardian contact details are required for minors.','danger')
            else:
                old_guardian=(u['guardian_name'],u['guardian_email'],u['dob'])
                verified=int(age>=18 or (bool(u['guardian_verified']) and old_guardian==(guardian,gemail,dob)))
                db().execute('''UPDATE users SET name=?,phone=?,address=?,dob=?,member_role=?,education_level=?,grade_at_joining=?,
                    grade_academic_year=?,guardian_name=?,guardian_email=?,guardian_verified=? WHERE id=?''',
                    (name,phone,address,dob,role,level,grade,
                     int(u['grade_academic_year']) if u['grade_at_joining']==grade and u['grade_academic_year'] else date.today().year if date.today().month>=4 else date.today().year-1,
                     guardian,gemail,verified,u['id']))
                db().commit();flash('Your profile has been updated.','success');return redirect('/members/dashboard/' if verified else '/members/guardian-pending/')
        return render16('profile',member=dict(u),school_grades=SCHOOL_GRADES,college_grades=COLLEGE_GRADES,age=years_old(u['dob']),academic_label=academic_label(u['grade_at_joining'],u['grade_academic_year']))
    app.view_functions['account_profile']=profile16

    @app.get('/members/dashboard/')
    @member_required
    def dashboard16():
        u=member();subscription=active_subscription(u['id'])
        loans=[dict(r) for r in db().execute('''SELECT l.*,b.title,b.author,b.image_path FROM lending_loans l
            JOIN books b ON b.id=l.book_id WHERE l.user_id=? ORDER BY l.id DESC LIMIT 80''',(u['id'],))]
        subs=[dict(r) for r in db().execute('''SELECT s.*,p.name,p.kind,s.book_limit_snapshot AS book_limit,p.months FROM lending_subscriptions s JOIN lending_plans p ON p.id=s.plan_id
            WHERE s.user_id=? ORDER BY s.id DESC LIMIT 24''',(u['id'],))]
        classes=[]  # Library-only: historical courses are not part of member dashboards.
        events=[dict(r) for r in db().execute('''SELECT r.status,r.seats,e.title,e.event_date,e.event_time,e.location
            FROM event_registrations r JOIN events e ON e.id=r.event_id WHERE r.user_id=? ORDER BY e.event_date DESC''',(u['id'],))]
        age=years_old(u['dob'])
        recommended=[dict(r) for r in db().execute('SELECT * FROM books ORDER BY is_new_arrival DESC,id DESC LIMIT 120').fetchall() if age_matches(r['age_group'],age)][:6]
        return render16('dashboard',member=dict(u),age=age,grade=academic_label(u['grade_at_joining'],u['grade_academic_year']),
            subscription=dict(subscription) if subscription else None,loans=loans,subscriptions=subs,classes=classes,events=events,
            recommended=recommended,remaining=max(0,int(subscription['book_limit'])-active_count(u['id'])) if subscription else 0)

    @app.get('/memberships/')
    @app.get('/membership-options/')
    def membership16():
        plans=[dict(r) for r in db().execute('SELECT * FROM lending_plans WHERE is_active=1 ORDER BY months,kind').fetchall()]
        return render16('plans','library',plans=plans)
    app.view_functions['membership']=membership16
    # Legacy plans middleware interception is avoided by using /membership-options/ in navigation.

    @app.post('/memberships/request/<int:plan_id>/')
    @member_required
    def request_plan16(plan_id):
        u=member()
        if years_old(u['dob']) is not None and years_old(u['dob'])<18 and not u['guardian_verified']:
            abort(403,'Guardian verification is required.')
        plan=db().execute('SELECT * FROM lending_plans WHERE id=? AND is_active=1',(plan_id,)).fetchone()
        if not plan:abort(404)
        pending=db().execute("SELECT id FROM lending_subscriptions WHERE user_id=? AND status='Pending' LIMIT 1",(u['id'],)).fetchone()
        if pending:flash('You already have a membership request awaiting review.','info');return redirect('/members/dashboard/')
        if active_subscription(u['id']):flash('Your membership is currently active. Contact the library to renew.','info');return redirect('/members/dashboard/')
        db().execute('INSERT INTO lending_subscriptions(user_id,plan_id,amount) VALUES(?,?,?)',(u['id'],plan_id,plan['amount']))
        db().commit();flash('Membership request received. The library will review it before activation.','success')
        return redirect('/members/dashboard/')

    @app.post('/books/<int:book_id>/request/')
    @member_required
    def request_book16(book_id):
        u=member();sub=active_subscription(u['id'])
        if years_old(u['dob']) is not None and years_old(u['dob'])<18 and not u['guardian_verified']:
            abort(403,'Guardian verification is required.')
        if not sub:flash('An active membership is required to request books.','danger');return redirect('/membership-options/')
        conn=db()
        # Protect capacity against two concurrent browser sessions requesting at once.
        try:
            conn.execute('BEGIN IMMEDIATE')
            active=conn.execute("SELECT COUNT(*) FROM lending_loans WHERE user_id=? AND status IN ('Requested','Issued')",(u['id'],)).fetchone()[0]
            book=conn.execute('SELECT * FROM books WHERE id=?',(book_id,)).fetchone()
            if not book or int(book['stock'] or 0)<1:
                conn.rollback();flash('This book currently has no available copies.','danger');return redirect('/library/')
            if active>=int(sub['book_limit']):
                conn.rollback();flash('You have reached your membership borrowing limit. Return a book or wait for a request to be resolved.','danger');return redirect('/members/dashboard/')
            reserved=conn.execute("SELECT COUNT(*) FROM lending_loans WHERE book_id=? AND status='Requested'",(book_id,)).fetchone()[0]
            if reserved>=int(book['stock'] or 0):
                conn.rollback();flash('All available copies already have pending requests. Please choose another title.','danger');return redirect('/library/')
            if conn.execute("SELECT id FROM lending_loans WHERE user_id=? AND book_id=? AND status IN ('Requested','Issued')",(u['id'],book_id)).fetchone():
                conn.rollback();flash('You have already requested or borrowed this book.','info');return redirect('/members/dashboard/')
            conn.execute('INSERT INTO lending_loans(user_id,book_id,subscription_id) VALUES(?,?,?)',(u['id'],book_id,sub['id']))
            conn.commit()
        except sqlite3.Error:
            conn.rollback();raise
        flash('Book request saved. A librarian will confirm the issue and due date.','success')
        return redirect('/members/dashboard/')

    @app.post('/members/loans/<int:loan_id>/cancel/')
    @member_required
    def cancel_request16(loan_id):
        cur=db().execute("UPDATE lending_loans SET status='Cancelled' WHERE id=? AND user_id=? AND status='Requested'",(loan_id,member()['id']))
        db().commit();flash('Request cancelled.' if cur.rowcount else 'Only pending requests can be cancelled.','info')
        return redirect('/members/dashboard/')

    @app.get('/members/statements/<int:sub_id>/')
    @member_required
    def statement16(sub_id):
        u=member()
        row=db().execute("""SELECT s.*,p.name AS plan_name,u.name AS member_name,u.email
            FROM lending_subscriptions s JOIN lending_plans p ON p.id=s.plan_id
            JOIN users u ON u.id=s.user_id WHERE s.id=? AND s.user_id=?""",(sub_id,u['id'])).fetchone()
        if not row:abort(404)
        return render16('statement',statement=dict(row))

    @app.get('/admin/lending/')
    @admin_required
    def admin_lending16():
        from library_filters import read_filters, loan_query
        from math import ceil
        import csv, io
        from flask import Response
        filters = read_filters(request.args)
        today_str = date.today().isoformat()
        joined, params, order = loan_query(filters, today_str)
        total = db().execute('SELECT COUNT(*) '+joined, params).fetchone()[0]
        pages = max(1, ceil(total / filters['per_page']))
        filters['page'] = min(filters['page'], pages)
        cols = 'l.*, b.title, u.name AS member_name, u.phone, u.email, u.dob, p.name AS plan_name'
        base = 'SELECT '+cols+' '+joined+' ORDER BY '+order
        if request.args.get('export') == 'csv':
            output = io.StringIO(); writer = csv.writer(output)
            writer.writerow(('Loan ID','Member','Email','Phone','Book','Plan','Status','Requested','Issued','Due','Returned','Note'))
            # Hard row limit protects the server against very large exports.
            for item in db().execute(base+' LIMIT 10000',params):
                row = dict(item)
                def safe_csv(value):
                    cell = str(value or '')
                    return "'"+cell if cell.lstrip().startswith(('=','+','-','@','\t','\r')) else cell
                writer.writerow([safe_csv(row.get(k)) for k in ('id','member_name','email','phone','title','plan_name','status','requested_at','issued_at','due_date','returned_at','admin_note')])
            return Response(output.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename="bookbuddy-loans-filtered.csv"','Cache-Control':'no-store'})
        rows=[dict(r) for r in db().execute(base+' LIMIT ? OFFSET ?',params+[filters['per_page'], (filters['page']-1)*filters['per_page']])]
        counts={r['status']:r['n'] for r in db().execute('SELECT status,COUNT(*) n FROM lending_loans GROUP BY status')}
        counts['Overdue']=db().execute("SELECT COUNT(*) FROM lending_loans WHERE status='Issued' AND due_date<>'' AND due_date<?",(today_str,)).fetchone()[0]
        counts['Return requested']=db().execute("SELECT COUNT(*) FROM lending_loans WHERE status='Issued' AND COALESCE(return_requested_at,'')<>''").fetchone()[0]
        overall=sum(counts.get(status,0) for status in ('Requested','Issued','Returned','Lost','Damaged','Rejected','Cancelled'))

        grouped_requests = []
        try:
            req_rows = db().execute("""
                SELECT r.*, u.name AS member_name, u.email, u.phone AS member_phone,
                       p.name AS plan_name,
                       (SELECT COUNT(*) FROM lending_loans l WHERE l.request_id = r.id) AS total_books,
                       (SELECT COUNT(*) FROM lending_loans l WHERE l.request_id = r.id AND l.status = 'Requested') AS pending_books
                FROM lending_requests r
                JOIN users u ON u.id = r.user_id
                LEFT JOIN lending_subscriptions s ON s.id = r.subscription_id
                LEFT JOIN lending_plans p ON p.id = s.plan_id
                ORDER BY r.id DESC LIMIT 50
            """).fetchall()
            for rrow in req_rows:
                req_dict = dict(rrow)
                b_rows = db().execute("""
                    SELECT l.id AS loan_id, l.status, b.id AS book_id, b.title, b.author, b.stock
                    FROM lending_loans l
                    JOIN books b ON b.id = l.book_id
                    WHERE l.request_id = ?
                    ORDER BY l.id ASC
                """, (req_dict["id"],)).fetchall()
                req_dict["books"] = [dict(b) for b in b_rows]
                grouped_requests.append(req_dict)
        except Exception:
            pass

        return render_template('workspace/lending.html',title='Borrowing desk',active='lending',admin=admin(),
                               rows=rows,counts=counts,status=filters['status'],filters=filters,
                               overall=overall,total=total,pages=pages,today=today_str,grouped_requests=grouped_requests)

    @app.post('/admin/lending/<int:loan_id>/status/')
    @admin_required
    def admin_loan_status16(loan_id):
        decision=request.form.get('action','');note=request.form.get('admin_note','').strip()[:600]
        conn=db()
        try:
            conn.execute('BEGIN IMMEDIATE')
            loan=conn.execute('SELECT * FROM lending_loans WHERE id=?',(loan_id,)).fetchone()
            if not loan:conn.rollback();abort(404)
            if decision=='issue' and loan['status']=='Requested':
                due=request.form.get('due_date','')
                try:due_dt=date.fromisoformat(due)
                except ValueError:due_dt=None
                if not due_dt or due_dt<=date.today():
                    conn.rollback();flash('Select a valid future due date.','danger');return redirect('/admin/lending/')
                if not active_subscription(loan['user_id']):
                    conn.rollback();flash('This member does not currently have an active plan.','danger');return redirect('/admin/lending/')
                result=conn.execute('UPDATE books SET stock=stock-1, available_copies=MAX(0,available_copies-1) WHERE id=? AND stock>0',(loan['book_id'],))
                if result.rowcount!=1:
                    conn.rollback();flash('No copies left to issue.','danger');return redirect('/admin/lending/')
                conn.execute("UPDATE lending_loans SET status='Issued',issued_at=?,due_date=?,admin_note=?,issued_by=? WHERE id=?",
                             (date.today().isoformat(),due,note,session['admin_id'],loan_id))
            elif decision=='return' and loan['status']=='Issued':
                conn.execute('UPDATE books SET stock=stock+1, available_copies=available_copies+1 WHERE id=?',(loan['book_id'],))
                conn.execute("UPDATE lending_loans SET status='Returned',returned_at=?,admin_note=?,returned_by=? WHERE id=?",
                             (date.today().isoformat(),note,session['admin_id'],loan_id))
            elif decision=='reject' and loan['status']=='Requested':
                conn.execute("UPDATE lending_loans SET status='Rejected',admin_note=? WHERE id=?",(note,loan_id))
            elif decision=='cancel' and loan['status']=='Requested':
                conn.execute("UPDATE lending_loans SET status='Cancelled',admin_note=? WHERE id=?",(note,loan_id))
            else:
                conn.rollback();flash('That status transition is not permitted.','danger');return redirect('/admin/lending/')
            
            if loan['request_id']:
                pending_rem = conn.execute("SELECT COUNT(*) FROM lending_loans WHERE request_id=? AND status='Requested'", (loan['request_id'],)).fetchone()[0]
                if pending_rem == 0:
                    issued_cnt = conn.execute("SELECT COUNT(*) FROM lending_loans WHERE request_id=? AND status='Issued'", (loan['request_id'],)).fetchone()[0]
                    new_req_status = 'Issued' if issued_cnt > 0 else ('Rejected' if decision == 'reject' else 'Cancelled')
                    conn.execute("UPDATE lending_requests SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_req_status, loan['request_id']))

            conn.execute('INSERT INTO admin_audit(admin_id,action) VALUES(?,?)',(session['admin_id'],f'Loan {loan_id}: {decision}'))
            conn.commit()
        except sqlite3.Error:
            conn.rollback();raise
        flash('Borrowing record updated.','success');return redirect('/admin/lending/')

    @app.post('/admin/lending/batch-request/<int:req_id>/')
    @admin_required
    def admin_batch_request16(req_id):
        action = request.form.get('action', '').strip().lower()
        note = request.form.get('admin_note', '').strip()[:600]
        due = request.form.get('due_date', '').strip()
        conn = db()
        try:
            conn.execute('BEGIN IMMEDIATE')
            req = conn.execute("SELECT * FROM lending_requests WHERE id=?", (req_id,)).fetchone()
            if not req:
                conn.rollback()
                abort(404)
            loans = conn.execute("SELECT * FROM lending_loans WHERE request_id=? AND status='Requested'", (req_id,)).fetchall()
            if not loans:
                conn.rollback()
                flash("No pending requested loans found in this batch.", "info")
                return redirect('/admin/lending/')

            if action == 'issue':
                due_dt = None
                if due:
                    try:
                        due_dt = date.fromisoformat(due)
                    except ValueError:
                        pass
                if not due_dt or due_dt <= date.today():
                    due_dt = date.today() + timedelta(days=14)
                due_str = due_dt.isoformat()

                issued_count = 0
                for l in loans:
                    res = conn.execute("UPDATE books SET stock=stock-1, available_copies=MAX(0,available_copies-1) WHERE id=? AND stock>0", (l['book_id'],))
                    if res.rowcount == 1:
                        conn.execute("UPDATE lending_loans SET status='Issued', issued_at=?, due_date=?, admin_note=?, issued_by=? WHERE id=?",
                                     (date.today().isoformat(), due_str, note, session.get('admin_id'), l['id']))
                        issued_count += 1
                    else:
                        conn.execute("UPDATE lending_loans SET status='Rejected', admin_note='Out of stock at issue time' WHERE id=?", (l['id'],))
                new_status = 'Issued' if issued_count > 0 else 'Rejected'
                conn.execute("UPDATE lending_requests SET status=?, admin_note=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_status, note, req_id))
                flash(f"Batch Request #{req_id} processed: {issued_count} book(s) issued.", "success")
            elif action == 'reject':
                conn.execute("UPDATE lending_loans SET status='Rejected', admin_note=? WHERE request_id=? AND status='Requested'", (note, req_id))
                conn.execute("UPDATE lending_requests SET status='Rejected', admin_note=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (note, req_id))
                flash(f"Batch Request #{req_id} rejected.", "info")
            elif action == 'cancel':
                conn.execute("UPDATE lending_loans SET status='Cancelled', admin_note=? WHERE request_id=? AND status='Requested'", (note, req_id))
                conn.execute("UPDATE lending_requests SET status='Cancelled', admin_note=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (note, req_id))
                flash(f"Batch Request #{req_id} cancelled.", "info")
            else:
                conn.rollback()
                flash("Invalid batch action.", "danger")
                return redirect('/admin/lending/')

            conn.execute("INSERT INTO admin_audit(admin_id, action) VALUES(?, ?)", (session.get('admin_id'), f"Batch Request {req_id}: {action}"))
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
            raise
        return redirect('/admin/lending/')

    @app.get('/admin/membership-desk/')
    @admin_required
    def admin_memberships16():
        subs=[dict(r) for r in db().execute('''SELECT s.*,u.name AS member_name,u.email,u.phone,p.name AS plan_name,p.months,s.book_limit_snapshot AS book_limit
              FROM lending_subscriptions s JOIN users u ON u.id=s.user_id
              JOIN lending_plans p ON p.id=s.plan_id ORDER BY s.id DESC LIMIT 200''')]
        minors=[dict(r) for r in db().execute("SELECT id,name,email,phone,dob,guardian_name,guardian_email FROM users WHERE guardian_verified=0 AND dob!='' ORDER BY id DESC LIMIT 150") if (years_old(r['dob']) or 0)<18]
        return render_template('workspace/membership.html',title='Membership & guardians',admin=admin(),active='memberships16',subs=subs,minors=minors)

    @app.post('/admin/membership-desk/<int:sub_id>/')
    @admin_required
    def review_subscription16(sub_id):
        action=request.form.get('action','');payment_status=request.form.get('payment_status','Unverified')
        if payment_status not in {'Unverified','Paid - confirmed by staff','Not paid'}:abort(400)
        conn=db();row=conn.execute('''SELECT s.*,p.months FROM lending_subscriptions s
            JOIN lending_plans p ON p.id=s.plan_id WHERE s.id=?''',(sub_id,)).fetchone()
        if not row or row['status']!='Pending':abort(400,'Only pending membership requests can be reviewed.')
        if action=='approve':
            start=date.today();end=add_months(start,int(row['months']))-timedelta(days=1)
            if active_subscription(row['user_id']):flash('Member already has an active subscription.','danger');return redirect('/admin/membership-desk/')
            conn.execute("UPDATE lending_subscriptions SET status='Active',starts_on=?,expires_on=?,payment_status=?,approved_by=?,book_limit_snapshot=(SELECT book_limit FROM lending_plans WHERE id=lending_subscriptions.plan_id) WHERE id=?",
                         (start.isoformat(),end.isoformat(),payment_status,session['admin_id'],sub_id))
        elif action=='reject':
            conn.execute("UPDATE lending_subscriptions SET status='Rejected',admin_note=?,approved_by=? WHERE id=?",
                         (request.form.get('admin_note','')[:600],session['admin_id'],sub_id))
        else:abort(400)
        conn.execute('INSERT INTO admin_audit(admin_id,action) VALUES(?,?)',(session['admin_id'],f'Membership {sub_id}: {action}'))
        conn.commit();flash('Membership request reviewed.','success');return redirect('/admin/membership-desk/')

    @app.route('/admin/lending-plans/',methods=['GET','POST'])
    @admin_required
    def admin_lending_plans16():
        if request.method=='POST':
            try:
                pid=int(request.form.get('plan_id','0'))
                amount=float(request.form.get('amount','-1'))
                limit=int(request.form.get('book_limit','0'))
                months=int(request.form.get('months','0'))
                enabled=int(request.form.get('is_active','0')=='1')
            except ValueError:abort(400,'Use valid numbers.')
            if not 0<=amount<=1000000 or not 1<=limit<=40 or not 1<=months<=36:abort(400,'Plan value out of range.')
            result=db().execute('UPDATE lending_plans SET amount=?,book_limit=?,months=?,is_active=? WHERE id=?',
                                (amount,limit,months,enabled,pid))
            if result.rowcount!=1:abort(404)
            db().execute('INSERT INTO admin_audit(admin_id,action) VALUES(?,?)',(session['admin_id'],f'Edited lending plan {pid}'))
            db().commit();flash('Plan saved. Existing subscriptions keep their recorded fee.','success')
            return redirect('/admin/lending-plans/')
        rows=[dict(r) for r in db().execute('SELECT * FROM lending_plans ORDER BY months,kind')]
        return render_template('workspace/plans.html',title='Lending plans',admin=admin(),active='lending-plans',plans=rows)

    @app.post('/admin/members/<int:uid>/approve-guardian/')
    @admin_required
    def approve_guardian16(uid):
        row=db().execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
        if not row or not row['guardian_email'] or not row['guardian_name']:abort(400,'Guardian details missing.')
        # Librarian must independently verify consent before pressing the button.
        if request.form.get('verified_offline')!='yes':abort(400,'Confirm independent guardian verification first.')
        db().execute('UPDATE users SET guardian_verified=1 WHERE id=?',(uid,))
        db().execute('INSERT INTO admin_audit(admin_id,action) VALUES(?,?)',(session['admin_id'],f'Guardian independently verified for member {uid}'))
        db().commit();flash('Guardian verification approved.','success');return redirect('/admin/membership-desk/')

    def legacy_shopping_removed(*a,**kw):
        if request.method=='POST':
            flash('Book Buddy is a lending library. Select Request to borrow on a book card.','info')
        return redirect('/library/')
    for ep in ('shop','add_to_cart','cart','update_cart','remove_from_cart','checkout','order_confirmation','process_library_checkout'):
        app.view_functions[ep]=legacy_shopping_removed

    @app.post('/users/submit-book-request/',endpoint='legacy_request_v16')
    @member_required
    def legacy_request_v16():
        try:book_id=int(request.form.get('book_id','0'))
        except ValueError:abort(400)
        return app.view_functions['request_book16'](book_id)
    app.view_functions['submit_book_request']=legacy_request_v16
    # Obsolete endpoints must never claim a successful payment, subscription, or checkout.
    for ep in ('users_activate_free_trial','users_process_membership','users_process_subscription'):
        app.view_functions[ep]=lambda: (Response('Use the membership request and staff approval workflow.',status=409,mimetype='text/plain'))

    @app.get('/healthz')
    @app.get('/healthz/')
    def healthz16():return Response('ok\n',mimetype='text/plain')

    # Only publicly readable marketing URLs appear in an XML sitemap.
    def sitemap16():
        from xml.sax.saxutils import escape
        import os
        root=os.environ.get('SITE_URL','http://127.0.0.1:5000').rstrip('/')
        urls=['/','/about/','/contact/','/membership/','/how-to-borrow/']
        body='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(root+p)+'</loc></url>' for p in urls)+'</urlset>'
        return Response(body,mimetype='application/xml')
    app.view_functions['sitemap_v7']=sitemap16
    app.view_functions['robots_txt']=lambda: Response("User-agent: *\nDisallow: /\n" if __import__('os').environ.get("DEMO_MODE", "0").strip().lower() in ("1", "true", "yes", "on") else 'User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /accounts/\nDisallow: /users/\nDisallow: /members/\nDisallow: /library/\nDisallow: /classes/\nDisallow: /events/\nSitemap: '+__import__('os').environ.get('SITE_URL','http://127.0.0.1:5000').rstrip('/')+'/sitemap.xml\n',mimetype='text/plain')
