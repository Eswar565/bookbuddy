# BookBuddy Cleanup Report (Task C)

Audit performed on `backend/app/templates/` and `backend/app/static/`.

## 1. Summary of Analysis

Per the user requirements:
- **Delete NOW only:**
  1. Backup and duplicate files (`home_v7_backup.html`, `*.bak`, `*.png.bak`, legacy duplicate SVG pairs not referenced).
  2. Unreferenced legacy CSS and JS files that are not linked in any live template or route.
  3. Proven dead templates with no route, no include, and no dynamic CMS loader.
- **Strictly KEEP:**
  1. All templates and assets that any live route or CMS page renders until their React replacement is implemented and verified.
  2. All admin workspace templates (`templates/workspace/*`).
  3. Single design token stylesheet (`static/css/theme.css`) and actively loaded fonts/art.

---

## 2. Category A: Backup & Duplicate Files (Action: DELETE NOW)

These files are explicit backups, duplicate exports, or ad-hoc test screenshots that are never rendered by the application:

| File Path | Classification | Evidence & Reason | Action |
| :--- | :--- | :--- | :--- |
| `backend/app/templates/site/home_v7_backup.html` | Backup Duplicate | Superseded by `home.html`. No route renders this file. | **DELETE** |
| `backend/app/templates/site/portal/home_v7_backup.html` | Backup Duplicate | Superseded by `portal/home.html`. No route renders this file. | **DELETE** |
| `backend/app/static/img/storybook_legacy/` (15 SVG files) | Duplicate Legacy Art | Replaced in v7/v8 by clean PNG/SVG assets in `static/img/art/` and `static/img/storybook/`. Zero references in codebase. | **DELETE** |
| `ref_contribution.html` (repo root) | Test Scraping Artifact | One-off scrape reference file from past UI work. | **DELETE** |
| `ref_contribution_1920.png` (repo root) | Test Screenshot | Screenshot artifact from past manual check. | **DELETE** |
| `ref_magazine.html` (repo root) | Test Scraping Artifact | One-off scrape reference file from past UI work. | **DELETE** |
| `ref_magazine_1920.png` (repo root) | Test Screenshot | Screenshot artifact from past manual check. | **DELETE** |
| `test_*.png` (10 files at repo root) | Test Screenshots | E.g., `test_newspaper_mobile.png`, `test_admin_current.png`. Never part of production app. | **DELETE** |
| `UI_CHECK_RESULTS.json` (repo root) | Test Audit Log | Static test report file from legacy audit. | **DELETE** |

---

## 3. Category B: Unreferenced Legacy CSS & JS (Action: DELETE NOW)

These stylesheets and scripts are obsolete remnants from superseded redesigns (e.g. legacy Storybook theme, unused third-party bundles):

| File Path | Classification | Evidence & Reason | Action |
| :--- | :--- | :--- | :--- |
| `backend/app/static/css/storybook.css` | Obsolete Theme CSS | Explicitly verified as retired. `test_storybook_theme.py` line 30 verifies `assert '/static/css/storybook' not in shell`. Replaced by `theme.css`. | **DELETE** |
| `backend/app/static/css/storybook-admin.css` | Obsolete Theme CSS | Legacy admin styling superseded by `admin-ui-base.css` and `bb-admin-v8.css`. Zero template links. | **DELETE** |
| `backend/app/static/js/bookbuddy-refined.js` | Dead JS Script | Zero `<script>` references across all templates and py files. | **DELETE** |
| `backend/app/static/js/edition.js` | Dead JS Script | Zero references in templates. Superseded by modular scripts. | **DELETE** |
| `backend/app/static/js/library-edition.js` | Dead JS Script | Replaced by `borrow-cart.js` and modern catalogue JS. Zero references. | **DELETE** |
| `backend/app/static/js/flexible.js` | Dead JS Script | Replaced by server-side YouTube embed helpers in `flexible.py`. Zero references in templates. | **DELETE** |
| `backend/app/static/js/vendor/modernizr-3.5.0.min.js` | Unused Third-Party | Never linked in any template. Modern browser support uses standard ECMAScript. | **DELETE** |
| `backend/app/static/js/vendor/jquery-3.6.0.min.js` | Unused Third-Party | The application scripts (`navigation.js`, `borrow-cart.js`, `home-calendar.js`) are vanilla JS. | **DELETE** |
| `backend/app/static/js/vendor/html2canvas.min.js` & license | Unused Vendor Lib | Exporting is now handled server-side in Python (`library_filters.py` for Excel/PDF). | **DELETE** |
| `backend/app/static/js/vendor/jspdf.umd.min.js` & license | Unused Vendor Lib | Client-side jsPDF is unused; Python PyMuPDF / reportlab handles PDF generation. | **DELETE** |

---

## 4. Category C: Server-Rendered Templates (Action: KEEP until React Migration)

These templates are rendered by active Python endpoints (`app/routes/site.py`, `app/services/management.py`, `app/services/accounts.py`, `app/services/portal.py`) or included in page structures. They **MUST BE KEPT** until their React page equivalents are fully built and verified in Phase 4:

| Template Path | Rendered By / Included In | Purpose | Status |
| :--- | :--- | :--- | :--- |
| `templates/site/base.html` | Layout Root | Base layout for all public pages | **KEEP** |
| `templates/site/home.html` | `GET /` (`render_site("home")`) | Homepage | **KEEP** |
| `templates/site/library.html` | `GET /library/` (`paged_books()`) | Book Catalogue & Borrow Cart | **KEEP** |
| `templates/site/_compact_book_card.html` | `templates/site/library.html` | Book Card Component | **KEEP** |
| `templates/site/book_detail.html` | `GET /library/<id>/` | Single book details | **KEEP** |
| `templates/site/events.html` | `GET /events/` | Events listing | **KEEP** |
| `templates/site/event_detail.html` | `GET /events/<id>/` | Event detail & booking | **KEEP** |
| `templates/site/about.html` | `GET /about/` (dynamic page dispatcher) | About page | **KEEP** |
| `templates/site/contact.html` | `GET /contact/` (dynamic page dispatcher) | Contact & inquiry page | **KEEP** |
| `templates/site/visit_us.html` | `GET /visit-us/` | Directions, timings, location | **KEEP** |
| `templates/site/community.html` | `GET /community/` | Community workshops & hub | **KEEP** |
| `templates/site/collaborators.html` | `GET /collaborators/` | Partners & sponsors | **KEEP** |
| `templates/site/media_hub.html` | `GET /media-hub/`, `/newspaper/`, `/magazine/`, `/podcasts/` | Media releases & publications | **KEEP** |
| `templates/site/gallery.html` | `GET /gallery/` | Photo gallery categories | **KEEP** |
| `templates/site/gallery_category.html` | `GET /gallery/<slug>/` | Categorized photo albums | **KEEP** |
| `templates/site/calendar.html` | `GET /events/calendar/` | Interactive event calendar | **KEEP** |
| `templates/site/member_login.html` | `GET /accounts/login/` | Member authentication | **KEEP** |
| `templates/site/member_signup.html` | `GET /accounts/signup/` | Member registration | **KEEP** |
| `templates/site/profile.html` | `GET /accounts/profile/` | Member profile & active loans | **KEEP** |
| `templates/site/confirmation.html` | `POST /library/checkout/` | Request confirmation view | **KEEP** |
| `templates/site/error.html` | 404 & 500 error handlers | User error display | **KEEP** |
| `templates/workspace/*.html` (all 20 files) | `GET /admin/*` (`management.py`) | Admin panel (stays on Flask permanently) | **KEEP** |
| `templates/site/portal/*.html` (12 files) | `GET /members/*` (`portal.py`) | Member portal & borrowing management | **KEEP** |

---

## 5. Category D: Static Stylesheets, Scripts & Media (Action: KEEP)

| Static Path | Referenced By | Reason | Status |
| :--- | :--- | :--- | :--- |
| `static/css/theme.css` | All templates & React tokens | Core design token system (Inter font, `--navy`, `--maroon`, etc.) | **KEEP** |
| `static/css/style.css`, `brand-theme.css` | `templates/site/base.html` | Legacy base styling | **KEEP** |
| `static/css/library-ui.css`, `library-edition.css` | `templates/site/library.html` | Catalogue & book card layout | **KEEP** |
| `static/css/admin-*.css`, `bb-admin-*.css` | `templates/workspace/base.html` | Admin styling | **KEEP** |
| `static/js/borrow-cart.js` | `templates/site/library.html` | Unified cart engine | **KEEP** |
| `static/js/navigation.js` | `templates/site/base.html` | Header dropdowns & drawer | **KEEP** |
| `static/js/home-calendar.js`, `folio.js` | `templates/site/home.html` | Calendar & slider components | **KEEP** |
| `static/fonts/inter-*.woff2` | `static/css/theme.css` | Inter font family | **KEEP** |
| `static/fonts/hind-*.woff2` | Multilingual support | Regional Indian language typography | **KEEP** |
| `static/img/art/*` & `static/img/brand/*` | Site branding & covers | Production illustrations & logos | **KEEP** |
| `static/uploads/*` | Book database & gallery items | User-uploaded content | **KEEP** |

---

## 6. Execution Plan for Deletions

1. **Commit 1 (Dead Backups & Root Test Artifacts):**
   - Delete `templates/site/home_v7_backup.html`, `templates/site/portal/home_v7_backup.html`
   - Delete `static/img/storybook_legacy/`
   - Delete root `ref_*.html`, `ref_*.png`, `test_*.png`, `UI_CHECK_RESULTS.json`
2. **Commit 2 (Unreferenced Legacy CSS & JS):**
   - Delete `static/css/storybook.css`, `static/css/storybook-admin.css`
   - Delete `static/js/bookbuddy-refined.js`, `static/js/edition.js`, `static/js/library-edition.js`, `static/js/flexible.js`
   - Delete `static/js/vendor/modernizr-3.5.0.min.js`, `static/js/vendor/jquery-3.6.0.min.js`, `static/js/vendor/html2canvas*`, `static/js/vendor/jspdf*`
3. **Verification:**
   - Run `pytest` to confirm 66/66 tests pass.
   - Run Flask server to confirm 200 responses on all public and admin pages.
