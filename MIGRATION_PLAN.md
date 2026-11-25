# BookBuddy Frontend Migration Plan: Flask/Jinja to React + Vite

**Document Version:** 1.0.0  
**Date:** 25-11-2026  
**Status:** Awaiting Approval (Phase 0 Audit Complete)

---

## 1. Executive Summary & Migration Objectives

BookBuddy is currently powered by a Flask + SQLite backend rendering server-side Jinja templates with custom vanilla CSS and vanilla JavaScript. This migration moves the public and member-facing frontend to a modern **React 18 + TypeScript + Vite** Single Page Application (SPA), while retaining:
1. **The Flask backend and SQLite database** (no database schema changes, no rewrite of core business rules).
2. **All existing URLs and SEO paths** (canonical URLs, meta descriptions, redirects for legacy paths).
3. **Existing Flask/Jinja Admin Panel** (retained under `/admin/*` without disruption).
4. **Single-font and token design system** (Inter font, CSS variables derived from `static/css/theme.css`).
5. **cPanel / Passenger WSGI compatibility** (`passenger_wsgi.py` serving Flask, with Flask serving the built SPA assets and handling the SPA route fallback).

---

## 2. Complete Route Inventory

### 2.1 Public Frontend Routes (Targeted for React Migration)

| URL Path | Flask Handler | Current Template | Target React Route | Key Data Required |
| :--- | :--- | :--- | :--- | :--- |
| `/` | `index` (`app.py`) | `site/home.html` | `/` (`Home.tsx`) | Hero content, upcoming events calendar, featured books (up to 8), reading highlights, statistics, working hours. |
| `/about/`, `/about-us/` | `about_page` (`app.py`) | `site/about.html` | `/about` (`About.tsx`) | About sections (intro, story, mission, team, vision, values, stats). |
| `/visit-us/` | `visit_us_page` (`app.py`) | `site/visit_us.html` | `/visit-us` (`VisitUs.tsx`) | Working hours, address, transit instructions, borrowing policies, guidelines, Google Maps embed info. |
| `/contact/` | `contact_page` (`app.py`) | `site/contact.html` | `/contact` (`Contact.tsx`) | Contact details, library working hours, contact form submission (`POST /api/v1/contact`). |
| `/library/` | `modern_library` (`app.py`) | `site/library.html` | `/library` (`Catalogue.tsx`) | Paginated books list, filter facets (age group, audience/reader type, language, author, collection, availability, new arrivals), quick chips, export URLs (`/export/xlsx/`, `/export/pdf/`), cart checkout modal. |
| `/library/<int:book_id>/` | `book_detail` (`app.py`) | `site/book_detail.html` | `/library/:bookId` (`BookDetail.tsx`) | Book details (title, author, copies, stock, language, category, synopsis, cover, availability status, similar titles). |
| `/membership/`, `/membership-options/` | `membership` (`portal.py`) | `site/membership.html` | `/membership` (`Membership.tsx`) | Active plans list (`lending_plans`), tiers, pricing, delivery fee rates, service mode settings, subscription modal with Razorpay checkout. |
| `/how-to-borrow/` | `how_to_borrow_route` (`app.py`) | `pages/how-to-borrow.html` | `/how-to-borrow` (`HowToBorrow.tsx`) | How-to-borrow steps, policy rules, plan matrix, FAQs. |
| `/community/` | `community_page` (`app.py`) | `site/community.html` | `/community` (`Community.tsx`) | Community highlights, reading circles summary, workshops, member spotlight, contribute CTA. |
| `/media/` | `media_hub_page` (`app.py`) | `site/media_hub.html` | `/media` (`MediaHub.tsx`) | Filtered media by kind (newspaper, magazine, podcast), cover thumbnails, publication date, download/view links. |
| `/newspaper/` | `newspaper_page` (`app.py`) | `site/newspaper.html` | `/newspaper` (`Newspaper.tsx`) | Newspaper issues, issue viewer, archive downloads. |
| `/magazine/` | `magazine_page` (`app.py`) | `site/magazine.html` | `/magazine` (`Magazine.tsx`) | The Book Buddy Times issues, articles, submission link. |
| `/podcasts/` | `podcasts_page` (`app.py`) | `site/podcasts.html` | `/podcasts` (`Podcasts.tsx`) | Podcast episodes, audio players, descriptions. |
| `/events/`, `/calendar/` | `events_page` (`app.py`) | `site/events.html` | `/events` (`Events.tsx`) | Active events calendar, categorized tabs (reading circles, contests, upcoming workshops), event booking modal. |
| `/event/<int:event_id>/` | `event_detail` (`app.py`) | `site/event_detail.html` | `/events/:eventId` (`EventDetail.tsx`) | Event information, speaker, seats remaining, price, registration/payment. |
| `/gallery/` | `gallery_home` (`app.py`) | `site/gallery.html` | `/gallery` (`Gallery.tsx`) | 4 Category tiles (Reading Moments, Events & Workshops, Our Space, Community Events) with cover photo and item count. |
| `/gallery/<slug>/` | `gallery_category` (`app.py`) | `site/gallery_category.html` | `/gallery/:slug` (`GalleryCategory.tsx`) | Category image grid, interactive lightbox, contextual bottom CTA link. |
| `/collaborators/` | `collaborators_page` (`app.py`) | `site/collaborators.html` | `/collaborators` (`Collaborators.tsx`) | 4 Sections (Library Partners, Storytellers & Authors, Community Partners, Creative Partners) with partner cards. |
| `/work-with-us/` | `work_with_us_page` (`app.py`) | `site/work_with_us.html` | `/work-with-us` (`WorkWithUs.tsx`) | Partner enquiry form, collaboration types. |

