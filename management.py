"""Content workspace and shared inner-page publishing for Book Buddy."""
import csv
import io
import json
import math
import re
import secrets
from datetime import date, timedelta
from functools import wraps
from urllib.parse import urlsplit

from flask import abort, flash, redirect, render_template, request, session, Response, make_response
from werkzeug.security import check_password_hash, generate_password_hash

# Only these fields can be edited. Password hashes are never exposed.
MODELS = {
    'books': ('Books', 'books', 'title author collection age_group language price stock description image_path is_active archived audience'),
    'events': ('Events', 'events', 'title description event_date event_time location fee capacity is_online is_active'),
    'publications': ('Publications', 'publications', 'title kind description edition file_path published_on is_active download_count'),
    'pages': ('Website pages', 'cms_pages', 'slug title summary body is_active'),
    'navigation': ('Navigation & footer links', 'site_navigation', 'group_name label url position is_active'),
    'working-hours': ('Working hours', 'working_hours', 'days hours closed position is_active'),
    'hours': ('Working hours', 'working_hours', 'days hours closed position is_active'),
    'working_hours': ('Working hours', 'working_hours', 'days hours closed position is_active'),
    'orders': ('Orders', 'orders', 'customer_name email phone address total status'),
    'registrations': ('Event registrations', 'event_registrations', 'event_id name email phone seats amount status'),
    'requests': ('Borrowing requests', 'book_requests', 'book_title user_name member_id phone_number request_type status'),
    'members': ('Members', 'users', 'name email'),
    'subscribers': ('Subscribers', 'subscribers', 'email edition_name'),
    'enquiries': ('Enquiries', 'contact_submissions', 'full_name email subject phone message'),
    'partners': ('Partner enquiries', 'partner_submissions', 'full_name email phone organisation proposal_type message status'),
    'contributions': ('Reader contributions', 'reader_contributions', 'student_name email title category body status'),
}
READ_ONLY = {'orders','registrations','members','requests','enquiries','subscribers','contributions'}
NUMBERS = {'price','fee','stock','capacity','seats','amount','total','event_id','position','download_count'}
BOOLS = {'is_active','is_online'}
LONG = {'body','description','summary','message','address','proposal_type','hours'}

