# Public access and media update

Public: Home, About, catalogue, book details, event listings and booking forms, media listings and previews, gallery, contact and contribution forms, membership plans.

Sign-in required: book requests, personal dashboard, borrowing history/profile and other personal account actions. Administration remains staff-only. Contact enquiries and event registrations can be submitted as a guest; existing CSRF validation remains enabled.

Media: Admin > Media > Newspaper / Magazine / Podcasts > Edit. Set **Paid membership required** to No for public free reading/listening, Yes for members with an active subscription and confirmed payment. Paid status is verified against Paid - Razorpay or Paid - confirmed by staff, together with subscription start/end dates. A login alone does not unlock paid media. This uses the existing membership payment workflow, not separate per-edition purchases.

Visitors can filter media by Free access or Paid membership. Paid previews do not embed the file or audio player. Uploaded file URLs also enforce access, including querystring and canonical-path aliases. Previously category-restricted media is migrated as paid; other existing media defaults to free. Review the new field for your existing publications after deployment.

For paid material, upload files through the application. A third-party public hosting URL is still publicly accessible on that third-party service; this application cannot revoke outside access. Keep paid descriptions as previews, not the full paid text.

Menu links now use separate component classes and explicit heights/padding, removing the inherited Home-link styles that caused the tall selection and crowded text. The mobile menu remains expandable with keyboard support.

Validation: 13 tests pass, including public browsing, guest request protection, free file downloads, paid preview redaction, blocked unpaid/expired access, confirmed paid access and Free/Paid filtering. The 42-route test-client smoke check passes. Real browser visual testing remains unavailable because Chromium installation failed; live payment processing and hosting were not exercised.

Deploy: back up the database/uploads/.env, replace the application source, install requirements and restart Passenger. Keep your existing instance database and uploads. The is_paid publication column is added automatically on startup. Hard-refresh for CSS/JS v4. No test database, accounts or secrets are shipped.