### 2.2 Authentication & Member Portal Routes

| URL Path | Flask Handler | Current Template | Target React Route | Key Data Required |
| :--- | :--- | :--- | :--- | :--- |
| `/accounts/login/` | `account_login` (`accounts.py`) | `site/accounts/login.html` | `/login` (`Login.tsx`) | Login form (email, password), CSRF token, redirect param. |
| `/accounts/signup/` | `account_signup` (`accounts.py`) | `site/accounts/signup.html` | `/signup` (`Signup.tsx`) | Signup form (name, email, phone, password, child age/dob, grade). |
| `/accounts/password/reset/` | `account_reset_password` (`accounts.py`) | `site/accounts/reset.html` | `/forgot-password` (`ForgotPassword.tsx`) | Password reset request form. |
| `/accounts/password/new/<token>/` | `reset_finish17` (`accounts.py`) | `site/accounts/reset_finish.html` | `/reset-password/:token` (`ResetPassword.tsx`) | New password entry with security token. |
| `/members/dashboard/` | `member_dashboard` (`accounts.py`) | `site/accounts/dashboard.html` | `/dashboard` (`Dashboard.tsx`) | Active subscription details, active loans, pending requests, remaining slots, reading history, quick return request action. |
| `/members/loans/` | `member_loans` (`accounts.py`) | `site/accounts/dashboard.html` | `/dashboard/loans` (`Loans.tsx`) | All current loans, return request button, cancellation of requested loans. |
| `/members/profile/` | `profile_v16` (`accounts.py`) | `site/accounts/profile.html` | `/dashboard/profile` (`Profile.tsx`) | User profile update (name, phone, address, child info, password change). |
| `/members/billing/<int:sid>/` | `billing17` (`portal.py`) | `site/portal/billing.html` | `/membership/checkout/:subId` (`MembershipBilling.tsx`) | Pending subscription order, Razorpay SDK initialization, offline instructions. |
| `/members/notifications/` | `notifications17` (`accounts.py`) | `site/portal/notifications.html` | `/dashboard/notifications` (`Notifications.tsx`) | Member notification feed, mark as read. |

### 2.3 Existing Flask Admin Routes (Preserved As-Is in Jinja)

These routes are **not** rewritten into React and remain directly handled by Flask under `/admin/*`:
- `/admin/`, `/admin/dashboard/` (Admin overview dashboard)
- `/admin/login/`, `/admin/logout/` (Admin authentication)
- `/admin/manage/<kind>/` (Books, partners, collaborators, hero banners, working hours, enquiries, pages)
- `/admin/lending/` (Lending desk, issue/return/renew, batch requests)
- `/admin/membership-desk/` (Subscription approvals, payment verification)
- `/admin/appearance/` (Brand colors, typography, theme toggles)
- `/admin/about-editor/`, `/admin/how-to-borrow-editor/`
- `/admin/events/`, `/admin/reports17/`, `/admin/media/`, `/admin/settings/`

