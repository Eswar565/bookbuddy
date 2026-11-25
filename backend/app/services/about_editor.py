"""Book Buddy: local About publishing and public-page/admin directory.

Do not add shadow copies of existing pages. Structured page content lives in
site_content, generic CMS pages in cms_pages.
"""
from __future__ import annotations

import json
import re
from html import unescape
from urllib.parse import urlparse

from flask import abort, flash, redirect, render_template, request

ABOUT_FIELDS = (
    'about_heading', 'about_philosophy_subheading', 'about_philosophy_intro',
    'about_philosophy_body', 'about_ikigai_url',
    'about_video_heading', 'about_video_intro',
)


def plain_legacy_body(body: str) -> str:
    """Convert legacy CMS paragraph HTML to display text (not unsafe markup)."""
    if not re.search(r'</?[a-z][^>]*>', body, flags=re.I):
        return body.strip()
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body, 'html.parser')
    for element in soup(['script', 'style', 'iframe']):
        element.decompose()
    for tag in soup.find_all(['p','div','br','li','h1','h2','h3','h4']):
        if tag.name == 'br':
            tag.replace_with('\n')
        else:
            tag.insert_after('\n\n')
    return unescape(soup.get_text()).strip()


def mirror_about_cms_save(connection, record):
    """Legacy 'Website pages > About' saves immediately affect the live page."""
    mapping = {
        'title': 'about_heading',
        'summary': 'about_philosophy_intro',
        'body': 'about_philosophy_body',
    }
    for origin, target in mapping.items():
        value = str(record.get(origin, '') or '')
        if origin == 'body':
            value = plain_legacy_body(value)
        connection.execute('''INSERT INTO site_content(content_key,content_value)
            VALUES (?,?) ON CONFLICT(content_key)
            DO UPDATE SET content_value=excluded.content_value''', (target, value))
    connection.execute('''INSERT INTO site_content(content_key,content_value)
            VALUES ('about_text',?) ON CONFLICT(content_key)
            DO UPDATE SET content_value=excluded.content_value''',
                       (plain_legacy_body(str(record.get('body',''))),))


def mirror_contact_cms_save(connection, record):
    """Keep contact-page prose changes visible alongside the working form."""
    for key,value in {
        'contact_heading':str(record.get('title','')),
        'contact_intro':plain_legacy_body(str(record.get('body',''))),
    }.items():
        connection.execute('''INSERT INTO site_content(content_key,content_value) VALUES(?,?)
            ON CONFLICT(content_key) DO UPDATE SET content_value=excluded.content_value''',(key,value))


def valid_image_url(value):
    if not value: return True
    if value.startswith('/') and not value.startswith('//') and not value.startswith('/\\'):
        return '\\' not in value and '\r' not in value and '\n' not in value
    try:
        parsed = urlparse(value)
        return parsed.scheme == 'https' and bool(parsed.netloc) and not parsed.username and not parsed.password
    except ValueError:
        return False


def validate_videos(records):
    from flexible import video_embed
    out=[]
    for item in records:
        title=str(item.get('title','')).strip()
        url=str(item.get('url','')).strip()
        if not title and not url:
            continue
        if not title or not url or not video_embed(url):
            raise ValueError('Each video needs a title and a valid HTTPS YouTube or Vimeo URL.')
        out.append({'title':title[:160], 'description':str(item.get('description','')).strip()[:600], 'url':url})
    if len(out)>8:
        raise ValueError('Use at most eight videos.')
    return out


# Page inventory: public URL, editing endpoint, and the database or module
# actually used to render it. These are not fabricated generic CMS mirrors.
PUBLIC_PAGES = [
    ('Home', '/', '/admin/manage/home-sections/', 'Library homepage & community calendar', 'homepage_sections / site_content'),
    ('About', '/about/', '/admin/about-editor/', 'Library story and videos', 'site_content'),
    ('Library', '/library/', '/admin/library-center/', 'Book catalogue, stock, lending and membership', 'books / copies17'),
    ('Membership plans', '/membership-options/', '/admin/plans17/', 'Borrowing limits and plan pricing', 'lending_plans'),
    ('How to borrow', '/how-to-borrow/', '/admin/how-to-borrow-editor/', 'How to borrow guidelines & inquiry form', 'how_to_borrow_page'),
    ('Partner with us', '/work-with-us/', '/admin/manage/partners/', 'Collaboration proposals and partner enquiries', 'partner_submissions'),
    ('Reading circles', '/reading-circles/', '/admin/manage/events/?f_category=reading-circle', 'Reading circle events', 'events'),
    ('Contests', '/contests/', '/admin/manage/events/?f_category=contest', 'Reading contests', 'events'),
    ('Upcoming events', '/events/', '/admin/manage/events/?f_category=upcoming', 'Event calendar and registration', 'events'),
    ('Newspaper', '/publications/?kind=news', '/admin/manage/publications/?f_kind=news', 'News editions', 'publications'),
    ('Magazine', '/publications/?kind=magazine', '/admin/manage/publications/?f_kind=magazine', 'Magazines', 'publications'),
    ('Podcasts', '/podcasts/', '/admin/manage/publications/?f_kind=podcast', 'Audio publications', 'publications'),
    ('Gallery', '/about/#gallery', '/admin/about-editor/#gallery', 'Library and event photographs (on About page)', 'gallery_items'),
    ('Contact', '/contact/', '/admin/manage/enquiries/', 'Contact enquiries', 'contact_submissions'),
    ('User dashboard', '/members/dashboard/', '/admin/manage/members/', 'Member accounts and borrowing', 'users / lending_loans'),
]


