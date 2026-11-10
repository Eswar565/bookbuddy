"""Server-priced event bookings, Razorpay checkout and signed payment reconciliation."""
import base64, csv, hashlib, hmac, io, json, os, re, secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import wraps
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from flask import request, session, abort, redirect, flash, render_template, Response
from management import MODELS, READ_ONLY
from resources import today_ist

def money_paise(value):
    try:
        d=Decimal(str(value))
        if not d.is_finite() or d<0:raise ValueError()
        return int((d*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    except (InvalidOperation,ValueError):raise ValueError('Enter a valid nonnegative amount.')

def razorpay_request(method,path,data=None):
    if os.environ.get('DEMO_MODE','0').strip().lower() in ('1','true','yes','on'):
        raise RuntimeError('Online payments are not configured yet. Please contact Book Buddy.')
    key=os.environ.get('RAZORPAY_KEY_ID','');secret=os.environ.get('RAZORPAY_KEY_SECRET','')
    if not key or not secret:raise RuntimeError('Online payments are not configured yet. Please contact Book Buddy.')
    auth=base64.b64encode((key+':'+secret).encode()).decode()
    req=Request('https://api.razorpay.com/v1/'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Basic '+auth,'Content-Type':'application/json'},method=method)
    try:
        with urlopen(req,timeout=20) as response:return json.load(response)
    except (URLError,HTTPError,ValueError):raise RuntimeError('The payment service is unavailable. Please try again shortly.')

def install_event_payments(app,db,render,admin):
    with app.app_context():
        have={r[1] for r in db().execute('PRAGMA table_info(event_registrations)')}
        fields={'booking_token':"TEXT DEFAULT ''",'amount_paise':'INTEGER DEFAULT 0','discount_paise':'INTEGER DEFAULT 0','coupon_id':'INTEGER DEFAULT 0','coupon_code':"TEXT DEFAULT ''",'razorpay_order_id':"TEXT DEFAULT ''",'razorpay_payment_id':"TEXT DEFAULT ''",'payment_status':"TEXT DEFAULT 'Legacy'",'hold_until':"TEXT DEFAULT ''",'attended':'INTEGER DEFAULT 0'}
        for name,definition in fields.items():
            if name not in have:db().execute(f'ALTER TABLE event_registrations ADD COLUMN {name} {definition}')
        db().executescript("CREATE UNIQUE INDEX IF NOT EXISTS booking_token_unique ON event_registrations(booking_token) WHERE booking_token!='';CREATE UNIQUE INDEX IF NOT EXISTS razorpay_order_unique ON event_registrations(razorpay_order_id) WHERE razorpay_order_id!='';CREATE UNIQUE INDEX IF NOT EXISTS razorpay_payment_unique ON event_registrations(razorpay_payment_id) WHERE razorpay_payment_id!='';CREATE TABLE IF NOT EXISTS payment_webhooks(event_key TEXT PRIMARY KEY,created_at TEXT DEFAULT CURRENT_TIMESTAMP);")
        db().commit()
    # Financial state can only be changed by the dedicated booking workflow.
    MODELS['registrations']=('Event registrations','event_registrations','event_id name email phone seats amount status')
    def now():return datetime.now(timezone.utc).isoformat()
    def booking_open(event):
        if event['event_date']<today_ist() or (event['booking_closes'] and event['booking_closes']<today_ist()):return False
        if event['event_date']==today_ist() and re.fullmatch(r'\d{2}:\d{2}',event['event_time'] or ''):
            from datetime import timezone,timedelta
            if event['event_time']<=datetime.now(timezone(timedelta(hours=5,minutes=30))).strftime('%H:%M'):return False
        return True
    def held(event_id,exclude=0):
        return db().execute("SELECT COALESCE(SUM(seats),0) FROM event_registrations WHERE event_id=? AND id!=? AND (status='Registered' OR (status='Pending' AND hold_until>?))",(event_id,exclude,now())).fetchone()[0]
    def coupon_count(coupon_id,exclude=0):return db().execute("SELECT COUNT(*) FROM event_registrations WHERE coupon_id=? AND id!=? AND (status='Registered' OR payment_status='Paid' OR (status='Pending' AND hold_until>?))",(coupon_id,exclude,now())).fetchone()[0]
    def price(event,seats,code):
        total=money_paise(event['fee'])*seats;discount=0;coupon=None
        if code:
            coupon=db().execute('SELECT * FROM event_coupons WHERE code=? COLLATE NOCASE AND is_active=1',(code,)).fetchone()
            if not coupon or coupon['event_id'] not in {0,event['id']} or (coupon['expires_on'] and coupon['expires_on']<today_ist()):raise ValueError('This coupon is invalid or has expired.')
            if total<money_paise(coupon['min_amount']):raise ValueError('This booking does not meet the coupon minimum amount.')
            if coupon['max_uses'] and coupon_count(coupon['id'])>=coupon['max_uses']:raise ValueError('This coupon has reached its usage limit.')
            discount=int((Decimal(total)*Decimal(str(coupon['value']))/100).quantize(Decimal('1'),rounding=ROUND_HALF_UP)) if coupon['discount_type']=='percent' else money_paise(coupon['value'])
            discount=min(total,discount)
        return total-discount,discount,coupon
    def get_event(event_id):
        event=db().execute('SELECT * FROM events WHERE id=? AND is_active=1',(event_id,)).fetchone()
        if not event:abort(404)
        return dict(event)
    def detail(event_id):
        e=get_event(event_id)
        return render('event_booking','events',event=e,seats_left=max(0,e['capacity']-held(event_id)),booking_available=booking_open(e),payment_enabled=bool(os.environ.get('RAZORPAY_KEY_ID') and os.environ.get('RAZORPAY_KEY_SECRET') and os.environ.get('DEMO_MODE','0').strip().lower() not in ('1','true','yes','on')))
    app.view_functions['event_detail']=detail
    def register(event_id):
        e=get_event(event_id);name=request.form.get('name','').strip();email=request.form.get('email','').strip().lower();phone=request.form.get('phone','').strip();code=request.form.get('coupon','').strip().upper()
        try:
            seats=int(request.form.get('seats','1'))
            if not 1<=seats<=10:raise ValueError('Choose 1–10 seats.')
            if not name or len(name)>200 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(email)>254:raise ValueError('Enter your name and a valid email.')
            if phone and not re.fullmatch(r'[+\d ()-]{7,25}',phone):raise ValueError('Enter a valid phone number.')
            if not booking_open(e):raise ValueError('Registration for this event has closed.')
            db().execute('BEGIN IMMEDIATE')
            previous=db().execute("SELECT booking_token FROM event_registrations WHERE event_id=? AND email=? AND name=? AND seats=? AND coupon_code=? AND status='Pending' AND hold_until>? AND booking_token!=''",(event_id,email,name,seats,code,now())).fetchone()
            if previous:db().rollback();return redirect('/booking/'+previous[0]+'/')
            if seats>e['capacity']-held(event_id):raise ValueError('There are not enough places left for this booking.')
            amount,discount,coupon=price(e,seats,code)
            if amount and not (os.environ.get('RAZORPAY_KEY_ID') and os.environ.get('RAZORPAY_KEY_SECRET') and os.environ.get('DEMO_MODE','0').strip().lower() not in ('1','true','yes','on')):raise ValueError('Online payments are not configured yet. Please contact Book Buddy.')
            token=secrets.token_urlsafe(32);expiry=(datetime.now(timezone.utc)+timedelta(minutes=15)).isoformat();status='Pending' if amount else 'Registered';pay='Pending' if amount else 'Free'
            cur=db().execute('INSERT INTO event_registrations(event_id,user_id,name,email,phone,seats,amount,status,booking_token,amount_paise,discount_paise,coupon_id,coupon_code,payment_status,hold_until) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(event_id,session.get('user_id'),name,email,phone,seats,amount/100,status,token,amount,discount,coupon['id'] if coupon else 0,code,pay,expiry));booking_id=cur.lastrowid;db().commit()
            if amount:
                try:
                    order=razorpay_request('POST','orders',{'amount':amount,'currency':'INR','receipt':'bb-event-'+str(booking_id),'notes':{'booking_id':str(booking_id),'event_id':str(event_id)}})
                    if not re.fullmatch(r'order_[A-Za-z0-9]+',str(order.get('id',''))) or order.get('amount')!=amount or order.get('currency')!='INR':raise RuntimeError('Could not prepare the payment order.')
                    db().execute('UPDATE event_registrations SET razorpay_order_id=? WHERE id=?',(order['id'],booking_id));db().commit()
                except RuntimeError:
                    db().execute("UPDATE event_registrations SET status='Cancelled',payment_status='Failed' WHERE id=?",(booking_id,));db().commit();raise
            return redirect('/booking/'+token+'/')
        except (ValueError,RuntimeError) as error:
            db().rollback();flash(str(error),'danger');return redirect('/events/'+str(event_id)+'/')
    app.view_functions['register_event']=register

    def booking(token):
        row=db().execute('SELECT r.*,e.title,e.event_date,e.event_time,e.location,e.join_url FROM event_registrations r JOIN events e ON e.id=r.event_id WHERE r.booking_token=? AND r.booking_token!=?',(token,'')).fetchone()
        if not row:abort(404)
        return dict(row)
    @app.get('/booking/<token>/')
    def event_booking_v9(token):
        b=booking(token)
        response=render('booking','events',booking=b,expired=b['status']=='Pending' and b['hold_until']<now(),razorpay_key=os.environ.get('RAZORPAY_KEY_ID',''))
        response=app.make_response(response);response.headers['Cache-Control']='no-store';response.headers['Referrer-Policy']='no-referrer';response.headers['X-Robots-Tag']='noindex,nofollow';return response

    def settle(order_id,payment):
        """Atomic and idempotent; late payments get a place only when capacity permits."""
        db().execute('BEGIN IMMEDIATE')
        try:
            b=db().execute('SELECT * FROM event_registrations WHERE razorpay_order_id=? AND razorpay_order_id!=?',(order_id,'')).fetchone()
            if not b:raise ValueError('Unknown booking order.')
            if payment.get('order_id')!=b['razorpay_order_id'] or payment.get('amount')!=b['amount_paise'] or payment.get('currency')!='INR' or payment.get('status')!='captured' or not re.fullmatch(r'pay_[A-Za-z0-9]+',str(payment.get('id',''))):raise ValueError('Payment is not captured or does not match this booking.')
            if b['payment_status']=='Paid':
                if b['razorpay_payment_id']!=payment['id']:raise ValueError('This booking already has a payment.')
                db().rollback();return
            event=db().execute('SELECT * FROM events WHERE id=?',(b['event_id'],)).fetchone()
            coupon=db().execute('SELECT * FROM event_coupons WHERE id=?',(b['coupon_id'],)).fetchone() if b['coupon_id'] else None
            fits=event and event['is_active'] and booking_open(event) and b['status']=='Pending' and held(b['event_id'],b['id'])+b['seats']<=event['capacity']
            if coupon and coupon['max_uses'] and coupon_count(coupon['id'],b['id'])>=coupon['max_uses']:fits=False
            db().execute('UPDATE event_registrations SET payment_status=?,status=?,razorpay_payment_id=? WHERE id=?',('Paid','Registered' if fits else 'Payment review',payment['id'],b['id']));db().commit()
        except Exception:db().rollback();raise
    @app.post('/booking/<token>/verify/')
    def verify_event_payment_v9(token):
        b=booking(token);payment_id=request.form.get('razorpay_payment_id','');order=request.form.get('razorpay_order_id','');signature=request.form.get('razorpay_signature','');secret=os.environ.get('RAZORPAY_KEY_SECRET','')
        if not secret or order!=b['razorpay_order_id'] or not re.fullmatch(r'pay_[A-Za-z0-9]+',payment_id):abort(400,'Invalid payment response.')
        expected=hmac.new(secret.encode(),(b['razorpay_order_id']+'|'+payment_id).encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature,expected):abort(400,'Payment signature could not be verified.')
        try:settle(b['razorpay_order_id'],razorpay_request('GET','payments/'+payment_id))
        except (RuntimeError,ValueError):flash('Your payment is being verified. Refresh this booking shortly; contact Book Buddy if it remains pending.','info')
        return redirect('/booking/'+token+'/')
    @app.post('/payments/razorpay/webhook/')
    def razorpay_webhook_v9():
        raw=request.get_data();secret=os.environ.get('RAZORPAY_WEBHOOK_SECRET','');signature=request.headers.get('X-Razorpay-Signature','')
        if not secret or not hmac.compare_digest(hmac.new(secret.encode(),raw,hashlib.sha256).hexdigest(),signature):abort(400,'Invalid webhook signature.')
        try:data=json.loads(raw)
        except ValueError:abort(400)
        if not isinstance(data,dict) or not isinstance(data.get('payload',{}),dict):abort(400)
        event_key=request.headers.get('X-Razorpay-Event-Id','') or hashlib.sha256(raw).hexdigest()
        if db().execute('SELECT 1 FROM payment_webhooks WHERE event_key=?',(event_key,)).fetchone():return {'ok':True}
        if data.get('event') in {'payment.captured','order.paid'}:
            block=data.get('payload',{}).get('payment',{})
            if not isinstance(block,dict):abort(400)
            p=block.get('entity',{})
            if not isinstance(p,dict):abort(400)
            # Only this application's event orders are consumed. Other gateway products can share an account.
            if db().execute('SELECT 1 FROM event_registrations WHERE razorpay_order_id=? AND razorpay_order_id!=?',(p.get('order_id',''),'' )).fetchone():
                try:settle(p.get('order_id'),p)
                except ValueError:abort(400,'Payment does not match the booking.')
        db().execute('INSERT OR IGNORE INTO payment_webhooks(event_key) VALUES (?)',(event_key,));db().commit();return {'ok':True}

    def guard(fn):
        @wraps(fn)
        def wrapper(*a,**kw):
            if not admin():return redirect('/admin/login/')
            return fn(*a,**kw)
        return wrapper
    def workspace(template,**kw):return render_template('workspace/'+template+'.html',models=MODELS,admin=admin(),active='events',**kw)
    @app.get('/admin/events/')
    @guard
    def event_admin_v9():
        events=[dict(x) for x in db().execute("SELECT e.*,(SELECT COALESCE(SUM(seats),0) FROM event_registrations r WHERE r.event_id=e.id AND r.status='Registered') booked,(SELECT COALESCE(SUM(amount),0) FROM event_registrations r WHERE r.event_id=e.id AND r.payment_status='Paid') collected FROM events e ORDER BY event_date DESC")]
        return workspace('events',title='Event bookings & participants',events=events,payment_ready=bool(os.environ.get('RAZORPAY_KEY_ID') and os.environ.get('RAZORPAY_KEY_SECRET')),webhook_ready=bool(os.environ.get('RAZORPAY_WEBHOOK_SECRET')))
    @app.route('/admin/events/<int:event_id>/',methods=['GET','POST'])
    @guard
    def event_participants_v9(event_id):
        event=db().execute('SELECT * FROM events WHERE id=?',(event_id,)).fetchone()
        if not event:abort(404)
        if request.method=='POST':
            row=db().execute('SELECT * FROM event_registrations WHERE id=? AND event_id=?',(request.form.get('registration_id',''),event_id)).fetchone()
            if not row:abort(404)
            action=request.form.get('action')
            if action=='attendance' and row['status']=='Registered':db().execute('UPDATE event_registrations SET attended=? WHERE id=?',(0 if row['attended'] else 1,row['id']))
            elif action=='confirm-review' and row['status']=='Payment review' and row['payment_status']=='Paid':
                db().execute('BEGIN IMMEDIATE')
                if held(event_id,row['id'])+row['seats']>event['capacity']:
                    db().rollback();flash('Not enough places available. Arrange a refund in Razorpay or increase capacity after confirming availability.','danger');return redirect(request.path)
                db().execute("UPDATE event_registrations SET status='Registered' WHERE id=?",(row['id'],))
            elif action=='cancel' and row['status'] in {'Pending','Registered','Payment review'}:db().execute("UPDATE event_registrations SET status='Cancelled' WHERE id=?",(row['id'],))
            else:abort(400,'This action is not available for this booking.')
            db().execute('INSERT INTO admin_audit(admin_id,action) VALUES (?,?)',(session['admin_id'],f'Event {event_id} booking {row["id"]}: {action}'));db().commit();return redirect(request.path)
        status=request.args.get('status','');q=request.args.get('q','').strip();sql='SELECT * FROM event_registrations WHERE event_id=?';args=[event_id]
        if status:sql+=' AND status=?';args.append(status)
        if q:sql+=' AND (name LIKE ? OR email LIKE ? OR phone LIKE ?)';args+=['%'+q+'%']*3
        records=[dict(x) for x in db().execute(sql+' ORDER BY id DESC',args)]
        if request.args.get('export')=='csv':
            fields=['id','name','email','phone','seats','amount','discount_paise','coupon_code','status','payment_status','razorpay_order_id','razorpay_payment_id','attended','created_at'];stream=io.StringIO();writer=csv.writer(stream);writer.writerow(fields)
            for r in records:writer.writerow([("'"+str(r[f])) if str(r[f]).startswith(('=','+','-','@')) else r[f] for f in fields])
            return Response(stream.getvalue(),mimetype='text/csv',headers={'Content-Disposition':f'attachment; filename=event-{event_id}-participants.csv'})
        return workspace('participants',title='Participants · '+event['title'],event=dict(event),records=records,q=q,selected_status=status)
    # Generic record editor cannot forge or overwrite gateway-backed registrations.
    original=app.view_functions['edit_record']
    def protected_editor(kind,record_id):
        if kind=='registrations':
            if not admin():return redirect('/admin/login/')
            r=db().execute('SELECT event_id FROM event_registrations WHERE id=?',(record_id,)).fetchone()
            if not r:abort(404)
            return redirect('/admin/events/'+str(r[0])+'/')
        return original(kind,record_id)
    app.view_functions['edit_record']=protected_editor
