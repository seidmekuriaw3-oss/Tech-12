"""
Lightweight CSRF protection for Semira Fashion.
Token is stored in the Flask session and validated on every state-changing request.
"""
import secrets
from flask import session, request, abort


def generate_csrf():
    """Return the CSRF token for the current session (creates one if absent)."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf():
    """Abort 403 when the submitted CSRF token does not match the session token."""
    token = session.get('_csrf_token')
    submitted = (
        request.form.get('csrf_token')
        or request.headers.get('X-CSRFToken')
        or request.headers.get('X-CSRF-Token')
    )
    if not token or not submitted:
        abort(403, description="CSRF token missing")
    if not secrets.compare_digest(str(token), str(submitted)):
        abort(403, description="CSRF token invalid")
