"""Public previews and per-publication entitlement checks, including raw files."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re
from flask import request, session, abort, send_file
from management import MODELS, BOOLS


def install_media_access(app, db, render, root):
    with app.app_context():
        cols={r[1] for r in db().execute('PRAGMA table_info(publications)')}
        if 'is_paid' not in cols:
            # Preserve previously restricted media as paid during migration.
            rule=db().execute("SELECT access_mode FROM access_rules WHERE scope='media'").fetchone()
            db().execute('ALTER TABLE publications ADD COLUMN is_paid INTEGER NOT NULL DEFAULT 0')
            if rule and rule[0] != 'public':db().execute('UPDATE publications SET is_paid=1')
        db().execute('UPDATE publications SET is_active = 1 WHERE is_active IS NULL OR is_active = 0')
        db().commit()
    name,table,fields=MODELS['publications']
    if 'is_paid' not in fields.split():MODELS['publications']=(name,table,fields+' is_paid')
    BOOLS.add('is_paid')

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
        if not path.startswith(('/media/','/static/uploads/','/static/demo/')):return None
        if path.startswith('/media/'):
            resolved = (media_root / path[7:]).resolve()
            if not resolved.is_relative_to(media_root): return None
        else:
            resolved = (Path(root)/path.lstrip('/')).resolve()
            allowed = [(Path(root)/p).resolve() for p in ('static/uploads','static/demo')]
            if not any(resolved.is_relative_to(base) for base in allowed): return None
        if any(part in {'users','interns','resumes'} for part in Path(path).parts):return None
        return resolved

    @app.context_processor
    def media_context():return {'can_read_publication':can_read}

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
        response=send_file(target,conditional=True)
        response.headers['Cache-Control']='public, max-age=3600' if is_image else 'private, no-store'
        return response
    hooks=app.before_request_funcs[None]
    hooks.remove(publication_access);hooks.insert(0,publication_access)