def preserve_existing_about_copy(connection):
    """One-time non-destructive import of previously saved About CMS text.

    Ignore known sample data; preserve already-published philosophy text.
    """
    marker='about-content-copied'
    if connection.execute('SELECT 1 FROM schema_updates WHERE version=?',(marker,)).fetchone():
        return
    active=connection.execute("SELECT content_value FROM site_content WHERE content_key='about_philosophy_body'").fetchone()
    if not active or not (active[0] or '').strip():
        legacy=connection.execute("SELECT title,summary,body FROM cms_pages WHERE slug='about'").fetchone()
        old=connection.execute("SELECT content_value FROM site_content WHERE content_key='about_text'").fetchone()
        legacy_text=plain_legacy_body(legacy['body']) if legacy else ''
        old_text=(old[0] if old else '').strip()
        def real(text):
            demo=('Discover books and take part in community activities.',
                  'Our demo library supports readers',
                  'A welcoming space for reading.')
            return bool(text and not any(fragment.lower() in text.lower() for fragment in demo))
        copy=legacy_text if real(legacy_text) else (old_text if real(old_text) else '')
        if copy:
            connection.execute("INSERT OR REPLACE INTO site_content(content_key,content_value) VALUES('about_philosophy_body',?)",(copy,))
            if legacy and real(legacy_text):
                if legacy['summary']:
                    connection.execute("INSERT OR REPLACE INTO site_content(content_key,content_value) VALUES('about_philosophy_intro',?)",(legacy['summary'],))
                if legacy['title'] and legacy['title']!='About BookBuddy':
                    connection.execute("INSERT OR REPLACE INTO site_content(content_key,content_value) VALUES('about_heading',?)",(legacy['title'],))
    connection.execute('INSERT OR IGNORE INTO schema_updates(version) VALUES (?)',(marker,))


