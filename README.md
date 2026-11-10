# Current release: v7

See **V7_LOGO_CONTACT_HERO.md** for branding changes and **CPANEL_RAZORPAY_V6.md** for deployment.

# Current release: v6

Start with **CPANEL_RAZORPAY_V6.md** for current deployment, payment setup and validation limits.

# Book Buddy · Library Website · Version 1

This is the **library-focused** Flask website and admin panel.

**Public navigation:** Home, About, Library, Events (Reading Circles / Contests / Upcoming Events), Media (Newspaper / Magazine / Podcasts / Gallery), Contact, User Dashboard.

**Admin:** Library catalogue and inventory, lending, membership approvals, events and registrations, publications, gallery, enquiries, reader accounts, notifications, staff permissions and website editors.

The Skills/Class module is not loaded. The standalone install does not create class schedules, class enrollments, or worksheet/activity tables. The About content is stored in the site's own database and edited under **Admin → About**. No sample data or external About text is downloaded on startup.

## Windows PowerShell — start for the first time

```powershell
cd "D:\5.Our Products\Website\Book Buddy\BookBuddy"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
flask --app app create-admin
python run.py
```

Open `http://127.0.0.1:5000/`. Admin login: `/admin/login/`.

**For a clean Version 1 folder:** delete old project source files first, then extract this ZIP. **Keep a backup** of the old folder (including `.env`, `instance/`, and your uploaded media). Do not merge this ZIP into an older source directory: removed modules would otherwise remain on disk.

**Existing database:** Keep `BOOK_BUDDY_DATABASE` pointing to the previous SQLite database to retain existing book records, users, borrowing, plan and publication data. The new code does not delete older lesson or class tables from existing databases; those tables simply are not exposed. Migrate manually only after a verified backup if you need physical data removal.

**Local testing:** `python -m pytest -q` automatically uses an isolated temporary copy of the database and disables notifications (`APP_ENV=testing`). Automated test suites never write to or pollute the development or production database.

**Database & Environments:**
- `APP_ENV=development`: Default for local development via `python run.py`. Automatically uses `instance/book_buddy_dev.sqlite3` (auto-cloned from `book_buddy.sqlite3` on first run) and sets `notifications_enabled='0'` in `app_flags` table to prevent notification bell spam from local testing.
- `APP_ENV=production`: Uses `instance/book_buddy.sqlite3` (or the path set by `BOOK_BUDDY_DATABASE`) with `notifications_enabled='1'`.
- Override with `BOOK_BUDDY_DATABASE` or `BOOK_BUDDY_DB` to target any specific database file.
- Event booking notifications fire only for confirmed/paid registrations and free events (not abandoned/pending checkouts).


**Production:** Set a secure `SECRET_KEY`, `COOKIE_SECURE=1` on HTTPS, and configure the public base URL. Keep writable `instance/` and uploads outside source replacement. cPanel Passenger uses `passenger_wsgi.py`; restart via `tmp/restart.txt`.

## Startup repair (Version 1.1)

This release corrects the previous `sqlite3.OperationalError: no such table: class_schedules` on `flask --app app create-admin`. The library portal no longer migrates or creates old class schedules or class attendance. The CLI command can be registered without a historical learning database.

**Safe upgrade:** Make a backup of your current `instance/`, `.env`, and uploads. Extract this release into a **new** `BookBuddy` folder, then copy only your preserved `instance/`, `.env` and uploaded media into that folder. Do not overwrite source code with old modules. Existing SQLite historical tables and historical records are left untouched; this is not a destructive migration.

Run `python -m pip install -r requirements.txt`, `flask --app app --help` and then `flask --app app create-admin` (or `flask --app app run`). If the admin account already exists, use its previous credentials rather than creating another.

**Other fixes included:** The installer uses the correct `install_about_editor` function name, and it drops the obsolete `notify10_event_payment` SQLite trigger that referred to a missing `payment_status` column. Event registration notifications remain enabled. The project intentionally retains compatible historical lending subscription fields and does not delete users, books, or payments.

To run regression tests on Windows: `python -m pip install -r requirements-dev.txt` then `python -m pytest -q`. Always use a test database or back up your production data before running tests.

## Storybook redesign — Version 1 visual refresh

This edition has a **completely new, child-friendly library presentation**, replacing the previous corporate layout. It keeps all existing routes, forms, admin functionality and database handling; this is a **front-end redesign, not a new database schema**.

