import os
"""Library publications, gallery, events and media editing."""
import calendar, csv, io, json, re
from datetime import datetime, date, timezone, timedelta
from flask import request, session, abort, redirect, render_template, Response
from management import MODELS, NUMBERS, BOOLS, LONG
from library_core import valid_url, IMPORTABLE


def today_ist():return datetime.now(timezone(timedelta(hours=5,minutes=30))).date().isoformat()

def spotify_embed_url(value):
    if not value: return ''
    from urllib.parse import urlsplit
    try: u=urlsplit(value or '')
    except ValueError: return ''
    if u.hostname == 'open.spotify.com':
        path = u.path.strip('/')
        if path.startswith('embed/'): return 'https://open.spotify.com/' + path
        if path.startswith(('episode/', 'show/')): return 'https://open.spotify.com/embed/' + path
    return ''

def embed_source(value):
    """Only known media players may be embedded; arbitrary external HTML is not run."""
    from urllib.parse import urlsplit
    try:u=urlsplit(value or '')
    except ValueError:return ''
    if u.scheme!='https' or u.username or u.password:return ''
    if u.hostname=='open.spotify.com':
        path = u.path.strip('/')
        if re.fullmatch(r'embed/(episode|show)/[A-Za-z0-9]+/?', path): return 'https://open.spotify.com/' + path
        if re.fullmatch(r'(episode|show)/[A-Za-z0-9]+/?', path): return 'https://open.spotify.com/embed/' + path
    if u.hostname in {'www.youtube-nocookie.com','www.youtube.com'} and re.fullmatch(r'/embed/[A-Za-z0-9_-]+',u.path):return 'https://www.youtube-nocookie.com'+u.path
    return ''

def validate_admin_record(kind,v,db):
    e=[]
    if kind=='gallery' and not v.get('image_path'):e.append('Add an image URL or local media path.')
    if kind=='heroes' and not re.fullmatch('[a-z0-9/-]+',v.get('slug','')):e.append('Use a page slug such as about or english.')
    if kind=='publications' and v.get('embed_url') and not embed_source(v['embed_url']):e.append('Use a Spotify episode/show embed URL or a YouTube embed URL.')
    if kind=='coupons':
        if not re.fullmatch('[A-Za-z0-9_-]{2,40}',v.get('code','')):e.append('Coupon code needs 2–40 letters, numbers, hyphens or underscores.')
        v['code']=v.get('code','').upper()
        if v.get('event_id') and not db().execute('SELECT 1 FROM events WHERE id=?',(v['event_id'],)).fetchone():e.append('Event ID does not exist. Use 0 for all events.')
        if v.get('discount_type') not in {'percent','fixed'}:e.append('Choose percent or fixed discount.')
        if v.get('discount_type')=='percent' and v.get('value',0)>100:e.append('Percentage cannot exceed 100.')
        if not v.get('value'):e.append('Discount must be greater than zero.')
    if kind=='events':
        if v.get('booking_closes'):
            try:
                date.fromisoformat(v['booking_closes'])
                if v['booking_closes']>v.get('event_date',''):e.append('Booking closing date must be on or before the event date.')
            except ValueError:e.append('Use a valid booking closing date.')
        try:datetime.strptime(v['event_date'],'%Y-%m-%d')
        except (KeyError,ValueError):e.append('Enter the event date.')
    return e