---

## 3. Template, JavaScript, and CSS Inventory

### 3.1 Template Inventory (93 templates)
* **Public Site Templates (`templates/site/`, 40 files):**
  - Layout & Partials: `base.html`, `_compact_book_card.html`, `_icons_sprite.html`, `_visit_us_content.html`, `_storybook_banner.html`.
  - Core Pages: `home.html`, `library.html`, `book_detail.html`, `about.html`, `visit_us.html`, `contact.html`, `membership.html`, `community.html`, `events.html`, `event_detail.html`, `event_booking.html`, `gallery.html`, `gallery_category.html`, `collaborators.html`, `media_hub.html`, `newspaper.html`, `magazine.html`, `podcasts.html`, `publications.html`, `publication_detail.html`, `work_with_us.html`, `error.html`.
  - Member Portal: `site/accounts/login.html`, `signup.html`, `dashboard.html`, `profile.html`, `plans.html`, `statement.html`, `how_to_borrow.html`.
  - Portal & Billing: `site/portal/billing.html`, `chat.html`, `notifications.html`, `support.html`, `reset.html`.
* **Admin & Workspace Templates (`templates/workspace/`, 33 files):**
  - `workspace/base.html`, `dashboard.html`, `lending.html`, `membership.html`, `plans.html`, `appearance.html`, `about_editor.html`, `how_to_borrow_editor.html`, `gallery_manager.html`, `book_inquiries.html`, `edit.html`, `list.html`, `settings.html`, etc.

### 3.2 JavaScript Files (`static/js/`, 18 files)
1. `borrow-cart.js`: Shared borrow cart state (`localStorage.bb_cart`), event delegation, bump animation, checkout modal.
2. `bb-gallery.js`: Gallery category lightbox and filter controls.
3. `bb-media.js`: Media hub filters and audio player toggles.
4. `home-calendar.js`: Interactive calendar date picker and event cards switcher.
5. `bookbuddy.js`: Razorpay payment checkout integration and legacy form validation.
6. `bookbuddy-refined.js`, `library-edition.js`, `edition.js`, `flexible.js`, `folio.js`, `navigation.js`: Responsive navigation, search drawers, scroll listeners.
7. `admin.js`, `admin-notifications.js`, `admin-preview.js`: Admin-specific desk behaviors.
8. Vendor libraries: `jspdf.umd.min.js`, `html2canvas.min.js`, `jquery-3.6.0.min.js`, `modernizr-3.5.0.min.js`.

### 3.3 CSS Files (`static/css/`, 32 files)
1. **Core Single Theme & Variables:** `theme.css` (Contains the frozen typography, color variables `--navy`, `--maroon`, `--cream`, `--gold`, `.bb-book-grid`, `.bb-modal`, `.bb-card`).
2. **Supplemental stylesheets:** `bb-tokens.css`, `bb-typography.css`, `bb-icons.css`, `brand-theme.css`, `bb-home-v8.css`, `bb-membership.css`, `bb-gallery.css`, `bb-media.css`, `bb-visit-us.css`, `bookbuddy.css`, `library-ui.css`, `library-edition.css`, `flexible.css`, `folio.css`.
3. **Admin Styles:** `admin.css`, `admin-layout.css`, `admin-ui-base.css`, `admin-ui-controls.css`, `admin-ui-filters.css`, `admin-ui-layout.css`, `about-editor.css`, `bookbuddy-admin.css`, `storybook-admin.css`.

---

## 4. Page Data Requirements & Endpoint Conversions

