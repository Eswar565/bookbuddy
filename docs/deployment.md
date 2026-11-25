# Book Buddy v6 — cPanel and Razorpay setup

## What changed
The hero is on the left and calendar on the right on desktop; mobile stacks them. The calendar has compact circular dates, quiet weekday labels, event markers and a filtered agenda. Admin forms, uploads, tables and navigation now use consistent spacing and typography. The public catalogue, free/paid media rules, admin-controlled homepage and image features remain available.

Existing event and membership Razorpay flows are retained and hardened: membership order responses are checked against server amounts/currency, captured payments are required, signatures are validated and repeated callbacks cannot activate benefits twice. Membership webhooks safely ignore unrelated event orders in a shared Razorpay account and reject malformed payloads. Membership checkout is a one-time payment for a fixed-duration membership; it is not automatic recurring billing.

## 1. Configure the Python app
Back up the current database and media folders before replacing source. Keep your production .env, database and uploads. Extract BookBuddy to an application directory such as /home2/CPANELUSER/bookbuddy outside public_html. Use your actual account home (some hosts use /home instead of /home2).

In cPanel Setup Python App choose Python 3.11 or newer, the BookBuddy application root, your HTTPS domain, startup file passenger_wsgi.py and entry point application. Keep cPanel-generated Passenger configuration rather than replacing it with another host's .htaccess. Use the virtualenv activation command cPanel displays.

Inside the application directory with that virtualenv active:

    python -m pip install -r requirements.txt

Copy .env.cpanel.example to a PRIVATE environment file, for example /home2/CPANELUSER/private/bookbuddy.env. Create the private folder first. Set BOOK_BUDDY_ENV_FILE to that absolute path in the cPanel environment settings. Fill in the actual HTTPS SITE_URL and PUBLIC_BASE_URL, database/private/backup locations and a long random SECRET_KEY. Use COOKIE_SECURE=1 and FLASK_DEBUG=0.

Generate a secret locally with:

    python -c "import secrets; print(secrets.token_hex(32))"

Do not reset SECRET_KEY on each restart. The app/virtualenv must be able to write the database parent, private files, backups and application media directories; do not use world-writable permissions. Preserve all existing media and static/uploads files when upgrading. Keep the application source/assets outside the public document root; do not expose a separate public alias to paid media/static uploads, because those requests must reach the Flask access checks through Passenger.

Restart the Python app in cPanel after source/env changes. Schema additions apply on startup. Hard-refresh to load CSS v6.

## 2. Create an administrator and check deployment
From the app directory with the same environment file configured:

    python -m flask --app app create-admin
    python tools/cpanel_check.py

The check reports missing configuration without printing secret values, performs SQLite integrity and Passenger route checks, and sends no network payment or email. It exits nonzero until all required configuration passes. Do not run pytest against your production database.

## 3. Razorpay events and membership
Set the following private environment variables:

- RAZORPAY_KEY_ID: test key first, live key after staging verification.
- RAZORPAY_KEY_SECRET: matching API secret.
- RAZORPAY_WEBHOOK_SECRET: your chosen event-webhook secret.
- RAZORPAY_MEMBERSHIP_WEBHOOK_SECRET: your chosen membership-webhook secret.

Create these two HTTPS webhooks in your Razorpay dashboard, replacing YOUR-DOMAIN:

Event payments:
    https://YOUR-DOMAIN/payments/razorpay/webhook/
Events: payment.captured and order.paid
Secret: RAZORPAY_WEBHOOK_SECRET

Membership payments:
    https://YOUR-DOMAIN/payments/membership/webhook/
Events: payment.captured, order.paid, payment.failed, refund.processed
Secret: RAZORPAY_MEMBERSHIP_WEBHOOK_SECRET

Use separate matching webhook secrets. Configure captured payments in your Razorpay dashboard; authorization alone does not confirm a booking or membership. The server checks HMAC signatures, stored order IDs, amount, currency and capture status. Do not put API secrets into templates or JavaScript. cPanel must allow outbound HTTPS to api.razorpay.com; the visitor browser needs checkout.razorpay.com. The webhook URLs must accept Razorpay POST requests through any host firewall.

Events: Admin > Events > add date/time, capacity and fee. A zero-fee event confirms directly. A paid guest registration creates a server-priced order; successful captured payment confirms places, subject to capacity/deadline. Late payments that cannot be fulfilled enter Payment review for staff handling; this does not automatically refund money.

Membership: Admin > Library > Membership plans. The user signs in, selects a plan, opens billing, prepares checkout, and pays through Razorpay. Verified payment activates the membership or schedules it after an existing membership. A verified full refund cancels benefits; partial refunds require staff review. Refund actions through the Razorpay dashboard should also be checked in the app.

## 4. Background tasks
Use the exact virtualenv Python path shown by cPanel, with the app folder as working directory and BOOK_BUDDY_ENV_FILE set. Schedule `python -m flask --app app send-mail` once each minute (at most one queued email per run), `python -m flask --app app maintenance` daily, and `python -m flask --app app backup` daily. Configure SMTP only if sending mail. Keep cron logs and backups outside public_html.

## 5. Validation and go-live
Automated validation completed: 28 tests; 44 Flask test-client route checks; JavaScript syntax checks; Passenger WSGI import. Tests cover admin image upload, catalogue filters, public/private media, valid/invalid payment signatures, wrong amount/currency, authorized-only payments, captured payments, duplicate callbacks/webhooks, malformed webhooks, shared-account orders, free events and capacity limits. Gateway network responses are mocked; no real money was moved.

Still required on your staging host: desktop/mobile visual checks, real Razorpay test-mode checkout, webhook deliveries, SMTP delivery, HTTPS cookie behavior, upload/download tests and cPanel restart. Browser visual testing could not run here because Chromium installation failed. Live Razorpay settlement and the user's cPanel environment have not been verified; this archive is not a claim of a fully live-tested deployment.

Useful commands on a development/staging copy only:

    python -m pip install -r requirements-dev.txt
    BOOK_BUDDY_DATABASE=/tmp/bookbuddy-test.sqlite3 python -m pytest -q
    python tools/smoke_ui.py

Official references used for payment review:
https://github.com/razorpay/markdown-docs/blob/master/payments/payment-gateway/web-integration/standard/integration-steps.md
https://github.com/razorpay/markdown-docs/blob/master/webhooks/validate-test.md
