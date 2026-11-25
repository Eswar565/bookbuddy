# Official branding and hero update

The supplied logo is used unchanged in the public header, footer and admin sidebar. Its original 169 × 42 aspect ratio is preserved.

Phone: +91 9080759312
Email: bookbuddy.edu@gmail.com
Address: MK Complex 2nd floor Chennai Hot Puffs upstairs, K.Pudur, Madurai, Tamil Nadu 625007

These contact details apply on the first startup of this release to new and existing databases. Later edits through Admin > Settings remain preserved. The brand migration runs only once.

Hero hook: A book today. A bigger world tomorrow.
Primary action: Find your next read.
The calendar remains on the right. The headline, highlighted line, description, button, link and image are editable under Admin > Website controls > Homepage content & images; edit the hero record. The new Highlight field controls the emphasized line.

Deployment: keep your production database, uploads and private environment file. Replace source, restart Passenger, and hard-refresh for CSS v7. Existing payment configuration and access rules remain unchanged. See CPANEL_RAZORPAY_V6.md for hosting and webhook setup.

Validation: 28 automated tests passed, plus rendered checks for the logo, phone, email, address and highlighted hero text. Real-browser visual checks, live Razorpay and production cPanel verification remain outstanding.
