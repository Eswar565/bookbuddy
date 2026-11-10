"""Event calendar and per-admin reader notifications."""
import calendar,re
from datetime import date
from functools import wraps
from flask import request,session,redirect,abort,render_template,jsonify
from management import MODELS
from library_core import IMPORTABLE
from resources import today_ist

def install_release10(app,db,render,admin):
    with app.app_context():
        import os
        conn = db()
        conn.executescript('''CREATE TABLE IF NOT EXISTS admin_notifications(id INTEGER PRIMARY KEY,kind TEXT NOT NULL,title TEXT NOT NULL,body TEXT DEFAULT '',url TEXT NOT NULL,source_key TEXT UNIQUE NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS notification_reads(notification_id INTEGER NOT NULL REFERENCES admin_notifications(id) ON DELETE CASCADE,admin_id INTEGER NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,read_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(notification_id,admin_id));
        CREATE INDEX IF NOT EXISTS notification_kind_date ON admin_notifications(kind,id);
        CREATE TABLE IF NOT EXISTS app_flags(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        ''')
        # Seed notifications_enabled if missing: default '0' for development/local/testing, '1' for production
        app_env = (os.environ.get("APP_ENV") or "").lower()
        default_enabled = '0' if app_env in ('development', 'dev', 'local', 'testing') else '1'
        conn.execute("INSERT OR IGNORE INTO app_flags(key,value) VALUES ('notifications_enabled', ?)", (default_enabled,))

        # Drop old notify10 triggers so new definitions with WHEN clause take effect
        old_tables = ['users', 'contact_submissions', 'event_registrations', 'event_registrations_insert', 'event_registrations_update', 'memberships', 'orders', 'book_requests', 'subscribers', 'reader_contributions']
        for ot in old_tables:
            conn.execute(f"DROP TRIGGER IF EXISTS notify10_{ot}")

        # Retain existing trigger cleanup from previous releases
        conn.execute('DROP TRIGGER IF EXISTS notify10_event_payment')

        # Standard AFTER INSERT triggers guarded by notifications_enabled flag
        triggers=[
            ('users','members','New member registration',"NEW.name || ' · ' || NEW.email","'/admin/manage/members/' || NEW.id || '/'"),
            ('contact_submissions','enquiries','New contact message',"COALESCE(NEW.full_name,'Visitor') || ' · ' || COALESCE(NEW.subject,'Website enquiry')","'/admin/manage/enquiries/' || NEW.id || '/'"),
            ('memberships','memberships','New membership request',"'Member #' || NEW.user_id || ' · ' || NEW.status","'/admin/manage/memberships/' || NEW.id || '/'"),
            ('orders','orders','New book order',"NEW.customer_name || ' · Order #' || NEW.id","'/admin/manage/orders/' || NEW.id || '/'"),
            ('book_requests','library','New borrowing request',"NEW.user_name || ' · ' || NEW.book_title","'/admin/manage/requests/' || NEW.id || '/'"),
            ('subscribers','subscribers','New newsletter subscriber',"NEW.email","'/admin/manage/subscribers/' || NEW.id || '/'"),
            ('reader_contributions','contributions','New reader contribution',"NEW.student_name || ' · ' || NEW.title","'/admin/manage/contributions/' || NEW.id || '/'")
        ]
        for table,kind,title,body,url in triggers:
            conn.execute(f"""CREATE TRIGGER IF NOT EXISTS notify10_{table} AFTER INSERT ON {table}
            WHEN (SELECT value FROM app_flags WHERE key='notifications_enabled')='1'
            BEGIN
                INSERT OR IGNORE INTO admin_notifications(kind,title,body,url,source_key) VALUES ('{kind}','{title}',{body},{url},'{table}:' || NEW.id);
            END;""")

        # Event registration triggers: only fire for confirmed/paid/registered bookings (not pending checkout)
        conn.execute("""CREATE TRIGGER IF NOT EXISTS notify10_event_registrations_insert AFTER INSERT ON event_registrations
        WHEN (SELECT value FROM app_flags WHERE key='notifications_enabled')='1'
          AND lower(NEW.status) IN ('registered','confirmed','paid')
        BEGIN
            INSERT OR IGNORE INTO admin_notifications(kind,title,body,url,source_key)
            VALUES ('events','New event booking',NEW.name || ' · ' || NEW.seats || ' seat(s) · ' || NEW.status,'/admin/events/' || NEW.event_id || '/','event_registrations:' || NEW.id);
        END;""")

        conn.execute("""CREATE TRIGGER IF NOT EXISTS notify10_event_registrations_update AFTER UPDATE OF status ON event_registrations
        WHEN (SELECT value FROM app_flags WHERE key='notifications_enabled')='1'
          AND lower(NEW.status) IN ('registered','confirmed','paid')
          AND lower(OLD.status) <> lower(NEW.status)
        BEGIN
            INSERT OR IGNORE INTO admin_notifications(kind,title,body,url,source_key)
            VALUES ('events','New event booking',NEW.name || ' · ' || NEW.seats || ' seat(s) · ' || NEW.status,'/admin/events/' || NEW.event_id || '/','event_registrations:' || NEW.id);
        END;""")

        conn.commit()

    def guard(fn):
        @wraps(fn)
        def inner(*a,**kw):
            if not admin():return redirect('/admin/login/')
            return fn(*a,**kw)
        return inner
    def unread_count():return db().execute('SELECT COUNT(*) FROM admin_notifications n WHERE NOT EXISTS (SELECT 1 FROM notification_reads r WHERE r.notification_id=n.id AND r.admin_id=?)',(session['admin_id'],)).fetchone()[0]
    def latest(limit=8):return [dict(r) for r in db().execute('SELECT n.*,EXISTS(SELECT 1 FROM notification_reads r WHERE r.notification_id=n.id AND r.admin_id=?) is_read FROM admin_notifications n ORDER BY n.id DESC LIMIT ?',(session['admin_id'],limit))]
    def calendar_context():
        month=request.args.get('month',today_ist()[:7]);category=request.args.get('category','')
        if category not in {'reading-circle','contest'}:category=''
        try:y,m=map(int,month.split('-'));assert 2000<=y<=2100 and 1<=m<=12
        except (ValueError,AssertionError):y,m=map(int,today_ist()[:7].split('-'))
        key=f'{y}-{m:02d}';sql='SELECT id,title,event_date,event_time,location,fee,category FROM events WHERE is_active=1 AND event_date LIKE ?';args=[key+'%']
        if category in {'reading-circle','contest'}:sql+=' AND category=?';args.append(category)
        records=[dict(r) for r in db().execute(sql+' ORDER BY event_date,event_time',args)]
        prev=date(y-1,12,1) if m==1 else date(y,m-1,1);nxt=date(y+1,1,1) if m==12 else date(y,m+1,1)
        return {'month':key,'label':date(y,m,1).strftime('%B %Y'),'weeks':calendar.Calendar(firstweekday=0).monthdayscalendar(y,m),'prev':prev.strftime('%Y-%m'),'next':nxt.strftime('%Y-%m'),'category':category,'events':records,'today':today_ist(),'prev_enabled':y>2000 or m>1,'next_enabled':y<2100 or m<12}
    @app.context_processor
    def extras10():
        path=request.path.strip('/');first=path.split('/')[0]
        data={}
        if not path:
            data['home_calendar']=calendar_context();data['home_upcoming']=[dict(r) for r in db().execute('SELECT id,title,event_date,event_time,location,fee,category FROM events WHERE is_active=1 AND event_date>=? ORDER BY event_date,event_time LIMIT 4',(today_ist(),))]
        if admin():data.update(admin_notification_count=unread_count(),admin_latest_notifications=latest())
        return data
    @app.get('/home-calendar/')
    def home_calendar10():
        response=app.make_response(render_template('site/calendar.html',home_calendar=calendar_context()));response.headers['Cache-Control']='no-store';response.headers['X-Robots-Tag']='noindex';return response
    @app.get('/admin/notifications/feed/')
    def notification_feed10():
        if not admin():return jsonify(error='Sign in required'),401
        try:after=max(0,int(request.args.get('after','0')))
        except ValueError:after=0
        items=latest(12);response=jsonify(unread=unread_count(),latest_id=db().execute('SELECT COALESCE(MAX(id),0) FROM admin_notifications').fetchone()[0],new_count=db().execute('SELECT COUNT(*) FROM admin_notifications WHERE id>?',(after,)).fetchone()[0],items=items);response.headers['Cache-Control']='no-store';return response
    @app.get('/admin/notifications/')
    @guard
    def notifications10():
        kind=request.args.get('kind','');view=request.args.get('view','unread')
        try:page=max(1,int(request.args.get('page','1')))
        except ValueError:page=1
        where=[];args=[session['admin_id']]
        if view!='all':where.append('r.notification_id IS NULL')
        if kind:where.append('n.kind=?');args.append(kind)
        condition=(' WHERE '+' AND '.join(where)) if where else ''
        base=' FROM admin_notifications n LEFT JOIN notification_reads r ON r.notification_id=n.id AND r.admin_id=?'
        count=db().execute('SELECT COUNT(*)'+base+condition,args).fetchone()[0];pages=max(1,(count+39)//40);page=min(page,pages)
        rows=[dict(r) for r in db().execute('SELECT n.*,r.read_at'+base+condition+' ORDER BY n.id DESC LIMIT 40 OFFSET ?',args+[(page-1)*40])]
        return render_template('workspace/notifications.html',models=MODELS,admin=admin(),title='Notifications',active='notifications',notifications=rows,kinds=[r[0] for r in db().execute('SELECT DISTINCT kind FROM admin_notifications ORDER BY kind')],selected_kind=kind,selected_view=view,page=page,pages=pages,total=count)
    @app.post('/admin/notifications/read/')
    @guard
    def read_notifications10():
        if request.form.get('all')=='1':db().execute('INSERT OR IGNORE INTO notification_reads(notification_id,admin_id) SELECT id,? FROM admin_notifications',(session['admin_id'],))
        else:
            try:nid=int(request.form.get('notification_id','0'))
            except ValueError:abort(400)
            if not db().execute('SELECT 1 FROM admin_notifications WHERE id=?',(nid,)).fetchone():abort(404)
            db().execute('INSERT OR IGNORE INTO notification_reads(notification_id,admin_id) VALUES (?,?)',(nid,session['admin_id']))
        db().commit();return redirect('/admin/notifications/')