def install_about_editor(app, db, current_admin):
    with app.app_context():
        for key, value in {
            'about_philosophy_subheading': '',
            'about_video_heading': '',
            'about_video_intro': '',
            'about_videos_json': '',
            'contact_heading':'',
            'contact_intro':'',
        }.items():
            db().execute('INSERT OR IGNORE INTO site_content(content_key,content_value) VALUES (?,?)', (key,value))
        preserve_existing_about_copy(db())
        db().commit()

    def require_editor():
        user=current_admin()
        if not user:
            return None,redirect('/admin/login/')
        row=db().execute('SELECT role,is_active FROM admin_users WHERE id=?',(user['id'],)).fetchone()
        if not row or not row['is_active'] or row['role'] not in {'super_admin','org_admin'}:
            abort(403)
        return user,None

    @app.route('/admin/about/', methods=['GET','POST'])
    @app.route('/admin/about-editor/', methods=['GET','POST'])
    def about_editor():
        user,denied=require_editor()
        if denied is not None: return denied
        import gallery_service
        if request.method=='POST':
            gallery_action = request.form.get('gallery_action') or request.form.get('admin_action')
            if gallery_action:
                if gallery_action == 'save_settings':
                    pill = request.form.get('gallery_pill', '')
                    heading = request.form.get('gallery_heading', '')
                    gallery_service.save_gallery_settings(db, pill, heading)
                    flash('Gallery settings saved successfully.', 'success')
                elif gallery_action == 'upload':
                    files = request.files.getlist('photos')
                    category = request.form.get('category', 'reading-moments')
                    errs = gallery_service.add_gallery_photos(db, files, category=category)
                    if errs:
                        for err in errs: flash(err, 'danger')
                    else:
                        flash(f'Uploaded {len(files)} photo(s) successfully.', 'success')
                elif gallery_action == 'update_category':
                    try:
                        gid = int(request.form.get('item_id', '0'))
                        cat = request.form.get('category', 'reading-moments')
                        gallery_service.update_gallery_item_category(db, gid, cat)
                        flash('Photo category updated.', 'success')
                    except ValueError: pass
                elif gallery_action == 'reorder':
                    pos_dict = {}
                    for key in request.form:
                        if key.startswith('pos_'):
                            try:
                                gid = int(key.split('_')[1])
                                pos_dict[gid] = int(request.form[key])
                            except ValueError: pass
                    if pos_dict:
                        gallery_service.reorder_gallery(db, pos_dict)
                        flash('Photo order updated.', 'success')
                elif gallery_action == 'toggle':
                    try:
                        gid = int(request.form.get('item_id', '0'))
                        gallery_service.toggle_gallery_active(db, gid)
                        flash('Photo visibility toggled.', 'success')
                    except ValueError: pass
                elif gallery_action == 'delete':
                    try:
                        gid = int(request.form.get('item_id', '0'))
                        gallery_service.delete_gallery_item(db, gid)
                        flash('Photo removed from gallery.', 'success')
                    except ValueError: pass
                elif gallery_action == 'update_alt':
                    try:
                        gid = int(request.form.get('item_id', '0'))
                        alt = request.form.get('alt_text', '')
                        gallery_service.update_gallery_item_alt(db, gid, alt)
                        flash('Alt text updated.', 'success')
                    except ValueError: pass
                return redirect('/admin/about-editor/#gallery')

            values={key:request.form.get(key,'').strip() for key in ABOUT_FIELDS}
            if request.files.get('asset_about_ikigai_url') and request.files['asset_about_ikigai_url'].filename:
                try:
                    store_media = app.extensions.get('bookbuddy_store_media_v13')
                    if store_media:
                        values['about_ikigai_url'] = store_media('asset_about_ikigai_url', 'about', 'image')
                except Exception as exc:
                    abort(400, str(exc))
            for key, value in values.items():
                if len(value)>(40000 if key=='about_philosophy_body' else 3000):
                    abort(400,'About text is too long in '+key)
            if not valid_image_url(values['about_ikigai_url']):
                abort(400,'Ikigai image must have a valid HTTPS URL or local /static/ or /media/ path.')
            if not values['about_heading']:
                abort(400,'Please provide a public About heading.')
            raw_videos=[{
                'title':request.form.get(f'video_title_{n}',''),
                'url':request.form.get(f'video_url_{n}',''),
                'description':request.form.get(f'video_description_{n}',''),
            } for n in range(1,9)]
            try:
                videos=validate_videos(raw_videos)
            except ValueError as exc:
                abort(400,str(exc))
            connection=db()
            try:
                for key,value in values.items():
                    connection.execute('''INSERT INTO site_content(content_key,content_value)
                        VALUES (?,?) ON CONFLICT(content_key)
                        DO UPDATE SET content_value=excluded.content_value''',(key,value))
                connection.execute('''INSERT INTO site_content(content_key,content_value)
                    VALUES ('about_videos_json',?) ON CONFLICT(content_key)
                    DO UPDATE SET content_value=excluded.content_value''',
                                   (json.dumps(videos,ensure_ascii=False),))
                connection.execute('''INSERT INTO site_content(content_key,content_value)
                    VALUES ('about_text',?) ON CONFLICT(content_key)
                    DO UPDATE SET content_value=excluded.content_value''',
                                   (values['about_philosophy_body'],))
                # Keep legacy generic admin record in sync for exports and SEO.
                connection.execute('''UPDATE cms_pages SET title=?,summary=?,body=?,is_active=1
                    WHERE slug='about' ''', (
                    values['about_heading'],values['about_philosophy_intro'],
                    values['about_philosophy_body']))
                connection.execute('INSERT INTO admin_audit(admin_id,action) VALUES (?,?)',
                                   (user['id'],'Updated About public page'))
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            flash('About page published. Open the public preview to see the updated text.', 'success')
            return redirect('/admin/about-editor/?saved=1')
        content={r['content_key']:r['content_value'] for r in db().execute('SELECT content_key,content_value FROM site_content')}
        content.setdefault('about_heading','Our Ikigai')
        if content['about_heading']=='About BookBuddy': content['about_heading']='Our Ikigai'
        content.setdefault('about_philosophy_body','')
        try:
            videos=json.loads(content.get('about_videos_json') or 'null')
            if not isinstance(videos,list): videos=[]
        except (TypeError,ValueError): videos=[]
        cached_body=''
        gallery_items = gallery_service.get_admin_gallery(db)
        gallery_settings = gallery_service.get_gallery_settings(db)
        from management import MODELS
        return render_template('workspace/about_editor.html',title='Edit About page',active='about-editor',
                               models=MODELS,admin=user,settings=content,videos=videos,
                               gallery_items=gallery_items,gallery_settings=gallery_settings,
                               cached_body=cached_body)

    @app.get('/admin/page-map/')
    def page_map():
        user,denied=require_editor()
        if denied is not None: return denied
        from management import MODELS
        rows=[]
        built_in_slugs={path.strip('/') for _,path,_,_,_ in PUBLIC_PAGES if path!='/' }
        for label,url,edit,desc,source in PUBLIC_PAGES:
            match=db().execute('SELECT id,is_active FROM cms_pages WHERE slug=?',(url.split('?',1)[0].strip('/'),)).fetchone()
            rows.append({'label':label,'url':url,'edit':edit,'desc':desc,'source':source,
                         'cms_shadow':bool(match and label not in {'About','How to borrow'}),
                         'enabled':not match or bool(match['is_active'])})
        return render_template('workspace/page_map.html',title='Website page map',active='page-map',
                               models=MODELS,admin=user,pages=rows)