| Page / Component | Required Data Payload | Proposed API Endpoint | HTTP Method |
| :--- | :--- | :--- | :--- |
| **Global App Shell** | Navigation hierarchy, site settings, active announcement, current user session state, CSRF token. | `/api/v1/bootstrap` | `GET` |
| **Auth State** | Current authenticated user `{id, name, email, phone, role, active_subscription, remaining_slots}`. | `/api/v1/auth/me` | `GET` |
| **Auth Actions** | Login, signup, password reset request, password reset confirm, logout. | `/api/v1/auth/login`<br>`/api/v1/auth/signup`<br>`/api/v1/auth/logout`<br>`/api/v1/auth/reset-password` | `POST` |
| **Home Page** | Hero copy, upcoming events list, calendar events map by date, featured books (8), statistics. | `/api/v1/home` | `GET` |
| **Catalogue Page** | Filtered books array, total count, page, pages, available filter facets (age, language, category). | `/api/v1/books` | `GET` |
| **Book Detail** | Full book metadata, stock, availability status, active loan flag, related books. | `/api/v1/books/:id` | `GET` |
| **Catalogue Export** | File downloads for Excel (.xlsx) and PDF (.pdf). | `/library/export/<fmt>/` | `GET` *(Retained on Flask)* |
| **Borrow Checkout** | Selected `book_ids`, user contact details, delivery mode (`offline` / `online`), address. | `/api/v1/library/checkout` | `POST` |
| **Membership Plans** | Active plans (`lending_plans`), features list, duration, fee rates, service mode settings. | `/api/v1/memberships/plans` | `GET` |
| **Membership Subscribe** | Selected `plan_id`, child info, delivery mode, address, referral code, coupon. Creates subscription & Razorpay order. | `/api/v1/memberships/subscribe` | `POST` |
| **Razorpay Verify** | `subscription_id`, `razorpay_payment_id`, `razorpay_order_id`, `razorpay_signature`. | `/api/v1/memberships/verify-payment` | `POST` |
| **Events Page** | All events categorized (`upcoming`, `reading-circle`, `contest`), past events. | `/api/v1/events` | `GET` |
| **Event Detail & Booking** | Event info, seats, booking creation with Razorpay checkout payload. | `/api/v1/events/:id`<br>`/api/v1/events/:id/book` | `GET`<br>`POST` |
| **Gallery Categories** | Category list (4 items: Reading Moments, Events & Workshops, Our Space, Community Events) with counts. | `/api/v1/gallery` | `GET` |
| **Gallery Category Items** | Category metadata, list of photos `{id, title, image_url, caption, sort_order}`. | `/api/v1/gallery/:slug` | `GET` |
| **Collaborators** | 4 sections with partner items `{id, name, category, brief, image, link}`. | `/api/v1/collaborators` | `GET` |
| **Media / Publications** | Filtered publications `{id, title, kind, published_on, cover_image, file_url}`. | `/api/v1/publications` | `GET` |
| **Contact Form** | Inquiry payload `{name, email, phone, message, subject}`. | `/api/v1/contact` | `POST` |
| **Member Dashboard** | Active subscription details, active loans, pending requests, notification count. | `/api/v1/members/dashboard` | `GET` |
| **Member Loan Return** | Request return for an issued loan `{loan_id}`. | `/api/v1/members/loans/:id/return` | `POST` |
| **Member Cancel Request**| Cancel pending requested loan `{loan_id}`. | `/api/v1/members/loans/:id/cancel` | `POST` |

---

## 5. Architecture: Auth, Session, CSRF, and Razorpay

### 5.1 Authentication & Session Handling
- **Mechanism:** Retain Flask secure cookie session (`session['user_id']`).
- **Cookie Security:** `HttpOnly=True`, `SameSite='Lax'`, `Secure=True` in production (`COOKIE_SECURE` configured via `.env`).
- **React Integration:** The React frontend performs all requests with `credentials: 'include'`.
- **State Hydration:** On initial load, TanStack Query calls `GET /api/v1/auth/me` to hydrate the React `AuthContext`.
- **Route Guards:** A React `<ProtectedRoute>` component protects `/dashboard/*` and automatically redirects unauthenticated users to `/login?next=...` while saving intended destination.

### 5.2 CSRF Protection
- **CSRF Token Endpoint:** `GET /api/v1/csrf` returns `{ ok: true, csrf_token: "<token>" }`.
- **Header Propagation:** All mutating calls (`POST`, `PUT`, `DELETE`, `PATCH`) in React attach the header:
  `X-CSRFToken: <token>`.
- **Flask Validation:** The Flask API blueprint runs a `@before_request` hook validating the CSRF token on mutating methods using Flask's existing session token generator.

