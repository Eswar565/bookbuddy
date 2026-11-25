"""Administrator-managed sections for the library, events, About and media pages."""
import json
import re
import sqlite3
from urllib.parse import urlparse, parse_qs
from flask import request, session, abort, redirect, flash, render_template

PAGES = {'home':'Home','about':'About','library':'Library','events':'Upcoming Events','reading-circles':'Reading Circles','contests':'Contests','publications':'Media / Newspaper / Magazine','podcasts':'Podcasts','gallery':'Gallery','membership-options':'Library membership','how-to-borrow':'How to borrow','contact':'Contact'}
KINDS = ['text','cards','steps','faq','checklist','video','callout','links','quote','exercise']


def video_embed(value):
    """Only supported video providers; never accept raw iframe HTML."""
    if not value:return ''
    try:
        p=urlparse(value)
        if p.scheme!='https' or p.username or p.password or p.port not in (None,443):return ''
    except ValueError:return ''
    host=(p.hostname or '').lower();ident=''
    if host in {'youtube.com','www.youtube.com','www.youtube-nocookie.com'}:
        if p.path=='/watch':ident=parse_qs(p.query).get('v',[''])[0]
        elif p.path.startswith('/embed/'):ident=p.path.split('/')[-1]
    elif host=='youtu.be':ident=p.path.strip('/')
    if re.fullmatch(r'[A-Za-z0-9_-]{11}',ident):return 'https://www.youtube-nocookie.com/embed/'+ident
    if host in {'vimeo.com','www.vimeo.com','player.vimeo.com'} and re.fullmatch(r'/(?:video/)?\d+',p.path):return 'https://player.vimeo.com/video/'+p.path.split('/')[-1]
    return ''


