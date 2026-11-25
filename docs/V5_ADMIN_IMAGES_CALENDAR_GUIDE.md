# Homepage, images, calendar and catalogue update

## Admin editing
Admin > Website controls > Homepage content & images (also linked on the admin dashboard).
Edit titles, section text, kicker, image, alternative text, button label, destination link, display order and visibility. Upload a JPG/PNG/WebP using the existing validated upload service or paste an HTTP/HTTPS/local image URL. New uploads replace the URL; leave the upload empty to keep it. Six editable sections with bundled template illustrations are supplied on first startup. They are never reseeded after deletion or hiding. Add sections with unique section keys; the key hero controls the main hero. Other keys become image/text sections in the chosen order. The collection section also shows actual featured catalogue books.

Existing About, events, media, gallery, contact and membership editors continue to control their records. Interface labels such as Search and Apply filters are application text.

## Catalogue
Adult/Kids and Tamil/English/Hindi shortcuts appear above the results. Detailed search, collection, audience, language, age, author, format, availability, new arrivals and sort controls sit on the left. On phones the sidebar becomes an expandable full-width filter area. Combined filters persist across pagination. Set each book's new Audience field in its admin editor: All ages, Kids or Adults. All ages books appear in both audience selections. Existing records default to All ages unless their age-group label explicitly identifies kids/children/adults or 18+; review and classify your catalogue for accurate results. Language matches are case-insensitive; set language names consistently (Tamil, English, Hindi).

## Calendar
The calendar is on the left of the desktop hero. Mobile uses a stacked hero and calendar. Month/category changes refresh without a full page reload. Event dots identify dates with events. Selecting a date filters the agenda; Show all restores the month. Event rows link directly to the event registration form. Past events are labelled. Availability, capacity, booking deadlines and payments remain controlled by the existing booking workflow. No events are invented or automatically registered. Existing event admin records populate the calendar.

## Validation and deployment
15 tests passed, including real admin multipart image upload, URL save, visibility, audience/language filtering, free/paid access and calendar links. 44 test-client route checks passed. Calendar JavaScript syntax checked. Browser visual and click testing could not run because Chromium installation is unavailable; live hosting/payment/email delivery is not verified.
Back up your database, uploads and .env. Replace the source and restart Passenger. Additive schema changes run automatically. Keep your existing instance and media folders. Hard-refresh to load assets version 5. No QA databases or accounts are included. Public access, protected book requests and per-publication free/paid access remain in place.
