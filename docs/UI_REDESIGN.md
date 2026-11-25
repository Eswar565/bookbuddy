# Book Buddy — Folio interface update

A complete source package based on the supplied v2(5).zip.

## Design
White and navy (#0A2472), system typography, an editorial homepage, a shared public/member/admin design system, responsive navigation, structured forms, cards and tables. All interface icons use the bundled Font Awesome library; no icon CDN is required. The new homepage uses real catalogue data and an honest empty state. Existing admin-controlled content, book covers and media remain supported.

## Interactions
Catalogue server filters; the existing asynchronous events calendar; member lending/membership actions; staff management forms; active sidebar links; mobile navigation; local table filtering with live result counts and empty states; comfortable/compact table rows; dismissible notices; visible keyboard focus; reduced-motion support. Table search only filters rows already loaded on the page. Use server search for the full database.

## Validation
15 pytest checks passed. 44 role-specific URL checks passed with local stylesheet/script availability checks. Public catalogue, event, media and form pages return 200 without sign-in. Personal member/admin pages remain private. Member and administrator checks use isolated QA accounts in a temporary database. JavaScript syntax check passed for folio.js. Existing About-page callable/connection mismatch fixed.

Run from the BookBuddy directory:

    python -m pip install -r requirements.txt -r requirements-dev.txt
    python -m pytest -q
    python tools/smoke_ui.py

The smoke script creates a separate temporary database and never uses the deployment database.

## Validation limits
Chromium could not be installed in this environment (the browser download was invalid). Visual alignment at real screen sizes, JavaScript interaction in a real browser, actual payments, email delivery and live cPanel hosting were not verified. URL checks are Flask test-client checks, not live-server tests. Review desktop/mobile layouts on staging before publishing.

## Upgrade
Back up your existing database, uploads and environment configuration. Extract the source into a staging folder. Keep your production .env, instance database and uploads; this archive intentionally contains no generated QA database, secrets or test accounts. Install requirements in the existing Python virtual environment, apply the updated source, and restart Passenger. Hard-refresh the browser to pick up folio.css?v=5 and folio.js?v=5. Public browsing no longer requires sign-in. Personal member/admin pages and book request actions remain protected.

Primary UI entry points: templates/site/base.html, templates/site/home.html, templates/workspace/base.html, static/css/folio.css and static/js/folio.js. Previous component CSS remains as structural compatibility support; storybook theme stylesheets are no longer loaded. Older illustrations remain as unused/backward-compatible assets where applicable.