def install_release9(app,db,render,admin,root):
    with app.app_context():
        changes = {
            'publications': {
                'cover_path': "TEXT DEFAULT ''",
                'embed_url': "TEXT DEFAULT ''",
                'volume': "TEXT DEFAULT ''",
                'issue_number': "TEXT DEFAULT ''",
                'badge_label': "TEXT DEFAULT ''",
                'episode_label': "TEXT DEFAULT ''",
                'position': "INTEGER DEFAULT 0",
            },
            'events': {
                'agenda': "TEXT DEFAULT ''",
                'booking_closes': "TEXT DEFAULT ''",
                'join_url': "TEXT DEFAULT ''",
            },
            'gallery_items': {
                'thumbnail_path': "TEXT DEFAULT ''",
            },
        }
        for table,fields in changes.items():
            have={x[1] for x in db().execute('PRAGMA table_info('+table+')')}
            for name,definition in fields.items():
                if name not in have:
                    try:
                        db().execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')
                    except Exception:
                        pass
        db().executescript('''CREATE TABLE IF NOT EXISTS content_visibility(id INTEGER PRIMARY KEY,section_key TEXT UNIQUE NOT NULL,title TEXT NOT NULL,is_active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS page_heroes(id INTEGER PRIMARY KEY,slug TEXT UNIQUE NOT NULL,title TEXT NOT NULL,eyebrow TEXT DEFAULT '',description TEXT DEFAULT '',image_path TEXT DEFAULT '',is_active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS gallery_items(id INTEGER PRIMARY KEY,title TEXT NOT NULL,description TEXT DEFAULT '',image_path TEXT NOT NULL,thumbnail_path TEXT DEFAULT '',alt_text TEXT DEFAULT '',page_slug TEXT DEFAULT 'home',position INTEGER DEFAULT 0,is_active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS event_coupons(id INTEGER PRIMARY KEY,code TEXT UNIQUE COLLATE NOCASE NOT NULL,event_id INTEGER DEFAULT 0,discount_type TEXT DEFAULT 'percent',value REAL DEFAULT 0,min_amount REAL DEFAULT 0,max_uses INTEGER DEFAULT 0,expires_on TEXT DEFAULT '',is_active INTEGER DEFAULT 1);
        ''')
        try:
            gallery_cols = {x[1] for x in db().execute('PRAGMA table_info(gallery_items)')}
            if 'thumbnail_path' not in gallery_cols:
                db().execute("ALTER TABLE gallery_items ADD COLUMN thumbnail_path TEXT DEFAULT ''")
        except Exception:
            pass
        db().commit()
    MODELS.update({'visibility':('Home section visibility','content_visibility','section_key title is_active'),'heroes':('Page heroes','page_heroes','slug title eyebrow description image_path is_active'),'gallery':('Gallery','gallery_items','image_path alt_text position is_active'),'coupons':('Event coupons','event_coupons','code event_id discount_type value min_amount max_uses expires_on is_active')})
    MODELS['events']=('Events','events','title category description agenda event_date event_time booking_closes location join_url image_path fee capacity is_online is_active')
    MODELS['publications']=('Newspaper, magazines & podcasts','publications','title kind edition volume issue_number badge_label episode_label cover_path file_path embed_url description position published_on is_active')
    NUMBERS.update({'value','min_amount','max_uses','position'});LONG.update({'agenda','description'});IMPORTABLE.update({'heroes','gallery','coupons'})
    app.jinja_env.filters['spotify_embed_filter'] = spotify_embed_url

    def rows(sql,args=()):return [dict(x) for x in db().execute(sql,args)]
    @app.context_processor
    def edition_context():
        path=request.path.strip('/')
        first=path.split('/')[0]
        slug='events' if first in {'reading-circles','contests','calendar'} else ('publications' if first in {'newspaper','news-paper','magazine','podcasts'} else first)
        info=db().execute('SELECT * FROM page_heroes WHERE slug=?',(slug,)).fetchone()
        info=dict(info) if info else None
        if path and not info:
            titles={'shop':'The Book Buddy bookshop.','cart':'Your book basket.','checkout':'Complete your order.','accounts':'Your Book Buddy account.','submit-contribution':'Share your story.'}
            info={'title':titles.get(first,first.replace('-',' ').title()),'eyebrow':'BOOK BUDDY','description':'','image_path':''}
        if first=='events' and re.fullmatch(r'events/\d+',path):
            e=db().execute('SELECT title,description,image_path FROM events WHERE id=?',(int(path.split('/')[1]),)).fetchone()
            if e: info={'title':e['title'],'description':e['description'],'image_path':e['image_path'],'eyebrow':'COMMUNITY / EVENT'}
        if first=='books' and path.split('/')[-1].isdigit():
            book=db().execute('SELECT title,description FROM books WHERE id=?',(int(path.split('/')[-1]),)).fetchone()
            if book: info={'title':book['title'],'description':book['description'],'image_path':'','eyebrow':'LIBRARY'}
        if first=='publication' and path.split('/')[-1].isdigit():
            publication=db().execute('SELECT title,edition,description FROM publications WHERE id=?',(int(path.split('/')[-1]),)).fetchone()
            if publication: info={'title':publication['title'],'description':publication['description'],'image_path':'','eyebrow':'MEDIA / '+publication['edition']}
        visibility={r[0]:r[1] for r in db().execute('SELECT section_key,is_active FROM content_visibility')}
        return {'section_enabled':lambda key:visibility.get(key,1),
                'hero_info':info if path and (not info or info.get('is_active',1)) else None,
                'page_gallery':rows("SELECT * FROM gallery_items WHERE (is_active=1 OR is_active IS NULL) AND (page_slug IN (?,'all') OR page_slug='' OR page_slug IS NULL) ORDER BY position,id",(first,)) if first not in {'gallery','admin',''} else [],
                'home_gallery':rows("SELECT * FROM gallery_items WHERE (is_active=1 OR is_active IS NULL) AND (page_slug IN ('home','all') OR page_slug='' OR page_slug IS NULL) ORDER BY position,id LIMIT 8"),
                'embed_source':embed_source,'site_today':today_ist()}

    @app.before_request
    def v9_dispatch():
        if request.method!='GET':return None
        path=request.path.strip('/')
        if path=='gallery' or path.startswith('gallery/'):
            return None
        if path in {'newspaper', 'magazine', 'podcasts'}:
            return None
        if path in {'news-paper', 'news'}:
            return redirect('/newspaper/', code=301)
        if path in {'podcast'}:
            return redirect('/podcasts/', code=301)
        if path=='publications':
            kind = request.args.get('kind', '').strip().lower()
            if kind in {'news', 'newspaper'}:
                return redirect('/newspaper/', code=301)
            elif kind in {'magazine', 'magazines'}:
                return redirect('/magazine/', code=301)
            elif kind in {'podcast', 'podcasts'}:
                return redirect('/podcasts/', code=301)
            return None
        if path in {'reading-circles','reading-circle'}:
            return redirect('/events/?type=reading-circle', code=301)
        if path in {'contests','contest'}:
            return redirect('/events/?type=contest', code=301)
        if path=='calendar':
            return redirect('/events/', code=301)
        if path=='events':
            return None
    funcs=app.before_request_funcs[None];funcs.remove(v9_dispatch);idx=next(i for i,f in enumerate(funcs) if f.__name__=='access_and_publishing');funcs.insert(idx+1,v9_dispatch)

    def event_listing(path):
        category={'reading-circles':'reading-circle','contests':'contest'}.get(path,request.args.get('category',''))
        view=request.args.get('view','upcoming');chosen=request.args.get('date','');month=request.args.get('month',today_ist()[:7])
        try:year,mon=map(int,month.split('-'));assert 2000<=year<=2100 and 1<=mon<=12
        except (ValueError,AssertionError):year,mon=map(int,today_ist()[:7].split('-'))
        events=rows('SELECT * FROM events WHERE is_active=1'+(' AND category=?' if category in {'reading-circle','contest'} else '')+' ORDER BY event_date,event_time',[category] if category in {'reading-circle','contest'} else [])
        all_events=events[:]
        if chosen:events=[e for e in events if e['event_date']==chosen]
        elif view=='past':events=[e for e in events if e['event_date']<today_ist()];events.reverse()
        elif view!='all':events=[e for e in events if e['event_date']>=today_ist()]
        prev=date(year-1,12,1) if mon==1 else date(year,mon-1,1);nxt=date(year+1,1,1) if mon==12 else date(year,mon+1,1)
        return render('events','events',events=events,all_events=all_events,calendar_weeks=calendar.Calendar(firstweekday=0).monthdayscalendar(year,mon),month_label=date(year,mon,1).strftime('%B %Y'),month_key=f'{year}-{mon:02d}',prev_month=prev.strftime('%Y-%m'),next_month=nxt.strftime('%Y-%m'),selected_view=view,selected_date=chosen,selected_category=category)
    from payments import install_event_payments
    install_event_payments(app,db,render,admin)
