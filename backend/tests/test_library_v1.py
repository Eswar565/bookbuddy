from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]

def get_file(rel_path: str) -> Path:
    candidates = [
        ROOT / rel_path,
        ROOT / "app" / rel_path,
        ROOT / "app" / "services" / rel_path,
        ROOT / "app" / "routes" / rel_path,
        ROOT / "app" / "templates" / rel_path,
    ]
    for c in candidates:
        if c.exists():
            return c
    return ROOT / rel_path

def test_standalone_library_package():
    for name in ('app.py','access.py','about_content.py','library_core.py','library_centers.py'):
        assert get_file(name).is_file()
    for obsolete in ('bookbuddy_reference.py','learning.py','skills26.py','seeds.py'):
        assert not (ROOT/obsolete).exists()
    assert not list(ROOT.glob('BOOKBUDDY_V*.md'))

def test_about_never_downloads_remote_references():
    for name in ('access.py','about_content.py','about_editor.py'):
        source=get_file(name).read_text(encoding='utf-8')
        assert 'from bookbuddy_reference' not in source
    form=get_file('workspace/about_editor.html').read_text(encoding='utf-8')
    for key in ('about_philosophy_intro','about_philosophy_body','about_ikigai_url'):
        assert f'name="{key}"' in form

def test_public_site_and_retired_routes():
    from app import app
    app.config['TESTING']=True
    with app.test_client() as client:
        for path in ('/','/about/','/library/','/events/','/reading-circles/','/contests/',
                     '/publications/?kind=news','/publications/?kind=magazine',
                     '/podcasts/','/contact/'):
            response=client.get(path, follow_redirects=True)
            assert response.status_code == 200, (path, response.status_code)
        assert client.get('/gallery/').status_code in (200, 301)
        assert client.get('/gallery/', follow_redirects=True).status_code == 200
        for path in ('/skills/','/english/','/maths/','/classes/','/admin/learning-center/','/admin/about-sync/'):
            assert client.get(path).status_code == 404, path
        assert client.get('/members/dashboard/').status_code in (200,302)
        assert client.get('/admin/login/').status_code==200


def test_no_class_schedule_startup_or_skills_dependencies():
    source=get_file('portal.py').read_text(encoding='utf-8')
    schema=get_file('schema.sql').read_text(encoding='utf-8')
    app_source=(get_file('site.py') if get_file('site.py').is_file() else get_file('app.py')).read_text(encoding='utf-8')
    assert 'class_schedules' not in source
    assert 'class_schedules' not in schema
    assert 'CREATE TABLE IF NOT EXISTS classes' not in app_source
    assert 'CREATE TABLE IF NOT EXISTS class_enrollments' not in app_source
    assert 'CREATE TABLE IF NOT EXISTS kids_activities' not in app_source

def test_first_run_database_has_library_tables_and_no_learning_tables(tmp_path):
    import os, subprocess, sys
    env=os.environ.copy()
    env['BOOK_BUDDY_DATABASE']=str(tmp_path/'fresh_library.sqlite3')
    # A fresh app import creates its own schema, independent of restored user databases.
    result=subprocess.run([sys.executable,'-c',"""import app
with app.app.app_context():
    db=app.get_db()
    tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    required={'books','users','admin_users','events','publications','lending_plans','lending_subscriptions','lending_loans','copies17','reservations17','notifications17','site_content'}
    assert required.issubset(tables),required-tables
    assert tables.isdisjoint({'class_schedules','attendance17','classes','class_enrollments','kids_activities'}),tables
print('FRESH_INSTALL_OK')"""],cwd=str(ROOT),env=env,capture_output=True,text=True,timeout=60)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert 'FRESH_INSTALL_OK' in result.stdout

def test_admin_cli_command_exists():
    from app import app
    assert 'create-admin' in app.cli.commands


def test_about_editor_installer_is_importable():
    from about_editor import install_about_editor
    assert callable(install_about_editor)

def test_retired_payment_trigger_cannot_break_sqlite_migrations():
    src=(get_file('site.py') if get_file('site.py').is_file() else get_file('app.py')).read_text(encoding='utf-8')
    notifications=get_file('notifications.py').read_text(encoding='utf-8')
    assert 'DROP TRIGGER IF EXISTS notify10_event_payment' in src
    assert 'DROP TRIGGER IF EXISTS notify10_event_payment' in notifications
    assert 'CREATE TRIGGER IF NOT EXISTS notify10_event_payment' not in notifications