### 5.3 Razorpay Payment Flow in React
1. **Plan Selection:** Member selects a plan on `/membership` and fills child/delivery details in the subscription modal.
2. **Order Creation:** React sends `POST /api/v1/memberships/subscribe`. Flask creates/updates the `lending_subscriptions` row and calls Razorpay API to generate `razorpay_order_id`.
3. **Modal Launch:** React dynamically loads `https://checkout.razorpay.com/v1/checkout.js` and opens the Razorpay popup using the public `RAZORPAY_KEY_ID`.
4. **Signature Verification:** On `handler(response)` callback, React sends `{ subscription_id, razorpay_order_id, razorpay_payment_id, razorpay_signature }` to `POST /api/v1/memberships/verify-payment`.
5. **Reconciliation:** Backend verifies the HMAC SHA256 signature, activates the subscription, and returns `{ ok: true, subscription_id }`. React redirects the user to `/dashboard` with a success toast.
6. **Webhooks:** The existing webhook endpoints (`/payments/membership/webhook/` and `/payments/razorpay/webhook/`) remain completely untouched as server-to-server endpoints.

---

## 6. Admin Panel Scope & Isolation

- **Preservation:** The existing Flask/Jinja admin interface (`/admin/*`) is retained completely.
- **SPA Fallback Routing Rule:** In Flask, the SPA fallback route catches unmatched frontend routes and returns `frontend/dist/index.html`. It **explicitly ignores** paths beginning with:
  - `/api/` (API requests return standard JSON 404)
  - `/admin/` (Handled by existing admin view functions; unauthenticated access redirects to `/admin/login/`)
  - `/static/` and `/media/` (Static file handlers)
  - `/library/export/` (Direct Excel and PDF binary streams)
- This guarantees zero regressions for staff and librarians managing books, loans, and content.

---

## 7. Build, Deployment, and SEO Strategy

### 7.1 Development Environment
- React project lives in `frontend/` powered by **Vite**.
- Vite dev server runs on `http://localhost:5173` with proxy configured in `vite.config.ts`:
  ```typescript
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:5000',
      '/media': 'http://127.0.0.1:5000',
      '/static': 'http://127.0.0.1:5000',
      '/admin': 'http://127.0.0.1:5000'
    }
  }
  ```

### 7.2 Production Build & cPanel / Passenger WSGI Integration
- Build command: `npm run build` in `frontend/` outputs static assets to `frontend/dist/`.
- Flask serves the static bundle:
  - Cache-Control headers: `public, max-age=31536000, immutable` for hashed assets (`/assets/*.js`, `/assets/*.css`).
  - `no-cache, no-store, must-revalidate` for `index.html`.
- `passenger_wsgi.py` continues to launch `app.app` without modification. A documented build script `build_frontend.py` or `npm run build` is run during deployment before reloading Passenger.

### 7.3 SEO & Meta Management
- **Per-Page Metadata:** React app uses `react-helmet-async` on every page to inject canonical titles, descriptions, and OpenGraph meta tags.
- **Robots & Sitemap:** Handled directly by Flask routes `/robots.txt` and `/sitemap.xml` so search engines can crawl all indexable paths.
- **Prerendering Recommendation:** Because BookBuddy relies on search engine discovery for its book catalogue, library events, and membership options, **prerendering static public routes via `vite-plugin-prerender` (or static HTML snapshots via `react-snap`)** is recommended for key public pages (`/`, `/about`, `/visit-us`, `/membership`, `/library`, `/community`, `/collaborators`, `/how-to-borrow`). This ensures search engine crawlers without JavaScript execution receive full semantic HTML while users enjoy instant client-side transitions.

---

## 8. Proposed Execution Order (Phased Rollout)

1. **PHASE 1: Setup & Build Pipeline** - **[COMPLETED]**
   - Initialized `frontend/` with Vite 5 + React 18 (`18.3.1`) + TypeScript 5 + React Router 6 + TanStack Query 5 + `react-helmet-async` + `lucide-react`.
   - Extracted CSS Variables / Design Tokens matching `static/css/theme.css` and single font `Inter`.
   - Set up Vite proxy to Flask (port 5000) for `/api`, `/media`, `/static`, `/admin`.
   - Set up production bundle serving with SPA fallback, immutable caching for `/assets/*`, and `no-cache` for `index.html` via `spa_serving.py`.
   - Setup `react-helmet-async`, ESLint (flat config), Prettier.
   - Verified with unit tests (`tests/test_spa_serving.py`), 100% pass rate across all 55 tests.
   - Documented cPanel / Passenger build and deployment steps in `README.md`.
