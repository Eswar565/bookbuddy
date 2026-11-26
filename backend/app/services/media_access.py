"""Public previews and per-publication entitlement checks, including raw files."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit, unquote, quote
import re
from flask import request, session, abort, send_file
from management import MODELS, BOOLS, NUMBERS


def install_media_access(app, db, render, root):
    with app.app_context():
        cols={r[1] for r in db().execute('PRAGMA table_info(publications)')}
        if 'is_paid' not in cols:
            # Preserve previously restricted media as paid during migration.
            rule=db().execute("SELECT access_mode FROM access_rules WHERE scope='media'").fetchone()
            db().execute('ALTER TABLE publications ADD COLUMN is_paid INTEGER NOT NULL DEFAULT 0')
            if rule and rule[0] != 'public':db().execute('UPDATE publications SET is_paid=1')
        if 'download_count' not in cols:
            db().execute('ALTER TABLE publications ADD COLUMN download_count INTEGER NOT NULL DEFAULT 0')
        db().execute('UPDATE publications SET is_active = 1 WHERE is_active IS NULL OR is_active = 0')
        db().commit()
    name,table,fields=MODELS['publications']
    fields_list = fields.split()
    if 'is_paid' not in fields_list:
        fields_list.append('is_paid')
    if 'download_count' not in fields_list:
        fields_list.append('download_count')
    MODELS['publications'] = (name, table, ' '.join(fields_list))
    BOOLS.add('is_paid')
    NUMBERS.add('download_count')

    def staff():
        return bool(db().execute('SELECT 1 FROM admin_users WHERE id=? AND is_active=1',(session.get('admin_id'),)).fetchone())

    def entitled():
        if staff():return True
        u=db().execute('SELECT * FROM users WHERE id=? AND is_active=1',(session.get('user_id'),)).fetchone()
        if not u or session.get('auth_version',0)!=u['session_version']:return False
        today=datetime.now(timezone(timedelta(hours=5,minutes=30))).date().isoformat()
        return bool(db().execute("""SELECT 1 FROM lending_subscriptions WHERE user_id=?
            AND status IN ('Active','Scheduled') AND starts_on<=? AND expires_on>=?
            AND payment_status IN ('Paid - Razorpay','Paid - confirmed by staff') LIMIT 1""",(u['id'],today,today)).fetchone())

    def can_read(publication):return not publication['is_paid'] or entitled()

    import os
    is_vercel = os.environ.get("VERCEL") == "1" or os.environ.get("VERCEL_ENV") is not None
    default_media_root = Path("/tmp/media") if is_vercel else Path(root) / "media"
    media_root = Path(os.environ.get("MEDIA_ROOT", default_media_root)).resolve()
    try:
        media_root.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    def local_file(value):
        parsed=urlsplit(value or '')
        if parsed.scheme or parsed.netloc:return None
        path=unquote(parsed.path)
        if path in {'/media', '/media/'}: return None
        if not path.startswith(('/media/','/static/uploads/','/static/demo/')):return None
        if path.startswith('/media/'):
            resolved = (media_root / path[7:]).resolve()
            if not resolved.is_relative_to(media_root): return None
        else:
            rel = path.lstrip('/')
            candidates = []
            if hasattr(app, 'static_folder') and app.static_folder:
                candidates.append(Path(app.static_folder).parent)
            candidates.extend([Path(root), Path(root) / 'backend' / 'app', Path(root) / 'app'])
            resolved = None
            for base in candidates:
                cand = (base / rel).resolve()
                if cand.exists():
                    resolved = cand
                    break
            if not resolved:
                resolved = (Path(root) / rel).resolve()
            allowed = []
            for base in candidates:
                allowed.extend([(base / p).resolve() for p in ('static/uploads', 'static/demo')])
            if not any(resolved.is_relative_to(base) for base in allowed): return None
        if any(part in {'users','interns','resumes'} for part in Path(path).parts):return None
        return resolved

    def format_content_disposition(disposition: str, filename: str) -> str:
        ascii_name = re.sub(r'[^\x20-\x7e]', '', filename).replace('"', '').replace(';', '').strip()
        if not ascii_name:
            ascii_name = "publication.pdf"
        quoted_utf8 = quote(filename.encode('utf-8'))
        return f"{disposition}; filename=\"{ascii_name}\"; filename*=UTF-8''{quoted_utf8}"

    def make_friendly_pdf_name(p):
        if not p:
            return "Book-Buddy-Publication.pdf"
        p_dict = dict(p) if hasattr(p, 'keys') else {}
        title = (p_dict.get('title') or '').strip()
        edition = (p_dict.get('edition') or '').strip()
        issue = str(p_dict.get('issue_number') or '').strip()
        published = str(p_dict.get('published_on') or '').strip()
        parts = []
        if title:
            parts.append(title)
        if issue:
            norm_issue = issue if issue.lower().startswith('issue') else f"Issue-{issue}"
            if norm_issue.lower() not in title.lower():
                parts.append(norm_issue)
        if edition and edition.lower() not in title.lower() and edition.lower() != 'latest edition':
            parts.append(edition)
        if published:
            parts.append(published)
        base = '-'.join(parts) if parts else 'Book-Buddy-Publication'
        base = re.sub(r'[\s_]+', '-', base)
        base = re.sub(r'[^a-zA-Z0-9\-\.]', '', base)
        base = re.sub(r'-{2,}', '-', base).strip('-')
        if not base.lower().endswith('.pdf'):
            base += '.pdf'
        return base

    def serve_publication_file(publication, as_attachment: bool = False):
        if not can_read(publication):
            abort(403, 'This publication requires an active paid membership.')
        file_path = publication.get('file_path') or ''
        target = local_file(file_path)
        if not target or not target.is_file() or target.suffix.lower() != '.pdf':
            abort(404)
        friendly_name = make_friendly_pdf_name(publication)
        if as_attachment:
            try:
                db().execute('UPDATE publications SET download_count = download_count + 1 WHERE id = ?', (publication['id'],))
                db().commit()
            except Exception:
                pass
        disposition = 'attachment' if as_attachment else 'inline'
        response = send_file(
            target,
            mimetype='application/pdf',
            as_attachment=as_attachment,
            download_name=friendly_name,
            conditional=True
        )
        response.headers['Content-Disposition'] = format_content_disposition(disposition, friendly_name)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'private, max-age=3600' if publication.get('is_paid') else 'public, max-age=3600'
        return response

    @app.route('/publications/<int:pub_id>/view/')
    def publication_view(pub_id):
        row = db().execute('SELECT * FROM publications WHERE id=? AND (is_active=1 OR is_active IS NULL)', (pub_id,)).fetchone()
        if not row:
            abort(404)
        return serve_publication_file(dict(row), as_attachment=False)

    @app.route('/publications/<int:pub_id>/download/')
    def publication_download(pub_id):
        row = db().execute('SELECT * FROM publications WHERE id=? AND (is_active=1 OR is_active IS NULL)', (pub_id,)).fetchone()
        if not row:
            abort(404)
        return serve_publication_file(dict(row), as_attachment=True)

    @app.context_processor
    def media_context():
        return {
            'can_read_publication': can_read,
            'make_friendly_pdf_name': make_friendly_pdf_name,
        }

    @app.before_request
    def publication_access():
        if request.method not in {'GET','HEAD'}:return None
        match=re.fullmatch(r'/publication/(\d+)/',request.path)
        if match:
            row=db().execute('SELECT * FROM publications WHERE id=? AND (is_active=1 OR is_active IS NULL)',(int(match[1]),)).fetchone()
            if not row:abort(404)
            publication=dict(row)
            return render('publication_detail','publications',publication=publication,media_locked=not can_read(publication))
        target=local_file(request.path)
        if target is None:return None
        # Compare canonical paths, protecting aliases, querystrings and encoded filenames.
        matches=[dict(row) for row in db().execute('SELECT * FROM publications WHERE file_path != ?',( '',)) if local_file(row['file_path'])==target]
        is_image = target.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.avif'}
        if matches and not staff() and not is_image:
            if not any(p.get('is_active', 1) for p in matches):abort(404)
            if any(p.get('is_paid') for p in matches) and not entitled():abort(403,'This publication requires an active paid membership.')
        if not target.is_file():abort(404)

        # Support ?download=1 and ?view=1 query params with friendly filename
        is_download = request.args.get('download') in ('1', 'true', 'yes')
        is_view = request.args.get('view') in ('1', 'true', 'yes')
        if matches and target.suffix.lower() == '.pdf' and (is_download or is_view):
            return serve_publication_file(matches[0], as_attachment=is_download)

        response=send_file(target,conditional=True)
        response.headers['Cache-Control']='public, max-age=3600' if is_image else 'private, no-store'
        return response
    hooks=app.before_request_funcs[None]
    hooks.remove(publication_access);hooks.insert(0,publication_access)