def install_flexible(app, db, render):
    with app.app_context():
        db().executescript('''
        CREATE TABLE IF NOT EXISTS page_sections23(id INTEGER PRIMARY KEY,page_slug TEXT NOT NULL,section_key TEXT NOT NULL,title TEXT NOT NULL,kind TEXT NOT NULL DEFAULT 'text',body TEXT NOT NULL DEFAULT '',items_json TEXT NOT NULL DEFAULT '[]',video_url TEXT NOT NULL DEFAULT '',position INTEGER NOT NULL DEFAULT 0,placement TEXT NOT NULL DEFAULT 'after',is_active INTEGER NOT NULL DEFAULT 0,premium INTEGER NOT NULL DEFAULT 0,UNIQUE(page_slug,section_key));
        ''')
        # Clean only obsolete demonstration sections, preserving administrator content.
        db().execute("DELETE FROM page_sections23 WHERE section_key LIKE 'demo23-%'")
        db().commit()

    def staff():
        a=db().execute('SELECT * FROM admin_users WHERE id=? AND is_active=1',(session.get('admin_id'),)).fetchone()
        if not a:return None
        return dict(a)
    def admin_required():
        a=staff()
        if not a:abort(401)
        if a['role'] not in {'super_admin','org_admin'}:abort(403)
        return a
    def premium(scope=None):
        if staff():return True
        from portal import today
        d=today().isoformat()
        if db().execute("SELECT 1 FROM lending_subscriptions WHERE user_id=? AND status IN ('Active','Scheduled') AND starts_on<=? AND expires_on>=?",(session.get('user_id'),d,d)).fetchone():return True
        legacy=db().execute("SELECT p.scopes FROM memberships m JOIN plans p ON p.id=m.plan_id WHERE m.user_id=? AND m.status='Active' AND m.starts_on<=? AND m.expires_on>=?",(session.get('user_id'),d,d))
        return any((scope in {x.strip() for x in row['scopes'].split(',')}) if scope else bool(row['scopes'].strip()) for row in legacy)
    def field(key,maxlen=10000,required=False):
        v=request.form.get(key,'').strip()
        if len(v)>maxlen or (required and not v):abort(400,'Check '+key.replace('_',' '))
        return v
    def choice(key,values,default):
        v=request.form.get(key,default)
        if v not in values:abort(400,'Invalid '+key)
        return v
    def number(key):
        try:v=int(request.form.get(key,'0'))
        except ValueError:abort(400,'Invalid number')
        if not 0<=v<=10000:abort(400,'Position must be 0–10000')
        return v
    def audit(action):db().execute('INSERT INTO admin_audit(admin_id,action) VALUES(?,?)',(session.get('admin_id'),action))
    def admin_page(template,title,**kw):
        from management import MODELS
        return render_template('workspace/'+template+'.html',admin=staff(),models=MODELS,title=title,active='flexible',**kw)
    def page_registry():
        pages=dict(PAGES)
        return pages
    def page_key():
        p=request.path.strip('/')
        aliases={'':'home','membership':'membership-options','magazine':'publications','newspaper':'publications','library-catalogue':'library'}
        return aliases.get(p,p) if '/' not in p else ''

    def catalogue23():
        from app import paged_books
        return render('library','library',**paged_books())
    app.view_functions['modern_library']=catalogue23

    @app.context_processor
    def flexible_context():
        key=page_key()
        sections=[]
        if key in page_registry():
            for row in db().execute("SELECT * FROM page_sections23 WHERE page_slug=? AND is_active=1 AND section_key NOT LIKE 'demo23-%' ORDER BY position,id",(key,)):
                s=dict(row);s['locked']=bool(s['premium'] and not premium(key))
                s['items']=[] if s['locked'] else json.loads(s['items_json'])
                if s['locked']:s['body']='';s['video_url']=''
                s['embed']=video_embed(s['video_url']);sections.append(s)
        return {'flex_sections':sections,'flex_page':key,'has_premium23':premium,'video_embed23':video_embed}

    @app.route('/admin/page-sections/',methods=['GET','POST'])
    def page_sections23():
        admin_required()
        slug=request.values.get('page','home')
        pages=page_registry()
        if slug not in pages:abort(400,'Choose a page')
        current=None
        if request.args.get('edit'):
            current=db().execute('SELECT * FROM page_sections23 WHERE id=? AND page_slug=?',(request.args['edit'],slug)).fetchone()
            if not current:abort(404)
            current=dict(current);current['items_text']='\n'.join(' | '.join([x.get('title',''),x.get('text',''),x.get('url','')]) for x in json.loads(current['items_json']))
        if request.method=='POST':
            ident=field('id',20)
            old=db().execute('SELECT * FROM page_sections23 WHERE id=? AND page_slug=?',(ident,slug)).fetchone() if ident else None
            if ident and not old:abort(404)
            if field('action',20)=='toggle':
                if not old:abort(404)
                db().execute('UPDATE page_sections23 SET is_active=1-is_active WHERE id=?',(ident,))
            else:
                title=field('title',160,True);kind=choice('kind',KINDS,'text');body=field('body',20000)
                video=field('video_url',500)
                try:embed=video_embed(video)
                except ValueError:embed=''
                if video and not embed:abort(400,'Use a valid HTTPS YouTube or Vimeo video URL.')
                items=[]
                for line in field('items',20000).splitlines():
                    parts=(line.split('|',2)+['',''])[:3];t,txt,url=[x.strip() for x in parts]
                    if url and (not url.startswith('/') or url.startswith('//') or '\\' in url):abort(400,'Links must use a local path beginning with one slash.')
                    if t:items.append({'title':t,'text':txt,'url':url})
                if len(items)>30:abort(400,'Use up to 30 items per section.')
                values=(title,kind,body,json.dumps(items),video,number('position'),choice('placement',['before','after'],'after'),int('is_active' in request.form),int('premium' in request.form))
                if old:db().execute('UPDATE page_sections23 SET title=?,kind=?,body=?,items_json=?,video_url=?,position=?,placement=?,is_active=?,premium=? WHERE id=?',(*values,ident))
                else:
                    import secrets
                    db().execute('INSERT INTO page_sections23(page_slug,section_key,title,kind,body,items_json,video_url,position,placement,is_active,premium) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(slug,secrets.token_hex(8),*values))
            audit('Page section saved: '+slug);db().commit();flash('Section saved.','success');return redirect('/admin/page-sections/?page='+slug)
        rows=[dict(r) for r in db().execute('SELECT * FROM page_sections23 WHERE page_slug=? ORDER BY position,id',(slug,))]
        return admin_page('page_sections23','Page sections',pages=pages,slug=slug,rows=rows,current=current or {},kinds=KINDS)

