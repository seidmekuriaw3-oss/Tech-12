---
name: Security baseline
description: CSRF protection, SECRET_KEY enforcement, and hardcoded password removal decisions.
---

## CSRF protection
- `utils/csrf.py` — `generate_csrf()` stores a 32-byte hex token in session; `validate_csrf()` checks form field `csrf_token` OR `X-CSRFToken` header using `secrets.compare_digest`.
- `app.py` registers `generate_csrf` as Jinja2 global `csrf_token` and adds a `before_request` hook that validates CSRF for POST/PUT/PATCH/DELETE except `/api/` and `/static/` prefixes.
- All 22 HTML POST forms have `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
- Both `templates/base.html` and `templates/admin/layouts/admin_base.html` have a `<meta name="csrf-token">` tag and an inline fetch interceptor that auto-adds `X-CSRFToken` header to non-/api/ AJAX POSTs.

**Why:** Cart clear and all admin AJAX calls POST to non-/api/ routes; without the fetch interceptor they'd be blocked by the before_request guard.

## SECRET_KEY and ADMIN_PASSWORD
- Both now raise `RuntimeError` at startup if not set in env vars (no silent fallback).
- `SECRET_KEY` is set as a shared env var (long hex string).
- `ADMIN_PASSWORD` env var value is controlled by the store owner via Replit secrets panel.

## Admin login
- Removed the "click to fill demo credentials" box that exposed password `1234` in plain HTML.
