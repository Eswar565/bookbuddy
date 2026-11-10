"""Gateway responses are mocked: no external payments or credentials are used."""
import hashlib,hmac,json,uuid
from datetime import date,timedelta
from bs4 import BeautifulSoup
import pytest

@pytest.fixture
def payment_case(monkeypatch):
    from app import app,get_db
    import payments
    key=uuid.uuid4().hex[:12]
    for name,value in [('RAZORPAY_KEY_ID','rzp_test_placeholder'),('RAZORPAY_KEY_SECRET','qa-secret'),('RAZORPAY_WEBHOOK_SECRET','event-secret'),('RAZORPAY_MEMBERSHIP_WEBHOOK_SECRET','member-secret')]:monkeypatch.setenv(name,value)
    with app.app_context():
        db=get_db()
        uid=db.execute("INSERT INTO users(name,email,password_hash,dob) VALUES(?,?,?,?)",('QA','qa-'+key+'@example.test','unused','1990-01-01')).lastrowid
        pid=db.execute("INSERT INTO lending_plans(name,months,kind,book_limit,amount,duration_days) VALUES(?,3,'Membership',2,250,90)",('QA '+key,)).lastrowid
        eid=db.execute("INSERT INTO events(title,event_date,event_time,capacity,fee,is_active) VALUES(?,?,?,2,100,1)",('QA event '+key,(date.today()+timedelta(days=30)).isoformat(),'10:00')).lastrowid;db.commit()
    state={'order_id':'order_'+key,'payment_id':'pay_'+key,'amount':25000,'currency':'INR','status':'captured'}
    def gateway(method,path,data=None):
        if method=='POST':state['amount']=data['amount'];return {'id':state['order_id'],'amount':data['amount'],'currency':'INR'}
        return dict(id=state['payment_id'],order_id=state['order_id'],amount=state['amount'],currency=state['currency'],status=state['status'])
    monkeypatch.setattr(payments,'razorpay_request',gateway)
    app.config['TESTING']=True
    return app,uid,pid,eid,state

def token(c):
    return BeautifulSoup(c.get('/accounts/login/').data,'html.parser').select_one('input[name=csrf_guard]')['value']

def sign(value,secret='qa-secret'):return hmac.new(secret.encode(),value.encode(),hashlib.sha256).hexdigest()

def member_order(c,uid,pid):
    with c.session_transaction() as s:s['user_id']=uid
    t=token(c)
    response=c.post('/memberships/request/'+str(pid)+'/',data={'csrf_guard':t})
    assert response.status_code==302
    url=response.headers['Location'];assert '/members/billing/' in url
    assert c.post(url,data={'csrf_guard':t}).status_code==302
    assert b'membership-pay' in c.get(url).data
    return url,t

@pytest.mark.parametrize('invalid',['signature','amount','currency','authorized'])
def test_membership_rejects_unverified_payment(payment_case,invalid):
    app,uid,pid,eid,state=payment_case
    from app import get_db
    with app.test_client() as c:
        url,t=member_order(c,uid,pid)
        signature=sign(state['order_id']+'|'+state['payment_id'])
        if invalid=='signature':signature='incorrect'
        if invalid=='amount':state['amount']=1
        if invalid=='currency':state['currency']='USD'
        if invalid=='authorized':state['status']='authorized'
        r=c.post(url+'verify/',data={'csrf_guard':t,'razorpay_payment_id':state['payment_id'],'razorpay_signature':signature})
        assert r.status_code==400
        with app.app_context():assert get_db().execute('SELECT status FROM lending_subscriptions WHERE user_id=?',(uid,)).fetchone()[0]=='Pending'

def test_membership_captured_and_duplicate(payment_case):
    app,uid,pid,eid,state=payment_case
    from app import get_db
    with app.test_client() as c:
        url,t=member_order(c,uid,pid)
        form={'csrf_guard':t,'razorpay_payment_id':state['payment_id'],'razorpay_signature':sign(state['order_id']+'|'+state['payment_id'])}
        for _ in range(2):assert c.post(url+'verify/',data=form).status_code==302
        with app.app_context():
            row=get_db().execute('SELECT * FROM lending_subscriptions WHERE user_id=?',(uid,)).fetchone();assert row['status']=='Active';assert row['payment_status']=='Paid - Razorpay'

def test_membership_rejects_bad_gateway_order(payment_case,monkeypatch):
    app,uid,pid,eid,state=payment_case
    import payments
    from app import get_db
    monkeypatch.setattr(payments,'razorpay_request',lambda *args,**kw:{'id':'order_bad','amount':1,'currency':'INR'})
    with app.test_client() as c:
        with c.session_transaction() as s:s['user_id']=uid
        t=token(c);url=c.post('/memberships/request/'+str(pid)+'/',data={'csrf_guard':t}).headers['Location']
        assert c.post(url,data={'csrf_guard':t}).status_code==302
        with app.app_context():assert get_db().execute('SELECT COUNT(*) FROM payments17 p JOIN lending_subscriptions s ON s.id=p.subscription_id WHERE s.user_id=?',(uid,)).fetchone()[0]==0

@pytest.mark.parametrize('invalid',[False,True])
def test_guest_event_checkout(payment_case,invalid):
    app,uid,pid,eid,state=payment_case
    from app import get_db
    with app.test_client() as c:
        t=token(c);r=c.post('/events/'+str(eid)+'/register/',data={'csrf_guard':t,'name':'Guest','email':'guest@example.test','phone':'9876543210','seats':'1','amount':'1'})
        assert r.status_code==302
        url=r.headers['Location'];assert '/booking/' in url;assert b'pay-event' in c.get(url).data
        assert state['amount']==10000  # Ignores submitted amount.
        form={'csrf_guard':t,'razorpay_payment_id':state['payment_id'],'razorpay_order_id':state['order_id'],'razorpay_signature':'bad' if invalid else sign(state['order_id']+'|'+state['payment_id'])}
        r=c.post(url+'verify/',data=form);assert r.status_code==(400 if invalid else 302)
        if not invalid:assert c.post(url+'verify/',data=form).status_code==302
        with app.app_context():assert get_db().execute('SELECT status FROM event_registrations WHERE event_id=?',(eid,)).fetchone()[0]==('Pending' if invalid else 'Registered')

def test_webhook_verification_and_shared_account(payment_case):
    app,uid,pid,eid,state=payment_case
    with app.test_client() as c:
        for endpoint,secret in [('/payments/membership/webhook/','member-secret'),('/payments/razorpay/webhook/','event-secret')]:
            body=json.dumps({'event':'payment.captured','payload':{'payment':{'entity':{'order_id':'order_unrelated'}}}})
            assert c.post(endpoint,data=body,content_type='application/json',headers={'X-Razorpay-Signature':'bad'}).status_code==400
            assert c.post(endpoint,data=body,content_type='application/json',headers={'X-Razorpay-Signature':sign(body,secret)}).status_code==200
        body='[]';assert c.post('/payments/membership/webhook/',data=body,content_type='application/json',headers={'X-Razorpay-Signature':sign(body,'member-secret')}).status_code==400

def test_membership_webhook_capture_is_idempotent(payment_case):
    app,uid,pid,eid,state=payment_case
    from app import get_db
    with app.test_client() as c:
        member_order(c,uid,pid)
        body=json.dumps({'event':'payment.captured','payload':{'payment':{'entity':dict(id=state['payment_id'],order_id=state['order_id'],amount=25000,currency='INR',status='captured')}}})
        for _ in range(2):assert c.post('/payments/membership/webhook/',data=body,content_type='application/json',headers={'X-Razorpay-Signature':sign(body,'member-secret')}).status_code==200
        with app.app_context():assert get_db().execute('SELECT status FROM lending_subscriptions WHERE user_id=?',(uid,)).fetchone()[0]=='Active'

def test_event_webhook_duplicate_and_malformed(payment_case):
    app,uid,pid,eid,state=payment_case
    from app import get_db
    with app.test_client() as c:
        t=token(c);c.post('/events/'+str(eid)+'/register/',data={'csrf_guard':t,'name':'Guest','email':'guest@example.test','seats':'1'})
        body=json.dumps({'event':'payment.captured','payload':{'payment':{'entity':dict(id=state['payment_id'],order_id=state['order_id'],amount=10000,currency='INR',status='captured')}}})
        headers={'X-Razorpay-Signature':sign(body,'event-secret'),'X-Razorpay-Event-Id':'event-'+state['order_id']}
        for _ in range(2):assert c.post('/payments/razorpay/webhook/',data=body,content_type='application/json',headers=headers).status_code==200
        with app.app_context():assert get_db().execute('SELECT status FROM event_registrations WHERE event_id=?',(eid,)).fetchone()[0]=='Registered'
        body=json.dumps({'event':'payment.captured','payload':{'payment':[]}})
        assert c.post('/payments/razorpay/webhook/',data=body,content_type='application/json',headers={'X-Razorpay-Signature':sign(body,'event-secret')}).status_code==400

def test_free_event_and_full_capacity(payment_case):
    app,uid,pid,eid,state=payment_case
    from app import get_db
    with app.app_context():get_db().execute('UPDATE events SET fee=0,capacity=1 WHERE id=?',(eid,));get_db().commit()
    with app.test_client() as c:
        t=token(c)
        for email in ('one@example.test','two@example.test'):
            assert c.post('/events/'+str(eid)+'/register/',data={'csrf_guard':t,'name':'Guest','email':email,'seats':'1'}).status_code==302
        with app.app_context():
            rows=get_db().execute('SELECT status,payment_status FROM event_registrations WHERE event_id=?',(eid,)).fetchall();assert len(rows)==1;assert tuple(rows[0])==('Registered','Free')

def test_passenger_wsgi_application():
    from passenger_wsgi import application
    with application.test_client() as c:
        assert c.get('/').status_code==200
