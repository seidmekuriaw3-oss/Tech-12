"""
Decorators Module for SEMIRA FASHION

This module provides reusable decorators for:
- Authentication and authorization
- Rate limiting
- Caching
- Performance monitoring
- Error handling
- Input validation
"""

import functools
import time
import logging
from flask import session, flash, redirect, url_for, request, jsonify
from functools import wraps

# ==================== LOGGING SETUP ====================
logger = logging.getLogger(__name__)


# ==================== AUTHENTICATION DECORATORS ====================

def login_required(f):
    """
    Decorator to require admin login for routes.
    
    Usage:
        @app.route('/admin/dashboard')
        @login_required
        def admin_dashboard():
            return "Admin Dashboard"
    
    Returns:
        Redirect to login page if not authenticated
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            # Check if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'redirect': url_for('admin.login')
                }), 401
            
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


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
        if not session.get('user_id'):
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


def admin_required(f):
    """Alias for login_required - requires admin authentication."""
    return login_required(f)


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


# ==================== ROLE-BASED ACCESS DECORATORS ====================

def role_required(*roles):
    """
    Decorator to require specific user roles.
    
    Usage:
        @app.route('/admin/users')
        @role_required('admin', 'super_admin')
        def manage_users():
            return "User Management"
    
    Args:
        *roles: List of allowed roles
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('role', 'user')
            if user_role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(permission):
    """
    Decorator to require specific permission.
    
    Usage:
        @app.route('/admin/products/delete')
        @permission_required('delete_products')
        def delete_product():
            return "Delete Product"
    
    Args:
        permission (str): Required permission name
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_permissions = session.get('permissions', [])
            if permission not in user_permissions and not session.get('admin'):
                flash('You do not have permission for this action.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==================== RATE LIMITING DECORATORS ====================

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests=10, time_window=60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests (int): Maximum requests allowed in time window
            time_window (int): Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def is_allowed(self, key):
        """
        Check if request is allowed.
        
        Args:
            key (str): Unique identifier (e.g., IP address)
        
        Returns:
            bool: True if allowed, False otherwise
        """
        now = time.time()
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if now - t < self.time_window]
        
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        self.requests[key].append(now)
        return True


# Default rate limiter instance
default_rate_limiter = RateLimiter(max_requests=10, time_window=60)


def rate_limit(max_requests=10, time_window=60, key_func=None):
    """
    Decorator to limit request rate.
    
    Usage:
        @app.route('/api/login')
        @rate_limit(max_requests=5, time_window=60)
        def login():
            return "Login"
    
    Args:
        max_requests (int): Maximum requests allowed
        time_window (int): Time window in seconds
        key_func (callable): Function to generate rate limit key
    """
    def decorator(f):
        limiter = RateLimiter(max_requests, time_window)
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier
            if key_func:
                key = key_func()
            else:
                key = request.remote_addr
            
            if not limiter.is_allowed(key):
                logger.warning(f"Rate limit exceeded for {key}")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'error': 'Too many requests. Please try again later.'
                    }), 429
                
                flash('Too many requests. Please try again later.', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==================== CACHING DECORATORS ====================

class SimpleCache:
    """Simple in-memory cache"""
    
    def __init__(self, default_ttl=300):
        self.cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key):
        """Get value from cache."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            del self.cache[key]
        return None
    
    def set(self, key, value, ttl=None):
        """Set value in cache."""
        if ttl is None:
            ttl = self.default_ttl
        self.cache[key] = (value, time.time() + ttl)
    
    def clear(self):
        """Clear all cache."""
        self.cache.clear()


# Default cache instance
default_cache = SimpleCache(default_ttl=300)


def cached(ttl=300, key_prefix=''):
    """
    Decorator to cache function results.
    
    Usage:
        @app.route('/api/products')
        @cached(ttl=60)
        def get_products():
            return jsonify(products)
    
    Args:
        ttl (int): Time to live in seconds
        key_prefix (str): Prefix for cache key
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}{f.__name__}:{request.path}:{request.args}"
            
            # Try to get from cache
            cached_result = default_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            default_cache.set(cache_key, result, ttl)
            return result
        return decorated_function
    return decorator


def invalidate_cache(key_pattern=None):
    """
    Decorator to invalidate cache after function execution.
    
    Usage:
        @app.route('/admin/products/add')
        @invalidate_cache('get_products')
        def add_product():
            return "Product added"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)
            # Clear specific cache or all
            if key_pattern:
                # Clear keys matching pattern
                keys_to_delete = [k for k in default_cache.cache if key_pattern in k]
                for key in keys_to_delete:
                    del default_cache.cache[key]
            else:
                default_cache.clear()
            return result
        return decorated_function
    return decorator


# ==================== PERFORMANCE MONITORING DECORATORS ====================

def timing_decorator(f):
    """
    Decorator to log function execution time.
    
    Usage:
        @app.route('/api/slow-operation')
        @timing_decorator
        def slow_operation():
            return "Done"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        
        logger.info(f"{f.__name__} took {execution_time:.2f}ms")
        
        # Add header for debugging
        if hasattr(result, 'headers'):
            result.headers['X-Execution-Time'] = f"{execution_time:.2f}ms"
        
        return result
    return decorated_function


# ==================== ERROR HANDLING DECORATORS ====================

def handle_errors(f):
    """
    Decorator to handle exceptions gracefully.
    
    Usage:
        @app.route('/api/data')
        @handle_errors
        def get_data():
            # May raise exception
            return data
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': 'An internal error occurred'
                }), 500
            
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('index'))
    return decorated_function


def require_https(f):
    """
    Decorator to enforce HTTPS.
    
    Usage:
        @app.route('/checkout')
        @require_https
        def checkout():
            return "Checkout"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and not app.debug:
            return redirect(request.url.replace('http://', 'https://'), code=301)
        return f(*args, **kwargs)
    return decorated_function


# ==================== INPUT VALIDATION DECORATORS ====================

def validate_json(schema=None):
    """
    Decorator to validate JSON request body.
    
    Usage:
        @app.route('/api/product', methods=['POST'])
        @validate_json(schema={'name': str, 'price': (int, float)})
        def create_product():
            data = request.validated_json
            return "Product created"
    
    Args:
        schema (dict): Expected field types
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            
            if schema:
                for field, expected_type in schema.items():
                    if field not in data:
                        return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
                    
                    if not isinstance(data[field], expected_type):
                        return jsonify({'success': False, 'error': f'Field {field} must be of type {expected_type}'}), 400
            
            request.validated_json = data
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==================== MAINTENANCE MODE DECORATOR ====================

def maintenance_mode(allow_ips=None):
    """
    Decorator to enable maintenance mode.
    
    Usage:
        @app.route('/')
        @maintenance_mode(allow_ips=['127.0.0.1'])
        def index():
            return "Home"
    
    Args:
        allow_ips (list): List of IPs allowed to bypass maintenance mode
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            maintenance_enabled = session.get('maintenance_mode', False)
            
            if maintenance_enabled:
                if allow_ips and request.remote_addr in allow_ips:
                    return f(*args, **kwargs)
                
                return render_template('maintenance.html'), 503
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator