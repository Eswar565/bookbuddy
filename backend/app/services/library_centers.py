"""Library administration overview.
Existing CRUD and transactional endpoints remain the source of truth.
"""
from flask import abort, redirect, render_template


def install_library_centers(app, db, admin):
    def permitted(roles):
        user=admin()
        if not user:return None
        row=db().execute('SELECT role FROM admin_users WHERE id=? AND is_active=1',(user['id'],)).fetchone()
        if not row or row['role'] not in roles:abort(403)
        return user
    def count(table):
        # Fixed table names only; these are not composed from request input.
        return db().execute('SELECT COUNT(*) FROM '+table).fetchone()[0]

    @app.get('/admin/library-center/')
    def admin_library_center():
        user=permitted(('super_admin','org_admin','librarian'))
        if not user:return redirect('/admin/login/')
        counts={name:count(name) for name in ('books','lending_loans','lending_subscriptions','lending_plans')}
        return render_template('workspace/library_center.html',admin=user,title='Library Management',active='library-center',counts29=counts)

