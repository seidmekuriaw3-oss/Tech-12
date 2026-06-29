"""
Pytest Configuration and Fixtures for Ethiosadat Furniture

This module contains all pytest fixtures and configuration for running tests.
"""

import sys
import os
import pytest
import tempfile
from flask import session

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app
from database.db import init_db, get_db, close_db
from config import Config


# ==================== TEST CONFIGURATION ====================

class TestConfig(Config):
    """Test configuration with in-memory database"""
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    DATABASE_PATH = ':memory:'  # Use in-memory database for tests
    WTF_CSRF_ENABLED = False
    DEBUG = False
    ADMIN_PASSWORD = 'test1234'


# ==================== FIXTURES ====================

@pytest.fixture(scope='session')
def app():
    """Create test Flask application instance."""
    # Override configuration
    flask_app.config.from_object(TestConfig)
    
    # Set additional test config
    flask_app.config.update({
        'TESTING': True,
        'SERVER_NAME': 'localhost.test'
    })
    
    with flask_app.app_context():
        # Initialize database for testing
        init_db()
        yield flask_app
        
        # Clean up after tests
        # Note: in-memory database will be destroyed automatically


@pytest.fixture(scope='function')
def client(app):
    """Create test client for making requests."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create test CLI runner for command testing."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db(app):
    """Get database connection for direct database testing."""
    with app.app_context():
        db = get_db()
        yield db
        # No need to close, Flask will handle it


@pytest.fixture
def auth(client):
    """Authentication helper for admin routes."""
    os.environ.setdefault('ADMIN_USERNAME', 'admin')
    os.environ.setdefault('ADMIN_PASSWORD', 'test1234')

    class AuthActions:
        def csrf_token(self):
            """Return a CSRF token for the current test session."""
            with client.session_transaction() as sess:
                token = sess.get('_csrf_token')
                if not token:
                    token = 'test-csrf-token'
                    sess['_csrf_token'] = token
                return token

        def login(self, password='test1234'):
            """Login as admin."""
            return client.post('/admin/login', data={
                'username': 'admin',
                'password': password,
                'csrf_token': self.csrf_token(),
            }, follow_redirects=True)
        
        def logout(self):
            """Logout admin."""
            return client.get('/admin/logout', follow_redirects=True)
        
        def is_logged_in(self):
            """Check if admin is logged in."""
            with client.session_transaction() as sess:
                return sess.get('admin', False)
    
    return AuthActions()


@pytest.fixture
def user_auth(client):
    """Authentication helper for user routes."""
    class UserAuthActions:
        def register(self, email='test@example.com', password='test123', name='Test User'):
            """Register a new user."""
            return client.post('/register', data={
                'full_name': name,
                'email': email,
                'password': password,
                'confirm_password': password
            }, follow_redirects=True)
        
        def login(self, email='test@example.com', password='test123'):
            """Login as user."""
            return client.post('/login/user', data={
                'email': email,
                'password': password
            }, follow_redirects=True)
        
        def logout(self):
            """Logout user."""
            return client.get('/logout/user', follow_redirects=True)
        
        def is_logged_in(self):
            """Check if user is logged in."""
            with client.session_transaction() as sess:
                return sess.get('user_id') is not None
    
    return UserAuthActions()


@pytest.fixture
def sample_product():
    """Sample product data for testing."""
    return {
        'name_am': 'ሙከራ ምርት',
        'name_en': 'Test Product',
        'price': '10000',
        'old_price': '15000',
        'category': 'ሶፋ',
        'description': 'Test description for the sample product',
        'stock': '10',
        'is_featured': '1'
    }


@pytest.fixture
def sample_product_db(app, sample_product):
    """Create a sample product in the database and return its ID."""
    from database.models import Product
    
    with app.app_context():
        product_id = Product.create(sample_product)
        return product_id


@pytest.fixture
def sample_ad():
    """Sample advertisement data for testing."""
    return {
        'text': 'Test Advertisement - Special Offer!',
        'title': 'Test Ad',
        'media': '',
        'link': '/category/all',
        'sort_order': 0
    }


@pytest.fixture
def sample_order():
    """Sample order data for testing."""
    return {
        'order_number': 'TEST-20241225-ABCD',
        'customer_name': 'Test Customer',
        'customer_phone': '0912345678',
        'customer_address': 'ወሎ ደሴ ኩታበር, Ethiopia',
        'customer_email': 'test@example.com',
        'items': '[{"name": "Test Product", "price": 10000, "quantity": 1, "total": 10000}]',
        'subtotal': 10000,
        'shipping_cost': 0,
        'total': 10000,
        'status': 'pending',
        'notes': 'Test order notes'
    }


@pytest.fixture
def empty_cart(client):
    """Ensure cart is empty before test."""
    with client.session_transaction() as sess:
        sess['cart'] = []
    return client


@pytest.fixture
def populated_cart(client, sample_product_db):
    """Create a cart with one item."""
    with client.session_transaction() as sess:
        sess['cart'] = [{
            'id': str(sample_product_db),
            'name': 'Test Product',
            'price': 10000,
            'quantity': 2,
            'image': ''
        }]
    return client


# ==================== HELPER FUNCTIONS ====================

def create_test_product(client, product_data=None):
    """Helper to create a product via API."""
    if product_data is None:
        product_data = {
            'name_am': 'API Test Product',
            'name_en': 'API Test Product',
            'price': 5000,
            'category': 'ሶፋ'
        }
    return client.post('/api/products', json=product_data)


def create_test_order(client, order_data=None):
    """Helper to create an order via API."""
    if order_data is None:
        order_data = {
            'customer_name': 'API Test Customer',
            'customer_phone': '0912345678',
            'items': [{'name': 'Test', 'price': 1000, 'quantity': 1}],
            'total': 1000
        }
    return client.post('/api/submit-order', json=order_data)


# ==================== CLEANUP ====================

@pytest.fixture(autouse=True)
def cleanup(request):
    """Clean up after each test."""
    def remove_test_data():
        # Clean up any test-specific data if needed
        pass
    
    request.addfinalizer(remove_test_data)


# ==================== MARKERS ====================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "db: marks tests that require database"
    )


# ==================== COLLECTION HOOKS ====================

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on path."""
    for item in items:
        if "test_api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        if "test_models" in str(item.fspath):
            item.add_marker(pytest.mark.db)
        if "slow" in item.name:
            item.add_marker(pytest.mark.slow)