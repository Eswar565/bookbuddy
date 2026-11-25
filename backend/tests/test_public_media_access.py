from datetime import date,timedelta
from pathlib import Path
from bs4 import BeautifulSoup
import pytest

@pytest.fixture
def media_data():
    from app import app,get_db,BASE_DIR
    from werkzeug.security import generate_password_hash
    app.config['TESTING']=True
    folder=BASE_DIR/'static/uploads';folder.mkdir(parents=True,exist_ok=True)
    free=folder/'qa_free_access.pdf';paid=folder/'qa_paid_access.pdf'
    free.write_bytes(b'%PDF-1.4 free test');paid.write_bytes(b'%PDF-1.4 paid test')
    with app.app_context():
        db=get_db()
        uid=db.execute("INSERT INTO users(name,email,password_hash,dob) VALUES(?,?,?,?)",('Test','media-qa@example.test',generate_password_hash('not-a-real-user'),'2000-01-01')).lastrowid
        plan=db.execute("INSERT INTO lending_plans(name,months,kind,book_limit,amount) VALUES('Media QA',3,'Regular',2,100)").lastrowid
        ids=[]
        for name,path,is_paid in [('Free QA',free,0),('Paid QA',paid,1)]:
            ids.append(db.execute("INSERT INTO publications(title,kind,file_path,is_active,is_paid) VALUES(?,?,?,?,?)",(name,'magazine','/static/uploads/'+path.name,1,is_paid)).lastrowid)
        db.commit()
    yield app,uid,plan,ids
    with app.app_context():
        db=get_db();db.execute('DELETE FROM lending_subscriptions WHERE user_id=?',(uid,));db.execute('DELETE FROM publications WHERE id IN (?,?)',ids);db.execute('DELETE FROM users WHERE id=?',(uid,));db.execute('DELETE FROM lending_plans WHERE id=?',(plan,));db.commit()
    free.unlink(missing_ok=True);paid.unlink(missing_ok=True)

def test_free_public_and_paid_gated(media_data):
    app,uid,plan,ids=media_data
    from app import get_db
    with app.test_client() as c:
        for url in ['/library/','/events/','/publications/','/newspaper/','/magazine/','/podcasts/','/submit-contribution/','/membership-options/','/contact/']:
            assert c.get(url, follow_redirects=True).status_code==200,url
        assert c.get('/gallery/').status_code in (200, 301)
        assert c.get('/gallery/', follow_redirects=True).status_code==200
        assert c.get('/static/uploads/qa_free_access.pdf').status_code==200
        free_page=c.get('/publications/?access=free', follow_redirects=True).data
        paid_page=c.get('/publications/?access=paid', follow_redirects=True).data
        assert b'Free QA' in free_page and b'Paid QA' not in free_page
        assert b'Paid QA' in paid_page and b'Free QA' not in paid_page
        response=c.get('/publication/'+str(ids[1])+'/')
        assert response.status_code==200
        assert b'qa_paid_access.pdf' not in response.data
        assert b'paid membership' in response.data.lower()
        assert c.get('/static/uploads/qa_paid_access.pdf').status_code==403
        assert c.get('/static/uploads/qa_paid_access.pdf?download=1').status_code==403
        with c.session_transaction() as s:s['user_id']=uid
        assert c.get('/static/uploads/qa_paid_access.pdf').status_code==403
        with app.app_context():
            db=get_db();db.execute("INSERT INTO lending_subscriptions(user_id,plan_id,status,starts_on,expires_on,payment_status,amount) VALUES(?,?,'Active',?,?,?,100)",(uid,plan,(date.today()-timedelta(days=1)).isoformat(),(date.today()+timedelta(days=30)).isoformat(),'Paid - confirmed by staff'));db.commit()
        assert c.get('/static/uploads/qa_paid_access.pdf').status_code==200
        assert b'qa_paid_access.pdf' in c.get('/publication/'+str(ids[1])+'/').data
        with app.app_context():
            get_db().execute("UPDATE lending_subscriptions SET expires_on='2000-01-01' WHERE user_id=?",(uid,));get_db().commit()
        assert c.get('/static/uploads/qa_paid_access.pdf').status_code==403

def test_guest_book_request_and_private_pages():
    from app import app
    with app.test_client() as c:
        html=c.get('/accounts/login/').get_data(as_text=True)
        token=BeautifulSoup(html,'html.parser').select_one('input[name=csrf_guard]')['value']
        response=c.post('/books/1/request/',data={'csrf_guard':token})
        assert response.status_code in (302,401)
        for path in ('/members/dashboard/','/users/profile/','/admin/dashboard/'):
            response=c.get(path)
            assert response.status_code in (302,401,403),path
