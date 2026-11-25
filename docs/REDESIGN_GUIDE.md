# Book Buddy — Storybook Library Design

## Visual identity
Warm cream canvas, lively coral actions, sea-glass mint, soft lavender, and sunny yellow. Rounded cards, friendly display headings, accessible dark navy body text, colorful reading-themed vector illustrations. The brand is designed to appeal to children and parents without sacrificing library readability.

## Updated pages and flows
- Home: entirely new storybook hero, quick library links, featured book covers, reading circles and contests, interactive events calendar, newspaper, magazine, podcast, gallery, and registration invitation.
- About: light lavender community story, large photo/illustration area and videos.
- Library: illustrated heading, category/age/language/availability filters, friendly grid, illustrated placeholder covers.
- Events, reading circles, contests: illustrated heading, event image fallbacks, calendar and booking pages.
- Media: illustrated banners, fallbacks for publications and podcasts, photo-first gallery.
- Contact and member forms: consistent rounded inputs, spacious card layouts and illustrative banners.
- Member dashboard: friendly borrowing summary, profile, membership and upcoming events.
- Admin: redesigned library manager sidebar, readable form/table surfaces, colorful dashboard metrics, responsive menu and source-preserving controls.

## Change the design safely
The two newest CSS files (`storybook.css` and `storybook-admin.css`) are applied LAST and intentionally override previous UI styles while leaving the older library-specific utility class implementations in place. Retired CSS should not be deleted blindly: third-party/dynamic form editors may still reference a class. You may modify the new files alone for a global palette or spacing adjustment.

All SVG artworks live in `static/img/storybook/`. They require no remote services, API keys, image hotlinks or JavaScript libraries. Admin-uploaded images continue to take precedence.

## Existing data and route behavior
No database deletion, reset, or dummy-content import was added. Public navbar: Home, About, Library, Events (Reading Circles, Contests, Upcoming Events), Media (Newspaper, Magazine, Podcasts, Gallery), Contact, User Dashboard. Skills pages remain retired from the prior library-only release. The library-only backend is otherwise unchanged.

## Setup reminder
```
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
flask --app app create-admin
python run.py
```
For an existing deployment with a configured admin, do not recreate the admin; use your saved `.env` and `instance/` records. Always back them up before replacing code.