- Public stylesheet: `static/css/storybook.css` (loaded after the compatible legacy structural styles).
- Admin stylesheet: `static/css/storybook-admin.css` (loaded last in the workspace layout).
- New homepages: `templates/site/home.html` and `templates/site/portal/home.html`.
- Per-page illustration banner: `templates/site/_storybook_banner.html`.
- Local original vector artwork: `static/img/storybook/` (including illustrated hero, bookshelf, reading circle, contest, magazine, newspaper, podcast, gallery, membership, contact and fallback book cover designs).
- Header/footer wordmark: `static/img/storybook/bookbuddy-playful-logo.svg`. The original branding files are retained under `static/img/brand/` and can be restored if preferred.

**Your admin-uploaded book covers, gallery photos, event thumbnails, and publication covers are never replaced.** New SVGs are supplementary images or illustrated placeholders when an image is unavailable. No dummy books, events, or publications have been inserted into the database. Uploaded image/media records stay unchanged.

**Safe update:** Extract into a fresh folder; copy `.env`, `instance/` and `static/uploads/` from your previous install to keep books, users, membership/borrowing history and files. Do not copy old templates or styles into the refreshed folder. Use your existing admin credentials, or run `flask --app app create-admin` for a new database.

**Quality notes:** The HTML templates and SVGs have been parsed, Python sources compiled, and SQLite schema smoke tests have passed in a validation environment. Live Flask request/response testing is not available in that environment because Flask could not be installed there; test sign-up, borrowing, event registration, payment and admin CRUD workflows on your local development copy before production rollout. Visual browser screenshots could not be completed in that environment.

---

## Deploy the demo

### 1. Persistent-Disk Cloud Host (Render / Railway / VPS / Docker)

1. **Persistent Disk**: Attach a persistent disk (e.g. 1 GB mounted at `/var/data`).
2. **Environment Variables**:
   - `DEMO_MODE=1`
   - `SECRET_KEY=<generate random 32+ char string>`
   - `COOKIE_SECURE=1`
   - `ADMIN_EMAIL=admin@example.com`
   - `ADMIN_PASSWORD=<secure-password>`
   - `BOOK_BUDDY_DATABASE=/var/data/book_buddy.sqlite3`
   - `MEDIA_ROOT=/var/data/media`
   - `RAZORPAY_KEY_ID=` (leave blank in demo mode)
   - `RAZORPAY_KEY_SECRET=` (leave blank in demo mode)
   - `GEMINI_API_KEY=` (leave blank if unused)
3. **Build & Start**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --workers 2 --timeout 120` (as defined in `Procfile` / `render.yaml`)
   - Health check path: `/healthz`
4. **Seed Demo Data & Snapshot**:
   - Run once via SSH or job runner:
     ```bash
     python tools/make_demo_data.py --target /var/data/book_buddy.sqlite3 --media /var/data/media
     ```
   - To quickly reset before each client demo:
     ```bash
     python tools/reset_demo.py
     ```

### 2. cPanel (CloudLinux / Phusion Passenger)

1. **Python App Setup**:
   - In cPanel, navigate to **Setup Python App**.
   - Create an application (Python 3.11 or 3.12).
   - Application root: `/home/USERNAME/bookbuddy`
   - Application URL: `https://demo.yourdomain.com`
   - Application startup file: `passenger_wsgi.py`
   - Application entry point: `application`
2. **Environment Variables** (in cPanel interface or `.env` outside `public_html`):
   - `DEMO_MODE=1`
   - `SECRET_KEY=<secure-random-key>`
   - `COOKIE_SECURE=1`
   - `BOOK_BUDDY_DATABASE=/home/USERNAME/private/book_buddy.sqlite3`
   - `MEDIA_ROOT=/home/USERNAME/private/media`
3. **Dependencies & Demo Data**:
   - Enter the Python virtualenv via SSH or terminal:
     ```bash
     source /home/USERNAME/virtualenv/bookbuddy/3.11/bin/activate
     pip install -r requirements.txt
     python tools/make_demo_data.py --target /home/USERNAME/private/book_buddy.sqlite3 --media /home/USERNAME/private/media
     ```
4. **Restart**:
   - Touch `tmp/restart.txt` or click **Restart** in cPanel.

# bookbuddy
