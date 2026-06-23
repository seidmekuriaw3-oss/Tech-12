"""
Authentication Middleware for SEMIRA FASHION

This module provides decorators for protecting routes that require
admin authentication or user authentication.
"""

from functools import wraps
from flask import session, flash, redirect, url_for, request, jsonify


def login_required(f):
    """
    Decorator to require admin login for routes.
    
    Usage:
        @app.route('/admin/dashboard')
        @login_required
        def admin_dashboard():
            return "Admin Dashboard"
    
    Returns:
        Redirect to login page if not authenticated, or the original function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if admin is logged in
        if not session.get('admin'):
            # Check if request expects JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'redirect': url_for('admin.admin_login')
                }), 401
            
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin.admin_login', next=request.url))
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    Alias for login_required - requires admin authentication.
    """
    return login_required(f)


def user_login_required(f):
    """
    Decorator to require user login for routes.
    
    Usage:
        @app.route('/profile')
        @user_login_required
        def user_profile():
            return "User Profile"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if not session.get('user_id'):
            # Check if request expects JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': 'User authentication required',
                    'redirect': url_for('customer.user_login')
                }), 401
            
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('customer.user_login', next=request.url))
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_or_user_required(f):
    """
    Decorator that requires either admin OR user login.
    Admin has access to user routes, but users cannot access admin routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_admin = session.get('admin', False)
        is_user = session.get('user_id') is not None
        
        if not (is_admin or is_user):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'redirect': url_for('customer.user_login')
                }), 401
            
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('customer.user_login', next=request.url))
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """
    Get the current logged in user information.
    
    Returns:
        dict: User information or None if not logged in
    """
    if session.get('admin'):
        return {
            'id': 'admin',
            'name': 'Administrator',
            'email': session.get('admin_email', 'admin@semirafashion.com'),
            'role': 'admin',
            'is_admin': True
        }
    
    if session.get('user_id'):
        return {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email'),
            'phone': session.get('user_phone'),
            'role': 'user',
            'is_admin': False
        }
    
    return None


def is_authenticated():
    """Check if user is authenticated (either admin or user)."""
    return session.get('admin', False) or session.get('user_id') is not None


def is_admin_user():
    """Check if current user is admin."""
    return session.get('admin', False)


def is_logged_in_user():
    """Check if current user is a regular logged in user."""
    return session.get('user_id') is not None


def logout_user():
    """Helper function to logout a user."""
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('user_phone', None)


def logout_admin():
    """Helper function to logout admin."""
    session.pop('admin', None)
    session.pop('admin_email', None)


def logout_all():
    """Helper function to logout both admin and user."""
    session.clear()


# ==================== SESSION HELPER FUNCTIONS ====================

def set_admin_session(email=None):
    """
    Set admin session data.
    
    Args:
        email (str, optional): Admin email address
    """
    session['admin'] = True
    if email:
        session['admin_email'] = email
    session.permanent = True


def set_user_session(user_id, user_name, user_email, user_phone=None):
    """
    Set user session data.
    
    Args:
        user_id (int): User ID
        user_name (str): User's full name
        user_email (str): User's email address
        user_phone (str, optional): User's phone number
    """
    session['user_id'] = user_id
    session['user_name'] = user_name
    session['user_email'] = user_email
    if user_phone:
        session['user_phone'] = user_phone
    session.permanent = True


def refresh_session():
    """Refresh session to prevent timeout."""
    session.modified = True


# ==================== HELPER FOR TEMPLATES ====================

def add_auth_context():
    """
    Add authentication context to templates.
    This function should be called from app context processor.
    
    Returns:
        dict: Authentication context variables
    """
    return {
        'current_user': get_current_user(),
        'is_authenticated': is_authenticated(),
        'is_admin': is_admin_user(),
        'is_logged_in_user': is_logged_in_user()
    }