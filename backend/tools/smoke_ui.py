import os,sys,json,tempfile
from pathlib import Path
qa_dir=tempfile.TemporaryDirectory(prefix='bookbuddy-ui-')
os.environ['BOOK_BUDDY_DATABASE']=str(Path(qa_dir.name)/'qa.sqlite3')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app,get_db
from werkzeug.security import generate_password_hash
from bs4 import BeautifulSoup
app.config['TESTING']=True
with app.app_context():
 db=get_db()
 db.execute("INSERT OR IGNORE INTO admin_users(email,name,password_hash,role) VALUES(?,?,?,?)",('qa@example.test','QA Admin',generate_password_hash('temporary'),'super_admin'))
 db.execute("INSERT OR IGNORE INTO users(email,name,password_hash,dob,email_verified) VALUES(?,?,?,?,?)",('reader@example.test','QA Reader',generate_password_hash('temporary'),'2000-01-01',1))
 db.commit();aid=db.execute('SELECT id FROM admin_users WHERE email=?',('qa@example.test',)).fetchone()[0];uid=db.execute('SELECT id FROM users WHERE email=?',('reader@example.test',)).fetchone()[0]
results=[]
paths={'guest':['/','/about/','/library/','/events/','/reading-circles/','/contests/','/publications/?kind=news','/publications/?kind=magazine','/podcasts/','/gallery/','/contact/','/membership-options/','/accounts/login/','/accounts/signup/','/admin/login/'], 'member':['/members/dashboard/','/members/library/','/members/notifications/','/members/support/','/users/profile/','/library/','/events/','/membership-options/'], 'admin':['/admin/dashboard/','/admin/manage/home-sections/','/admin/manage/home-sections/0/','/admin/library-center/','/admin/manage/books/','/admin/library17/','/admin/lending/','/admin/membership-desk/','/admin/plans17/','/admin/manage/events/','/admin/events/','/admin/manage/publications/','/admin/manage/gallery/','/admin/manage/members/','/admin/support17/','/admin/staff17/','/admin/about-editor/','/admin/notifications/','/admin/settings/','/admin/reports17/','/admin/password/']}
with app.test_client() as c:
 for role,urls in paths.items():
  with c.session_transaction() as s:
   s.clear()
   if role=='member':s['user_id']=uid
   if role=='admin':s['admin_id']=aid
  for url in urls:
   try:
    response=c.get(url,follow_redirects=True);html=response.get_data(as_text=True);soup=BeautifulSoup(html,'html.parser')
    assert response.status_code==200,(url,response.status_code)
    assert soup.select_one('link[href*="folio.css"]'),url
    for tag in soup.select('link[rel=stylesheet],script[src]'):
     src=tag.get('href') or tag.get('src')
     if src.startswith('/static/'):assert c.get(src).status_code==200,(url,src)
    results.append({'role':role,'url':url,'status':response.status_code,'redirected':len(response.history)>0})
   except Exception as e:results.append({'role':role,'url':url,'error':str(e)})
print(json.dumps(results,indent=2))
assert all('error' not in x for x in results)
