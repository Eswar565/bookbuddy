from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from pathlib import Path

def test_home_section_admin_edit_upload_and_hide():
    from app import app,get_db,BASE_DIR
    app.config['TESTING']=True
    with app.app_context():
        db=get_db();aid=db.execute("INSERT INTO admin_users(email,name,password_hash,role) VALUES('home-qa@example.test','Editor','unused','super_admin')").lastrowid;db.commit()
    path=None;sid=None
    try:
        with app.test_client() as c:
            with c.session_transaction() as s:s['admin_id']=aid
            response=c.get('/admin/manage/home-sections/0/')
            assert response.status_code==200
            token=BeautifulSoup(response.data,'html.parser').select_one('input[name=csrf_guard]')['value']
            image=BytesIO();Image.new('RGB',(30,30),'navy').save(image,format='PNG');image.seek(0)
            data=dict(csrf_guard=token,csrf_token=token,section_key='qa-extra',title='QA unique section',description='Edited from admin',kicker='TEST',image_path='',image_alt='QA image',button_label='Explore',url='/library/',position='99',is_active='1',asset_image_path=(image,'example.png'))
            response=c.post('/admin/manage/home-sections/0/',data=data,content_type='multipart/form-data')
            assert response.status_code==302,response.data[:500]
            with app.app_context():
                row=dict(get_db().execute("SELECT * FROM homepage_sections WHERE section_key='qa-extra'").fetchone());sid=row['id'];path=row['image_path'];assert path.startswith('/media/')
            assert b'QA unique section' in c.get('/').data
            assert path.encode() in c.get('/').data
            assert c.get(path).status_code==200
            data={k:v for k,v in row.items() if k!='id'};data.update(csrf_guard=token,csrf_token=token,is_active='0',image_path='https://example.com/template.png')
            assert c.post('/admin/manage/home-sections/'+str(sid)+'/',data=data).status_code==302
            assert b'QA unique section' not in c.get('/').data
    finally:
        with app.app_context():
            db=get_db();db.execute("DELETE FROM homepage_sections WHERE section_key='qa-extra'");db.execute('DELETE FROM admin_audit WHERE admin_id=?',(aid,));db.execute('DELETE FROM admin_users WHERE id=?',(aid,));db.commit()
        if path:(BASE_DIR/path.lstrip('/')).unlink(missing_ok=True)

def test_reader_language_combinations_and_calendar():
    from app import app,get_db
    ids=[]
    with app.app_context():
        db=get_db()
        for title,audience,lang in [('QA Kids Tamil','kids','Tamil'),('QA Adult English','adult','English'),('QA All Hindi','all','Hindi')]:
            ids.append(db.execute('INSERT INTO books(title,author,audience,language) VALUES(?,?,?,?)',(title,'QA Filter Author',audience,lang)).lastrowid)
        eid=db.execute("INSERT INTO events(title,event_date,event_time,is_active) VALUES('QA calendar event','2030-05-12','10:00',1)").lastrowid;db.commit()
    try:
        with app.test_client() as c:
            result=c.get('/library/?q=QA&audience=kids&language=Tamil');assert result.status_code==200
            soup=BeautifulSoup(result.data,'html.parser');titles=[e.get_text() for e in soup.select('.bb-book-title')]
            assert titles==['QA Kids Tamil']
            assert soup.select_one('.catalogue-sidebar')
            assert c.get('/library/?q=QA&audience=adult&language=Hindi').status_code==200
            result=c.get('/home-calendar/?month=2030-05');assert result.status_code==200
            assert b'data-event-date="2030-05-12"' in result.data
            assert ('/events/'+str(eid)+'/#event-registration').encode() in result.data
            assert c.get('/home-calendar/?month=not-a-date').status_code==200
    finally:
        with app.app_context():
            db=get_db();db.execute('DELETE FROM books WHERE id IN (?,?,?)',ids);db.execute('DELETE FROM events WHERE id=?',(eid,));db.commit()