def install_management(app, get_db, render_site, current_admin, base_dir):
    with app.app_context():
        get_db().executescript('''CREATE TABLE IF NOT EXISTS cms_pages (
            id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '', body TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS admin_audit (
            id INTEGER PRIMARY KEY, admin_id INTEGER, action TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS site_navigation (
            id INTEGER PRIMARY KEY, group_name TEXT NOT NULL, label TEXT NOT NULL,
            url TEXT NOT NULL, position INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1);
            CREATE TABLE IF NOT EXISTS reader_contributions (
            id INTEGER PRIMARY KEY, student_name TEXT, email TEXT, title TEXT, category TEXT,
            body TEXT, status TEXT DEFAULT 'Pending');
            CREATE TABLE IF NOT EXISTS working_hours (
            id INTEGER PRIMARY KEY, days TEXT NOT NULL DEFAULT '', hours TEXT NOT NULL DEFAULT '',
            closed TEXT NOT NULL DEFAULT '', position INTEGER NOT NULL DEFAULT 0, is_active INTEGER NOT NULL DEFAULT 1);''')
        if get_db().execute('SELECT COUNT(*) FROM working_hours').fetchone()[0] == 0:
            get_db().executescript('''
                INSERT INTO working_hours(days, hours, closed, position, is_active) VALUES ('Tuesday – Sunday', '10:00 AM – 1:00 PM\n4:30 PM – 8:30 PM', '', 1, 1);
                INSERT INTO working_hours(days, hours, closed, position, is_active) VALUES ('Monday', '', 'Closed', 2, 1);
            ''')
        get_db().executescript('''
            CREATE TABLE IF NOT EXISTS site_settings (
                id INTEGER PRIMARY KEY,
                theme TEXT NOT NULL DEFAULT 'maroon',
                font TEXT NOT NULL DEFAULT 'inter',
                custom_p TEXT NOT NULL DEFAULT '#7a1230',
                custom_bg TEXT NOT NULL DEFAULT '#f7f8fc',
                custom_card TEXT NOT NULL DEFAULT '#ffffff',
                custom_tx TEXT NOT NULL DEFAULT '#1a1a2e'
            );
        ''')
        cols = [r[1] for r in get_db().execute("PRAGMA table_info(site_settings)").fetchall()]
        for col, default in [
            ('theme', "'maroon'"),
            ('font', "'inter'"),
            ('custom_p', "'#7a1230'"),
            ('custom_bg', "'#f7f8fc'"),
            ('custom_card', "'#ffffff'"),
            ('custom_tx', "'#1a1a2e'")
        ]:
            if col not in cols:
                get_db().execute(f"ALTER TABLE site_settings ADD COLUMN {col} TEXT NOT NULL DEFAULT {default}")
        if not get_db().execute("SELECT id FROM site_settings WHERE id=1").fetchone():
            get_db().execute(
                "INSERT INTO site_settings (id, theme, font, custom_p, custom_bg, custom_card, custom_tx) "
                "VALUES (1, 'maroon', 'inter', '#7a1230', '#f7f8fc', '#ffffff', '#1a1a2e')"
            )
        get_db().commit()

    @app.context_processor
    def appearance_context():
        theme = 'maroon'
        font = 'inter'
        custom_p = '#7a1230'
        custom_bg = '#f7f8fc'
        custom_card = '#ffffff'
        custom_tx = '#1a1a2e'
        try:
            row = get_db().execute('SELECT theme, font, custom_p, custom_bg, custom_card, custom_tx FROM site_settings WHERE id=1').fetchone()
            if row:
                theme = row['theme'] or 'maroon'
                font = row['font'] or 'inter'
                custom_p = row['custom_p'] or '#7a1230'
                custom_bg = row['custom_bg'] or '#f7f8fc'
                custom_card = row['custom_card'] or '#ffffff'
                custom_tx = row['custom_tx'] or '#1a1a2e'
        except Exception:
            pass

        custom_theme_style = ""
        custom_btn_tx = '#ffffff'
        if theme == 'custom':
            custom_theme_style = f"<style>:root{{--p:{custom_p};--bg:{custom_bg};--card:{custom_card};--tx:{custom_tx};}}</style>"
            try:
                def _rel_lum(h):
                    h = h.lstrip('#')
                    r, g, b = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
                    def _adj(c):
                        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
                    return 0.2126 * _adj(r) + 0.7152 * _adj(g) + 0.0722 * _adj(b)
                lp = _rel_lum(custom_p)
                c_w = 1.05 / (lp + 0.05) if 1.0 >= lp else (lp + 0.05) / 0.05
                c_b = (lp + 0.05) / 0.05
                custom_btn_tx = '#ffffff' if c_w >= c_b else '#000000'
            except Exception:
                custom_btn_tx = '#ffffff'

        return {
            'site_theme': theme,
            'site_font': font,
            'custom_p': custom_p,
            'custom_bg': custom_bg,
            'custom_card': custom_card,
            'custom_tx': custom_tx,
            'custom_btn_tx': custom_btn_tx,
            'custom_theme_style': custom_theme_style
        }

    @app.context_processor
    def navigation_context():
        groups={}
        for row in get_db().execute('SELECT * FROM site_navigation WHERE is_active=1 ORDER BY position,id'):
            groups.setdefault(row['group_name'],[]).append(dict(row))
        return {'navigation_groups':groups}

    def token():
        return session.setdefault('csrf_token', secrets.token_urlsafe(32))
    app.jinja_env.globals['workspace_token'] = token

    @app.after_request
    def secure_forms(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='SAMEORIGIN'
        response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
        if response.mimetype=='text/html' and not response.direct_passthrough:
            text=response.get_data(as_text=True)
            if request.path.startswith('/legacy/'):
                text=text.replace('</head>','<style>header,.headerarea,.footerarea,.mobile-off-canvas-active,.scrolling-ticker{display:none!important}body{background:#fff!important}</style></head>')
            hidden='<input type="hidden" name="csrf_guard" value="'+token()+'">'
            text=re.sub(r'(<form\b[^>]*method=[\"\x27]post[\"\x27][^>]*>)',lambda m:m[0]+hidden,text,flags=re.I)
            response.set_data(text)
        if request.path.startswith('/admin/') or response.mimetype == 'text/html':
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    @app.before_request
    def secure_mutations():
        if request.method=='POST':
            if request.endpoint in {'razorpay_webhook_v9','membership_webhook17'}: return None
            expected=token()
            actual=request.form.get('csrf_guard') or request.form.get('csrf_token') or request.headers.get('X-CSRFToken','')
            if not actual or not secrets.compare_digest(actual,expected):
                abort(400,'Reload the page before submitting this form.')

    @app.post('/contact/')
    def contact_submit():
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip()
        message=request.form.get('message','').strip()
        if not name or '@' not in email or not message: abort(400,'Complete all fields.')
        get_db().execute('INSERT INTO contact_submissions(full_name,email,subject,phone,message) VALUES (?,?,?,?,?)',(name,email,request.form.get('subject','Website enquiry'),request.form.get('phone',''),message))
        get_db().commit(); flash('Your enquiry is saved. The team can review it in the admin workspace.','success')
        return redirect('/contact/')

    @app.get('/legacy/<path:slug>/')
    def original_page(slug):
        if '..' in slug: abort(404)
        from app import render_page
        return render_page(slug)

    def contribute():
        if request.method=='POST':
            values=[request.form.get(k,'').strip() for k in ['student_name','email','title','category','body']]
            if not values[0] or '@' not in values[1] or not values[2] or not values[4]: abort(400,'Complete the required fields.')
            get_db().execute('INSERT INTO reader_contributions(student_name,email,title,category,body) VALUES (?,?,?,?,?)',values)
            get_db().commit(); flash('Your contribution has been saved for editorial review.','success')
            return redirect('/submit-contribution/')
        return render_site('contribute','publications')
    app.view_functions['submit_contribution']=contribute

    @app.get('/publication/<int:publication_id>/')
    def publication_detail(publication_id):
        record=get_db().execute('SELECT * FROM publications WHERE id=? AND is_active=1',(publication_id,)).fetchone()
        if not record: abort(404)
        return render_site('publication_detail','publications',publication=dict(record))

    def guard(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not current_admin():
                return redirect('/admin/login/')
            if request.method == 'POST' and not secrets.compare_digest(request.form.get('csrf_token',''), token()):
                abort(400, 'Your session token expired. Reload the form and try again.')
            return fn(*args, **kwargs)
        return wrapped

    def audit(action):
        get_db().execute('INSERT INTO admin_audit(admin_id, action) VALUES (?,?)', (session['admin_id'], action))

    def workspace(template, **context):
        resp = make_response(render_template('workspace/'+template+'.html', models=MODELS, admin=current_admin(), **context))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp

    @guard
    def dashboard():
        counts = {}
        for key, model in MODELS.items():
            try:
                counts[key] = get_db().execute('SELECT COUNT(*) FROM ' + model[1]).fetchone()[0]
            except Exception:
                counts[key] = 0
        try:
            recent = get_db().execute('SELECT * FROM admin_audit ORDER BY id DESC LIMIT 10').fetchall()
        except Exception:
            recent = []
        return workspace('dashboard', title='Overview', active='', counts=counts, recent=recent)
    app.view_functions['admin_dashboard'] = dashboard

    @app.cli.command('create-admin')
    def create_admin():
        import click
        email=click.prompt('Admin email').strip().lower()
        password=click.prompt('Password (12+ characters)',hide_input=True,confirmation_prompt=True)
        if '@' not in email or len(password)<12: raise click.ClickException('Valid email and 12+ character password required.')
        get_db().execute('INSERT INTO admin_users(email,name,password_hash) VALUES (?,?,?) ON CONFLICT(email) DO UPDATE SET password_hash=excluded.password_hash',(email,'Book Buddy Admin',generate_password_hash(password)))
        get_db().commit(); click.echo('Admin account ready.')

    @app.route('/admin/media/',methods=['GET','POST'])
    @guard
    def workspace_media():
        folder=base_dir/'static'/'uploads'
        try:
            folder.mkdir(exist_ok=True)
        except OSError:
            pass
        if request.method=='POST':
            upload=request.files.get('file')
            if not upload or not upload.filename: abort(400,'Choose a file.')
            suffix=upload.filename.rsplit('.',1)[-1].lower()
            if suffix not in {'png','jpg','jpeg','webp','gif','avif','pdf','mp3'}: abort(400,'Use PNG, JPG, WebP, GIF, AVIF, PDF or MP3.')
            prefix=upload.stream.read(16); upload.stream.seek(0)
            valid = ((suffix=='png' and prefix.startswith(b'\x89PNG\r\n\x1a\n')) or
                (suffix in {'jpg','jpeg'} and prefix.startswith(b'\xff\xd8\xff')) or
                (suffix=='gif' and prefix[:6] in {b'GIF87a',b'GIF89a'}) or
                (suffix=='avif' and prefix[4:8]==b'ftyp' and prefix[8:12] in {b'avif',b'avis'}) or
                (suffix=='webp' and prefix[:4]==b'RIFF' and prefix[8:12]==b'WEBP') or
                (suffix=='pdf' and prefix.startswith(b'%PDF-')) or
                (suffix=='mp3' and (prefix.startswith(b'ID3') or prefix[:2] in {b'\xff\xfb',b'\xff\xf3',b'\xff\xf2'})))
            if not valid: abort(400,'The file content does not match its extension.')
            filename=secrets.token_hex(16)+'.'+suffix; upload.save(folder/filename)
            file_route = f'/static/uploads/{filename}'

            # Create or update corresponding record in publications or gallery_items
            target_kind = request.form.get('kind', '').strip().lower()
            raw_title = request.form.get('title', '').strip()
            title = raw_title or upload.filename.rsplit('.', 1)[0].replace('-', ' ').replace('_', ' ').title()
            is_paid = 1 if request.form.get('is_paid') in {'1', 'true', 'True'} else 0

            if not target_kind:
                if suffix == 'pdf':
                    target_kind = 'magazine'
                elif suffix == 'mp3':
                    target_kind = 'podcast'
                elif suffix in {'png', 'jpg', 'jpeg', 'webp', 'gif', 'avif'}:
                    target_kind = 'gallery'
                else:
                    target_kind = 'magazine'

            if target_kind == 'gallery':
                get_db().execute(
                    """INSERT INTO gallery_items (title, description, image_path, alt_text, page_slug, position, is_active)
                    VALUES (?, '', ?, ?, 'all', 0, 1)""",
                    (title, file_route, title)
                )
            else:
                if target_kind not in {'news', 'magazine', 'podcast'}:
                    target_kind = 'magazine'
                if suffix in {'png', 'jpg', 'jpeg', 'webp', 'gif', 'avif'}:
                    cover_path = file_route
                    file_path = file_route
                elif suffix == 'pdf':
                    cover_path = request.form.get('cover_path', '').strip() or '/static/img/storybook/magazine.svg'
                    file_path = file_route
                elif suffix == 'mp3':
                    cover_path = request.form.get('cover_path', '').strip() or '/static/img/storybook/podcast.svg'
                    file_path = file_route
                else:
                    cover_path = file_route
                    file_path = file_route

                get_db().execute(
                    """INSERT INTO publications (title, kind, description, edition, file_path, cover_path, published_on, is_active, is_paid)
                    VALUES (?, ?, '', 'Latest Edition', ?, ?, ?, 1, ?)""",
                    (title, target_kind, file_path, cover_path, date.today().isoformat(), is_paid)
                )

            audit('Uploaded media '+filename+' ('+target_kind+')')
            get_db().commit()
            flash('Uploaded and added to '+target_kind+' catalogue.','success')
            return redirect('/admin/media/')
        files=sorted(p.name for p in folder.iterdir() if p.is_file())
        return workspace('media',title='Media library',active='media',files=files)

    @app.route('/admin/manage/<kind>/', methods=['GET','POST'])
    @guard
    def manage_records(kind):
        if kind not in MODELS: abort(404)
        if kind == 'gallery':
            import gallery_service
            if request.method == 'POST':
                action = request.form.get('admin_action', '') or request.form.get('gallery_action', '')
                if action == 'save_settings':
                    pill = request.form.get('gallery_pill', '')
                    heading = request.form.get('gallery_heading', '')
                    gallery_service.save_gallery_settings(get_db, pill, heading)
                    flash('Gallery page settings saved.', 'success')
                elif action == 'upload':
                    files = request.files.getlist('photos')
                    errs = gallery_service.add_gallery_photos(get_db, files)
                    if errs:
                        for err in errs: flash(err, 'danger')
                    else:
                        flash(f'Uploaded {len(files)} photo(s) successfully.', 'success')
                elif action == 'reorder':
                    db = get_db()
                    for key in request.form:
                        if key.startswith('pos_'):
                            try:
                                gid = int(key.split('_')[1])
                                pos = int(request.form[key])
                                db.execute("UPDATE gallery_items SET position = ? WHERE id = ?", (pos, gid))
                            except (ValueError, IndexError): pass
                    db.commit()
                    flash('Gallery photo order updated.', 'success')
                elif action == 'toggle':
                    gid = int(request.form.get('item_id', 0))
                    if gallery_service.toggle_gallery_active(get_db, gid):
                        flash('Photo visibility toggled.', 'success')
                elif action == 'delete':
                    gid = int(request.form.get('item_id', 0))
                    if gallery_service.delete_gallery_item(get_db, gid):
                        flash(f'Gallery photo #{gid} deleted.', 'info')
                elif action == 'update_alt':
                    gid = int(request.form.get('item_id', 0))
                    alt = request.form.get('alt_text', '')
                    gallery_service.update_gallery_item_alt(get_db, gid, alt)
                    flash('Alt text updated.', 'success')
                return redirect('/admin/about-editor/#gallery')

            return redirect('/admin/about-editor/#gallery')

        label,table,fields_text = MODELS[kind]
        fields=fields_text.split()
        query=request.args.get('q','').strip()[:100]
        column_names={r['name'] for r in get_db().execute('PRAGMA table_info("'+table+'")')}
        # Only allow filters for real columns from our own known schema.
        filter_fields=[name for name in ('status','is_active','archived','kind','category','collection','age_group') if name in column_names]
        options={}
        selected={}
        for column in filter_fields:
            values=[str(r[0]) for r in get_db().execute('SELECT DISTINCT "'+column+'" FROM "'+table+'" WHERE "'+column+'" IS NOT NULL ORDER BY 1 LIMIT 35')]
            options[column]=values
            chosen=request.args.get('f_'+column,'')
            if chosen and chosen in values: selected[column]=chosen
        clauses=[];params=[]
        if query:
            clauses.append('('+ ' OR '.join('CAST("'+f+'" AS TEXT) LIKE ?' for f in fields)+')')
            params.extend(['%'+query+'%']*len(fields))
        for field,value in selected.items():
            clauses.append('CAST("'+field+'" AS TEXT)=?');params.append(value)
        where=(' WHERE '+' AND '.join(clauses)) if clauses else ''
        try: per_page=int(request.args.get('per_page',25))
        except (TypeError,ValueError): per_page=25
        if per_page not in (25,50,100):per_page=25
        try: page=max(1,int(request.args.get('page',1)))
        except (ValueError,TypeError): page=1
        default_sort = 'oldest' if kind in ('home-sections', 'homepage_sections', 'home_sections') else 'recent'
        sort = request.args.get('sort', default_sort) or default_sort
        textfield = next((f for f in ('title','name','slug','email','student_name') if f in column_names), None)
        if sort == 'oldest':
            order = 'id ASC'
        elif sort == 'az' and textfield:
            order = '"' + textfield + '" COLLATE NOCASE ASC,id DESC'
        elif sort == 'recent':
            order = 'id DESC'
        else:
            sort = default_sort
            order = 'id ASC' if default_sort == 'oldest' else 'id DESC'
        count=get_db().execute('SELECT COUNT(*) FROM '+table+where,params).fetchone()[0]
        page=min(page,max(1,math.ceil(count/per_page)))
        records=get_db().execute('SELECT id,'+','.join(fields)+' FROM '+table+where+' ORDER BY '+order+' LIMIT ? OFFSET ?',params+[per_page,(page-1)*per_page]).fetchall()
        filter_query={'q':query,'sort':sort,'per_page':per_page}
        filter_query.update({'f_'+field:value for field,value in selected.items()})
        return workspace('list',title=label,active=kind,fields=fields,records=records,q=query,
                         page=page,pages=max(1,math.ceil(count/per_page)),count=count,
                         can_create=kind not in READ_ONLY,filter_options=options,selected_filters=selected,
                         sort=sort,per_page=per_page,filter_query=filter_query,sort_by_name=bool(textfield))

    @app.route('/admin/manage/<kind>/<int:record_id>/', methods=['GET','POST'])
    @guard
    def edit_record(kind, record_id):
        if kind not in MODELS: abort(404)
        label,table,field_text = MODELS[kind]
        fields = field_text.split()
        if not record_id and kind in READ_ONLY: abort(403)
        record = dict(get_db().execute('SELECT * FROM '+table+' WHERE id=?',(record_id,)).fetchone() or {}) if record_id else {}
        if not record_id and kind == 'books':
            record.setdefault('audience', 'all')
            record.setdefault('is_active', 1)
            record.setdefault('stock', 1)
            record.setdefault('archived', 0)
        if not record_id and kind == 'publications':
            record.setdefault('kind', 'magazine')
            record.setdefault('is_active', 1)
            record.setdefault('is_paid', 0)
            record.setdefault('published_on', date.today().isoformat())
            record.setdefault('edition', 'Latest Edition')
        if not record_id and kind == 'gallery':
            record.setdefault('is_active', 1)
            record.setdefault('page_slug', 'all')
            record.setdefault('position', 0)
        if record_id and not record: abort(404)
        if kind == 'pages' and record.get('slug') == 'about' and request.method == 'GET':
            return redirect('/admin/about-editor/')
        errors=[]
        if request.method=='POST':
            values={}
            for field in fields:
                raw_val = request.form.get(field, None)
                value = raw_val.strip() if raw_val is not None else ''
                if field in BOOLS:
                    if raw_val is None or raw_val == '':
                        value = 0 if field == 'archived' else 1
                    else:
                        value = int(value == '1')
                elif field in NUMBERS:
                    if (raw_val is None or raw_val == '') and field == 'stock' and kind == 'books':
                        value = 1
                    else:
                        try:
                            value=float(value or 0)
                            if not math.isfinite(value) or value<0: raise ValueError()
                            if field in {'stock','capacity','seats','event_id','position','duration_days','duration_months','books_at_time','total_books','user_id','plan_id','max_uses'}:
                                if value != int(value): raise ValueError()
                                value=int(value)
                        except ValueError: errors.append(field+' must be a nonnegative number.'); value=0
                elif field in {'route','file_path','image_path','cover_path','url','join_url','embed_url'} and value:
                    if not value.startswith(('http://', 'https://', '/')) and any(value.startswith(p) for p in ('static/', 'media/')):
                        value = '/' + value
                    from library_core import valid_url
                    if not valid_url(value): errors.append(field+' must be a local path or HTTP/HTTPS image/file URL.')
                elif field in {'event_date','published_on','starts_on','expires_on'} and value:
                    try: date.fromisoformat(value)
                    except ValueError: errors.append('Enter a valid date.')
                values[field]=value
            # An uploaded media file always travels through authenticated admin CRUD.
            # The existing path remains unchanged when no new file is selected.
            for media_field in ('image_path','cover_path','file_path'):
                if media_field not in fields or not request.files.get('asset_'+media_field) or not request.files['asset_'+media_field].filename:
                    continue
                try:
                    kind_of_file = 'pdf' if media_field=='file_path' else 'image'
                    values[media_field] = app.extensions['bookbuddy_store_media_v13'](
                        'asset_'+media_field, kind, kind_of_file)
                except ValueError as exc:
                    errors.append(str(exc))
            if kind == 'books':
                if not values.get('audience') or values.get('audience') not in {'all', 'kids', 'adult'}:
                    values['audience'] = 'all'
                if values.get('stock') is None or values.get('stock') == '' or (not record_id and values.get('stock') == 0 and request.form.get('stock') is None):
                    values['stock'] = 1
                if 'is_active' in fields and (values.get('is_active') is None or values.get('is_active') == ''):
                    values['is_active'] = 1
                if 'archived' in fields and (values.get('archived') is None or values.get('archived') == ''):
                    values['archived'] = 0
            if kind == 'publications':
                if not values.get('kind') or values.get('kind') not in {'news', 'magazine', 'podcast'}:
                    values['kind'] = 'magazine'
                if 'is_active' in fields and (values.get('is_active') is None or values.get('is_active') == ''):
                    values['is_active'] = 1
                if 'is_paid' in fields and (values.get('is_paid') is None or values.get('is_paid') == ''):
                    values['is_paid'] = 0
                if 'published_on' in fields and not values.get('published_on'):
                    values['published_on'] = date.today().isoformat()
                if 'cover_path' in fields and not values.get('cover_path') and values.get('file_path'):
                    fp = values.get('file_path')
                    if any(fp.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif')):
                        values['cover_path'] = fp
            if kind == 'gallery':
                if 'is_active' in fields and (values.get('is_active') is None or values.get('is_active') == ''):
                    values['is_active'] = 1
                if 'page_slug' in fields and not values.get('page_slug'):
                    values['page_slug'] = 'all'
            if 'title' in values and not values['title']: errors.append('Title is required.')
            if 'slug' in values and (not values['slug'] or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in values['slug'])): errors.append('Slug must contain lowercase letters, numbers and hyphens.')
            if kind=='access':
                if values.get('scope') not in {'events','media'}: errors.append('Choose a valid content section.')
                if values.get('access_mode') not in {'public','login','plan'}: errors.append('Choose Public, Login or Plan access.')
            if kind=='plans':
                scopes={x.strip() for x in values['scopes'].split(',') if x.strip()}
                if not scopes or not scopes <= {'events','media'}: errors.append('Choose at least one valid included section.')
                if values.get('duration_months',0)>120: errors.append('Use at most 120 months.')
                if values['duration_days']<1 and values.get('duration_months',0)<1: errors.append('Duration must be at least one day.')
                values['scopes']=','.join(sorted(scopes))
            if kind=='memberships':
                plan=get_db().execute('SELECT * FROM plans WHERE id=?',(values['plan_id'],)).fetchone()
                if not plan or not get_db().execute('SELECT 1 FROM users WHERE id=?',(values['user_id'],)).fetchone(): errors.append('Select an existing member and plan.')
                if values['status'] not in {'Pending','Active','Cancelled','Expired'}: errors.append('Invalid membership status.')
                if values['status']=='Active' and plan:
                    values['starts_on']=values['starts_on'] or date.today().isoformat()
                    try:
                        start=date.fromisoformat(values['starts_on'])
                        from library_core import add_months
                        end=add_months(start,plan['duration_months']) if plan['duration_months'] else start+timedelta(days=plan['duration_days'])
                        values['expires_on']=values['expires_on'] or (end-timedelta(days=1)).isoformat()
                        if date.fromisoformat(values['expires_on'])<start: errors.append('Expiry must be on or after the start date.')
                    except (ValueError,OverflowError): errors.append('Enter valid membership dates and duration.')
            if kind=='events' and values['category'] not in {'upcoming','reading-circle','contest'}: errors.append('Select a valid event category.')
            if kind=='publications':
                if values.get('kind') not in {'news','magazine','podcast'}: errors.append('Select a media type.')
                if values.get('embed_url'):
                    eu = values['embed_url'].strip()
                    if 'open.spotify.com' in eu and '/embed/' not in eu:
                        eu = eu.replace('open.spotify.com/episode/', 'open.spotify.com/embed/episode/')
                        eu = eu.replace('open.spotify.com/show/', 'open.spotify.com/embed/show/')
                        values['embed_url'] = eu
            pass
            from resources import validate_admin_record
            errors.extend(validate_admin_record(kind,values,get_db))
            if not errors:
                try:
                    if record_id:
                        get_db().execute('UPDATE '+table+' SET '+','.join(f+'=?' for f in fields)+' WHERE id=?',list(values.values())+[record_id])
                        if kind == 'gallery' and values.get('image_path'):
                            from gallery_service import get_or_create_thumbnail
                            thumb = get_or_create_thumbnail(values['image_path'])
                            get_db().execute('UPDATE gallery_items SET thumbnail_path=? WHERE id=?', (thumb, record_id))
                    else:
                        insert_cols = list(fields)
                        insert_vals = [values[f] for f in fields]
                        if kind == 'gallery':
                            if 'title' not in insert_cols:
                                insert_cols.append('title')
                                insert_vals.append(values.get('alt_text') or f"Book Buddy gallery photo {values.get('position', 0)}")
                            if 'thumbnail_path' not in insert_cols and values.get('image_path'):
                                from gallery_service import get_or_create_thumbnail
                                insert_cols.append('thumbnail_path')
                                insert_vals.append(get_or_create_thumbnail(values['image_path']))
                        get_db().execute('INSERT INTO '+table+' ('+','.join(insert_cols)+') VALUES ('+','.join('?' for _ in insert_cols)+')',insert_vals)
                    if kind == 'pages' and values.get('slug') in {'about', 'contact'}:
                        # Dedicated page routes use site_content rather than
                        # cms_pages.body; never report a successful edit that
                        # cannot appear on the public page.
                        from about_editor import mirror_about_cms_save, mirror_contact_cms_save
                        if values['slug'] == 'about':
                            mirror_about_cms_save(get_db(), values)
                        else:
                            mirror_contact_cms_save(get_db(), values)
                    audit(('Updated' if record_id else 'Created')+' '+label+' #'+str(record_id or 'new'))
                    get_db().commit()
                    flash('Saved successfully.','success')
                    return redirect('/admin/manage/'+kind+'/')
                except Exception:
                    get_db().rollback(); errors.append('Could not save. Check duplicate slugs, email addresses and linked record IDs.')
            record.update(values)
        related=[]
        if kind=='orders' and record_id:
            related=[dict(r) for r in get_db().execute('SELECT title,quantity,price FROM order_items WHERE order_id=?',(record_id,))]
        options={}
        if kind=='memberships':
            options['user_id']=[(r['id'],r['name']+' — '+r['email']) for r in get_db().execute('SELECT id,name,email FROM users ORDER BY name')]
            options['plan_id']=[(r['id'],r['title']) for r in get_db().execute('SELECT id,title FROM plans ORDER BY title')]
            options['status']=[(v,v) for v in ['Pending','Active','Cancelled','Expired']]
        if kind=='access':
            options['scope']=[(record.get('scope',''),record.get('scope','').title())]
            options['access_mode']=[('public','Public — everyone'),('login','Login — registered members'),('plan','Plan — active membership required')]
        if kind=='coupons': options['discount_type']=[('percent','Percentage'),('fixed','Fixed rupees')]
        if kind=='events': options['category']=[('upcoming','General event'),('reading-circle','Reading Circle'),('contest','Contest')]
        if kind=='publications': options['kind']=[('news','Newspaper'),('magazine','Magazine'),('podcast','Podcast')]
        if kind=='navigation':
            options['group_name']=[('header','Header Navigation'),('footer_useful','Footer Useful Links'),('footer_bottom','Footer Bottom Links')]
        if kind=='partners':
            options['status']=[(v,v) for v in ['New','In Review','Contacted','Approved','Closed']]
            options['proposal_type']=[('Reading Circle Partner','Reading Circle Partner'),('School Library Outreach','School Library Outreach'),('Book Box Donation & Sponsorship','Book Box Donation & Sponsorship'),('Author & Storyteller Collaboration','Author & Storyteller Collaboration'),('Venue & Community Partner','Venue & Community Partner'),('Other','Other Collaboration')]
        if kind in ('home-sections','homepage_sections'):
            options['section_key']=[('hero','Hero Section'),('community','Community & Events'),('publications','Publications'),('reviews','Reviews & Ratings'),('footer','Footer Details')]
        pass
        return workspace('edit', options=options, title=('Edit ' if record_id else 'New ')+label, active=kind, fields=fields, record=record, record_id=record_id, errors=errors, long_fields=LONG, numbers=NUMBERS, bools=BOOLS, related=related)

    @app.post('/admin/manage/<kind>/<int:record_id>/delete/')
    @guard
    def delete_record(kind, record_id):
        if kind not in MODELS: abort(404)
        if request.form.get('confirm')!='DELETE': abort(400)
        table=MODELS[kind][1]
        # Preserve financial and participant records; they can be cancelled using status.
        if kind in READ_ONLY: abort(403)
        try:
            get_db().execute('DELETE FROM '+table+' WHERE id=?',(record_id,))
            audit('Deleted '+kind+' #'+str(record_id)); get_db().commit()
            flash('Record deleted.','success')
        except Exception:
            get_db().rollback(); flash('This record is in use. Unpublish it instead.','danger')
        return redirect('/admin/manage/'+kind+'/')

    @app.get('/admin/manage/<kind>/export/')
    @guard
    def export_records(kind):
        if kind not in MODELS: abort(404)
        _,table,field_text=MODELS[kind]; fields=['id']+field_text.split()
        stream=io.StringIO(); writer=csv.writer(stream); writer.writerow(fields)
        for row in get_db().execute('SELECT '+','.join(fields)+' FROM '+table):
            writer.writerow([("'"+str(v)) if str(v).startswith(('=','+','-','@')) else v for v in row])
        return Response(stream.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename='+kind+'.csv'})

    @app.get('/admin/import/<kind>/template.csv')
    @guard
    def import_template(kind):
        if kind not in MODELS or kind in READ_ONLY: abort(404)
        _, table, field_text = MODELS[kind]
        fields = ['id'] + field_text.split()
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(fields)
        return Response(stream.getvalue(), mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={kind}_template.csv'})

    @app.route('/admin/import/<kind>/', methods=['GET', 'POST'])
    @guard
    def import_records(kind):
        if kind not in MODELS: abort(404)
        if kind in READ_ONLY: abort(403)
        label, table, field_text = MODELS[kind]
        fields = field_text.split()
        errors = []
        preview = []
        token_val = ''

        cursor = get_db().execute(f'PRAGMA table_info({table})')
        table_cols = {col[1] for col in cursor.fetchall()}

        if request.method == 'POST':
            action = request.form.get('action', '')
            if action == 'apply':
                staged = session.get('import_preview', [])
                staged_token = request.form.get('token', '')
                saved_token = session.get('import_token')
                saved_kind = session.get('import_kind')

                if not staged or not staged_token or staged_token != saved_token or saved_kind != kind:
                    errors.append('Import session expired or is invalid. Please upload the CSV again.')
                else:
                    try:
                        db = get_db()
                        for item in staged:
                            rec_id = item.get('id')
                            vals = item.get('values', {})
                            valid_vals = {k: v for k, v in vals.items() if k in table_cols}
                            if not valid_vals:
                                continue
                            if rec_id:
                                exists = db.execute(f'SELECT 1 FROM {table} WHERE id=?', (rec_id,)).fetchone()
                                if exists:
                                    set_clause = ', '.join(f'{k}=?' for k in valid_vals.keys())
                                    db.execute(f'UPDATE {table} SET {set_clause} WHERE id=?', list(valid_vals.values()) + [rec_id])
                                else:
                                    cols = ['id'] + list(valid_vals.keys())
                                    db.execute(f'INSERT INTO {table} ({", ".join(cols)}) VALUES ({", ".join("?" for _ in cols)})', [rec_id] + list(valid_vals.values()))
                            else:
                                cols = list(valid_vals.keys())
                                db.execute(f'INSERT INTO {table} ({", ".join(cols)}) VALUES ({", ".join("?" for _ in cols)})', list(valid_vals.values()))
                        db.commit()
                        audit(f'Imported {len(staged)} {kind} via CSV')
                        session.pop('import_preview', None)
                        session.pop('import_token', None)
                        session.pop('import_kind', None)
                        flash(f'Successfully imported {len(staged)} records.', 'success')
                        return redirect(f'/admin/manage/{kind}/')
                    except Exception as e:
                        get_db().rollback()
                        errors.append(f'Could not apply import: {str(e)}')
            else:
                upload = request.files.get('file')
                if not upload or not upload.filename:
                    errors.append('Please choose a CSV file.')
                else:
                    try:
                        content = upload.stream.read()
                        if len(content) > 2 * 1024 * 1024:
                            errors.append('The CSV file exceeds the 2 MB limit.')
                        else:
                            text = content.decode('utf-8-sig', errors='replace')
                            stream = io.StringIO(text)
                            reader = csv.DictReader(stream)
                            if not reader.fieldnames:
                                errors.append('CSV file is empty or missing headers.')
                            else:
                                count = 0
                                for idx, row in enumerate(reader, start=2):
                                    count += 1
                                    if count > 2000:
                                        errors.append('File exceeds maximum limit of 2,000 rows.')
                                        break
                                    clean_row = {k.strip(): (v.strip() if v is not None else '') for k, v in row.items() if k}
                                    row_id = clean_row.get('id')
                                    clean_id = None
                                    if row_id:
                                        try:
                                            clean_id = int(row_id)
                                        except ValueError:
                                            errors.append(f'Row {idx}: ID "{row_id}" must be an integer.')
                                            continue
                                    row_vals = {}
                                    for f in fields:
                                        if f in clean_row:
                                            v = clean_row[f]
                                            if f in BOOLS:
                                                v = 1 if v.lower() in {'1', 'true', 'yes', 'y'} else 0
                                            elif f in NUMBERS and v != '':
                                                try:
                                                    num_val = float(v)
                                                    if num_val.is_integer():
                                                        num_val = int(num_val)
                                                    v = num_val
                                                except ValueError:
                                                    errors.append(f'Row {idx}: {f} must be a number.')
                                            row_vals[f] = v
                                    if 'title' in fields and not row_vals.get('title') and not clean_id:
                                        errors.append(f'Row {idx}: Title is required.')
                                    preview.append({'id': clean_id, 'values': row_vals})

                                if not errors and preview:
                                    token_val = secrets.token_urlsafe(16)
                                    session['import_token'] = token_val
                                    session['import_kind'] = kind
                                    session['import_preview'] = preview
                                elif not errors and not preview:
                                    errors.append('No data rows found in CSV.')
                    except Exception as e:
                        errors.append(f'Error reading CSV file: {str(e)}')

        return workspace('import', title='Import ' + label, active=kind, kind=kind, fields=fields, errors=errors, preview=preview, token=token_val)

    @app.route('/admin/settings/',methods=['GET','POST'])
    @guard
    def workspace_settings():
        if request.method=='POST':
            previous={r['content_key']:r['content_value'] for r in get_db().execute('SELECT content_key,content_value FROM site_content')}
            for row in get_db().execute('SELECT content_key FROM site_content').fetchall():
                key=row[0]
                if key in request.form: get_db().execute('UPDATE site_content SET content_value=? WHERE content_key=?',(request.form[key],key))
            # The legacy About text field was saved by older installations,
            # but the structured About page reads about_philosophy_body.
            # Avoid overriding that canonical field if the admin also edited it.
            if ('about_text' in request.form and request.form.get('about_text') != previous.get('about_text')
                    and request.form.get('about_philosophy_body',previous.get('about_philosophy_body')) == previous.get('about_philosophy_body')):
                get_db().execute("INSERT INTO site_content(content_key,content_value) VALUES('about_philosophy_body',?) ON CONFLICT(content_key) DO UPDATE SET content_value=excluded.content_value",(request.form['about_text'],))
            audit('Updated site settings'); get_db().commit(); flash('Settings saved.','success')
            return redirect('/admin/settings/')
        settings=get_db().execute('SELECT * FROM site_content ORDER BY content_key').fetchall()
        groups={}
        for item in settings:
            key=item['content_key']
            group=('SEO & sharing' if key.startswith('seo_') else 'Contact information' if key.startswith('contact_') else 'About & founder' if key.startswith(('about_','founder_','team_')) else 'Homepage' if key.startswith(('home_','hero_','newsletter_')) else 'Footer & navigation' if key.startswith(('base_','footer_')) else key.split('_')[0].replace('-',' ').title())
            groups.setdefault(group,[]).append(item)
        return workspace('settings', title='Website settings',active='settings',settings_groups=groups)

    @app.route('/admin/password/',methods=['GET','POST'])
    @guard
    def workspace_password():
        if request.method=='POST':
            row=get_db().execute('SELECT * FROM admin_users WHERE id=?',(session['admin_id'],)).fetchone()
            password=request.form.get('password','')
            if len(password)<12 or not check_password_hash(row['password_hash'],request.form.get('current','')):
                flash('Check your current password. The new password needs at least 12 characters.','danger')
            else:
                get_db().execute('UPDATE admin_users SET password_hash=? WHERE id=?',(generate_password_hash(password),row['id']))
                audit('Changed password'); get_db().commit(); flash('Password updated.','success')
        return workspace('password',title='Change password',active='password')

    ALLOWED_THEMES = {'maroon', 'navy', 'dark', 'custom'}
    ALLOWED_FONTS = {'inter', 'playfair', 'poppins'}
    HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')

    DEFAULT_P = '#7a1230'
    DEFAULT_BG = '#f7f8fc'
    DEFAULT_CARD = '#ffffff'
    DEFAULT_TX = '#1a1a2e'

    @app.route('/admin/appearance/', methods=['GET', 'POST'])
    @guard
    def workspace_appearance():
        if request.method == 'POST':
            action = request.form.get('action', 'save')
            if action == 'reset':
                theme = 'maroon'
                font = 'inter'
                custom_p = DEFAULT_P
                custom_bg = DEFAULT_BG
                custom_card = DEFAULT_CARD
                custom_tx = DEFAULT_TX
            else:
                theme = request.form.get('theme', 'maroon').strip().lower()
                font = request.form.get('font', 'inter').strip().lower()
                custom_p = request.form.get('custom_p', DEFAULT_P).strip()
                custom_bg = request.form.get('custom_bg', DEFAULT_BG).strip()
                custom_card = request.form.get('custom_card', DEFAULT_CARD).strip()
                custom_tx = request.form.get('custom_tx', DEFAULT_TX).strip()

                if theme not in ALLOWED_THEMES:
                    theme = 'maroon'
                if font not in ALLOWED_FONTS:
                    font = 'inter'

                for color_name, val in [('Primary', custom_p), ('Background', custom_bg), ('Card', custom_card), ('Text', custom_tx)]:
                    if not HEX_COLOR_RE.match(val):
                        flash(f'Invalid hex color format for {color_name} ({val}). Expected format: #RRGGBB', 'danger')
                        return redirect('/admin/appearance/')

            get_db().execute(
                "INSERT INTO site_settings (id, theme, font, custom_p, custom_bg, custom_card, custom_tx) "
                "VALUES (1, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "theme=excluded.theme, font=excluded.font, "
                "custom_p=excluded.custom_p, custom_bg=excluded.custom_bg, "
                "custom_card=excluded.custom_card, custom_tx=excluded.custom_tx",
                (theme, font, custom_p, custom_bg, custom_card, custom_tx)
            )
            audit(f'Updated appearance settings to theme={theme}, font={font}')
            get_db().commit()
            flash('Saved ✓', 'success')
            return redirect('/admin/appearance/')

        theme = 'maroon'
        font = 'inter'
        custom_p = DEFAULT_P
        custom_bg = DEFAULT_BG
        custom_card = DEFAULT_CARD
        custom_tx = DEFAULT_TX
        try:
            row = get_db().execute('SELECT theme, font, custom_p, custom_bg, custom_card, custom_tx FROM site_settings WHERE id=1').fetchone()
            if row:
                theme = row['theme'] or 'maroon'
                font = row['font'] or 'inter'
                custom_p = row['custom_p'] or DEFAULT_P
                custom_bg = row['custom_bg'] or DEFAULT_BG
                custom_card = row['custom_card'] or DEFAULT_CARD
                custom_tx = row['custom_tx'] or DEFAULT_TX
        except Exception:
            pass

        return workspace(
            'appearance',
            title='Appearance',
            active='appearance',
            current_theme=theme,
            current_font=font,
            custom_p=custom_p,
            custom_bg=custom_bg,
            custom_card=custom_card,
            custom_tx=custom_tx
        )

    @app.route('/admin/appearance', methods=['GET', 'POST'])
    @guard
    def workspace_appearance_slash():
        if request.method == 'POST':
            return workspace_appearance()
        return redirect('/admin/appearance/')

    @app.before_request
    def published_pages():
        path=request.path.strip('/')
        if request.method=='GET':
            aliases={'calendar':'/events/','newspaper':'/publications/?kind=news','news-paper':'/publications/?kind=news','index':'/'}
            if path in aliases: return redirect(aliases[path])
            # About is a structured page with library story, team and videos. Its
            # admin-managed copy is resolved by about_content.about_context.
            # Other explicitly implemented routes must not be silently replaced by
            # a generic CMS body merely because an identically named slug exists.
            if path in {'about', 'contact', 'how-to-borrow', 'visit-us'} or (
                request.endpoint not in (None, 'dynamic_page')
            ):
                return None
            page=get_db().execute('SELECT * FROM cms_pages WHERE slug=? AND is_active=1',(path,)).fetchone()
            if page:
                from about_editor import plain_legacy_body
                public=dict(page)
                public['body']=plain_legacy_body(public['body'])
                return render_site('content','content',page=public)
        # Retired placeholder actions must never falsely confirm payments or memberships.
        if request.path in {'/workshop/verify-payment/','/workshop/apply/','/users/membership/activate-trial/','/users/membership/process/','/users/subscription/process/'}:
            return {'status':'not_configured','message':'This integration needs configuration before it can be used.'},501
