# Sentinel's Journal

## 2026-02-24 - [Stored XSS in Client-Side Rendering]
**Vulnerability:** Dynamic data from API responses (item names, listing titles) was being inserted into the DOM using `innerHTML` without sanitization in `dashboard.html` and `index.html`.
**Learning:** The application uses modern Javascript template literals for client-side rendering but fails to escape HTML special characters, creating a Stored XSS vulnerability where malicious data from the database or external APIs could execute scripts in the user's browser.
**Prevention:** Always use a helper like `escapeHTML` when inserting dynamic content into `innerHTML`, or prefer `textContent` for pure text fields.
