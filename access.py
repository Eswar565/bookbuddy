import re
"""Library membership access, local About content and reader profile."""
import json
import math
from datetime import date, timedelta
from functools import wraps
from urllib.parse import quote
from flask import request, session, redirect, abort, flash, Response
from werkzeug.security import check_password_hash, generate_password_hash
from management import MODELS, NUMBERS, BOOLS, LONG

SCOPES = {'events','media'}

def install_upgrade(app, db, render, admin, root):
    def rows(sql, args=()): return [dict(r) for r in db().execute(sql,args)]
    def setting(key, fallback=''):
        row=db().execute('SELECT content_value FROM site_content WHERE content_key=?',(key,)).fetchone()
        return row[0] if row else fallback
    with app.app_context():
        db().executescript('''
        CREATE TABLE IF NOT EXISTS schema_updates(version TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS plans(id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '', price REAL DEFAULT 0, duration_days INTEGER DEFAULT 30, scopes TEXT DEFAULT '', is_active INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS memberships(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), plan_id INTEGER NOT NULL REFERENCES plans(id), status TEXT DEFAULT 'Pending', starts_on TEXT DEFAULT '', expires_on TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS access_rules(id INTEGER PRIMARY KEY, title TEXT UNIQUE NOT NULL, scope TEXT UNIQUE NOT NULL, access_mode TEXT DEFAULT 'public');
        ''')
        for key,value in {'about_philosophy_intro':'','about_philosophy_body':'','about_ikigai_url':'','reading_circle_whatsapp_url':''}.items(): db().execute('INSERT OR IGNORE INTO site_content VALUES (?,?)',(key,value))
        for table, cols in {'users':{'phone':"TEXT DEFAULT ''",'address':"TEXT DEFAULT ''",'bio':"TEXT DEFAULT ''",'is_active':'INTEGER DEFAULT 1'},'events':{'category':"TEXT DEFAULT 'upcoming'"}}.items():
            existing={r[1] for r in db().execute('PRAGMA table_info('+table+')')}
            for name,definition in cols.items():
                if name not in existing: db().execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')
        defaults={'contact_phone':'','contact_email':'','contact_address':'','contact_hours':'','founder_name':'','founder_role':'','founder_message':'','founder_note':'','about_heading':'About BookBuddy','membership_intro':'Choose a plan for borrowing books.'}
        for k,v in defaults.items(): db().execute('INSERT OR IGNORE INTO site_content VALUES (?,?)',(k,v))
        for scope in sorted(SCOPES): db().execute('INSERT OR IGNORE INTO access_rules(title,scope,access_mode) VALUES (?,?,?)',(scope.title(),scope,'public'))
        pass
        db().commit()
    MODELS.update({
        'plans':('Membership plans','plans','title description price duration_days scopes is_active'),
        'memberships':('Membership requests','memberships','user_id plan_id status starts_on expires_on'),
        'access':('Content access','access_rules','title scope access_mode'),
        'members':('Members','users','name email phone address bio is_active'),
    })
    MODELS['events']=('Events','events','title category description event_date event_time location fee capacity is_online is_active')
    MODELS['publications']=('Media & publications','publications','title kind description edition file_path cover_path published_on is_active')
    NUMBERS.update({'duration_days','user_id','plan_id'}); BOOLS.add('is_active'); LONG.add('bio')
    from management import READ_ONLY
    READ_ONLY.add('access')

    def authorized(scope):
        if admin(): return True
        rule=db().execute('SELECT access_mode FROM access_rules WHERE scope=?',(scope,)).fetchone()
        mode=rule[0] if rule else 'public'
        if mode=='public': return True
        uid=session.get('user_id')
        if not uid or not db().execute('SELECT 1 FROM users WHERE id=? AND is_active=1',(uid,)).fetchone(): return False
        if mode=='login': return True
        today=date.today().isoformat()
        memberships=rows("SELECT p.scopes FROM memberships m JOIN plans p ON m.plan_id=p.id WHERE m.user_id=? AND m.status='Active' AND m.starts_on<=? AND m.expires_on>=?",(uid,today,today))
        if any(scope in {s.strip() for s in m['scopes'].split(',')} for m in memberships):return True
        # Library borrowing plans also provide member-only reading content.
        try:
            return bool(db().execute("""SELECT 1 FROM lending_subscriptions
                 WHERE user_id=? AND status IN ('Active','Scheduled')
                 AND starts_on<=? AND expires_on>=? LIMIT 1""",(uid,today,today)).fetchone())
        except Exception:
            return False

    def locked(scope):
        if not session.get('user_id'): return redirect('/accounts/login/?next='+quote(request.full_path.rstrip('?'),safe=''))
        return render('access_required','account',scope=scope),403

    @app.context_processor
    def membership_context(): return {'can_access':authorized}

    @app.before_request
    def access_and_publishing():
        path=request.path.strip('/')
        if session.get('user_id') and not db().execute('SELECT 1 FROM users WHERE id=? AND is_active=1',(session['user_id'],)).fetchone(): session.pop('user_id',None)
        # Private documents in the supplied archive must not be served as website assets.
        if path.startswith(('media/resumes/','static/resumes/')): abort(404)
        if request.method=='GET' and not path.startswith(('admin/','static/','media/')):
            page=db().execute('SELECT is_active FROM cms_pages WHERE slug=?',(path.removeprefix('legacy/'),)).fetchone()
            if page and not page[0]: abort(404)
        # Catalogues and event pages are public; individual paid files are checked
        # by media_access.py, never by a whole-category gate.
        if request.method!='GET': return None
        if path=='about':
            page=db().execute("SELECT * FROM cms_pages WHERE slug='about' AND is_active=1").fetchone()
            from about_content import about_context
            return render('about','about',page=dict(page) if page else {},**about_context(db))
        if path=='contact': return render('contact','contact')
    @app.post('/membership/request/<int:plan_id>/')
    def request_plan(plan_id):
        if not session.get('user_id'): return redirect('/accounts/login/?next=/membership/')
        plan=db().execute('SELECT * FROM plans WHERE id=? AND is_active=1',(plan_id,)).fetchone()
        if not plan: abort(404)
        if not db().execute("SELECT 1 FROM memberships WHERE user_id=? AND plan_id=? AND status='Pending'",(session['user_id'],plan_id)).fetchone():
            db().execute('INSERT INTO memberships(user_id,plan_id) VALUES (?,?)',(session['user_id'],plan_id)); db().commit()
        flash('Membership request received. The team will confirm your plan and arrange payment, if applicable.','success')
        return redirect('/users/profile/')

    def profile():
        uid=session.get('user_id')
        if not uid: return redirect('/accounts/login/?next=/users/profile/')
        member=dict(db().execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone())
        if request.method=='POST':
            if request.form.get('action')=='password':
                password=request.form.get('password','')
                if len(password)<12 or not check_password_hash(member['password_hash'],request.form.get('current_password','')):
                    flash('Enter your current password and a new password of at least 12 characters.','danger')
                else:
                    db().execute('UPDATE users SET password_hash=? WHERE id=?',(generate_password_hash(password),uid)); db().commit(); flash('Password changed.','success')
            else:
                name=request.form.get('name','').strip()
                if not name: abort(400,'Name is required.')
                db().execute('UPDATE users SET name=?,phone=?,address=?,bio=? WHERE id=?',(name,request.form.get('phone','')[:40],request.form.get('address','')[:500],request.form.get('bio','')[:1000],uid)); db().commit(); flash('Profile updated.','success')
            return redirect('/users/profile/')
        return render('profile_v6_current','account',member=member,memberships=rows('SELECT m.*,p.title,p.scopes FROM memberships m JOIN plans p ON p.id=m.plan_id WHERE m.user_id=? ORDER BY m.id DESC',(uid,)),member_orders=rows('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC',(uid,)),member_events=rows('SELECT r.*,e.title FROM event_registrations r JOIN events e ON e.id=r.event_id WHERE r.user_id=?',(uid,)))
    app.view_functions['account_profile']=profile

    # A compact, server-paginated catalogue reuses the existing basket and checkout.
    def catalogue():
        q=request.args.get('q','').strip(); collection=request.args.get('collection','').strip()
        try: page=max(1,int(request.args.get('page',1)))
        except ValueError: page=1
        where=' WHERE (title LIKE ? OR author LIKE ? OR description LIKE ?)'; args=['%'+q+'%']*3
        if collection: where+=' AND collection=?'; args.append(collection)
        count=db().execute('SELECT count(*) FROM books'+where,args).fetchone()[0]; pages=max(1,math.ceil(count/12)); page=min(page,pages)
        return render('library','library',books=rows('SELECT * FROM books'+where+' ORDER BY id DESC LIMIT 12 OFFSET ?',args+[(page-1)*12]),query=q,selected_collection=collection,catalogue_page=page,catalogue_pages=pages,catalogue_count=count,collections=[r[0] for r in db().execute('SELECT DISTINCT collection FROM books ORDER BY collection')])
    app.view_functions['modern_library']=catalogue