2. **PHASE 2: Flask API Layer (`/api/v1`)**
   - Create Flask API blueprint `api_v1`.
   - Implement CSRF endpoint, auth endpoints, catalogue endpoints, checkout endpoint, memberships, events, gallery, and contact endpoints.
   - Standardize JSON error responses: `{ ok: false, error: { code, message, fields } }`.
   - Add unit and integration tests (`tests/test_api_v1.py`) with 100% pass rate.
3. **PHASE 3: React App Shell & Design System**
   - Build App Layout: Header with frozen structure, desktop dropdowns, active states, mobile drawer, Footer.
   - Build Design System components: Button, Card, BookCard, Modal, Field, Select, Tabs, Pagination, Toast, Skeleton, Icon (inline SVG).
   - Auth Context & Route Guards.
4. **PHASE 4: Page Implementations (In User-Specified Order)**
   - 4.1 Home (`/`)
   - 4.2 About (`/about`)
   - 4.3 Visit Us (`/visit-us`)
   - 4.4 Contact (`/contact`)
   - 4.5 Library Catalogue (`/library` with filters, URL sync, Excel/PDF download, cart drawer/modal, wishlist)
   - 4.6 Book Detail (`/library/:bookId`)
   - 4.7 Membership Plans (`/membership` with subscription modal + Razorpay)
   - 4.8 How to Borrow (`/how-to-borrow`)
   - 4.9 Community (`/community`)
   - 4.10 Media Hub & Publications (`/media`, `/newspaper`, `/magazine`, `/podcasts`)
   - 4.11 Events & Contests (`/events`, calendar, event detail)
   - 4.12 Gallery & Categories (`/gallery`, `/gallery/:slug` with lightbox)
   - 4.13 Collaborators (`/collaborators`)
   - 4.14 Login, Signup, Password Reset (`/login`, `/signup`, `/forgot-password`, `/reset-password/:token`)
   - 4.15 Member Dashboard (`/dashboard`, `/dashboard/loans`, `/dashboard/profile`)
5. **PHASE 5: Admin Panel Isolation & Route Verification**
   - Verify `/admin/*` routes are untouched and cleanly served by Flask.
6. **PHASE 6: Cutover, E2E Testing & Cleanup**
   - Feature flag `USE_REACT=1` in Flask.
   - Add Vitest + React Testing Library tests for key components (Cart, Checkout modal, Filters).
   - Run Playwright E2E tests for the full user flow (browse, filter, cart add, checkout, login, membership, events).
   - Run Lighthouse audits (performance, accessibility, SEO).
   - Update README and deployment documentation.

---

## 9. Risk & Mitigation Matrix

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **SEO Degradation for Catalogue & Events** | High | Use `react-helmet-async` for all meta tags; retain Flask `/sitemap.xml` and `/robots.txt`; implement SSG/prerendering for public paths so spiders see full HTML. |
| **Session Cookie Incompatibility in Dev** | Medium | Configure Vite dev proxy to pass through `Cookie` and `Set-Cookie` headers directly to `localhost:5000` without changing cookie domains. |
| **CSRF Rejections on Fetch Calls** | High | Implement centralized `apiClient` in React that automatically fetches and injects `X-CSRFToken` from `/api/v1/csrf` on mutating requests. |
| **Admin Route Capture by SPA Fallback** | Critical | Flask SPA catch-all explicitly checks `if request.path.startswith(('/admin/', '/api/', '/static/', '/media/'))` and returns 404 or delegates to admin blueprint. |
| **Client-Side Cart Desynchronization** | Medium | Reuse the proven `localStorage` key `bb_cart` schema so user carts survive page navigations and browser restarts; validate stock & plan limit strictly on server submit. |
| **Deployment / cPanel Passenger Failure** | High | Keep `passenger_wsgi.py` pointing to Flask `app`; Flask serves compiled assets from `frontend/dist`. Deployment docs include one-line build command: `npm run build`. |

---

*Phase 0 complete. Awaiting user approval to proceed to Phase 1 (Setup).*
