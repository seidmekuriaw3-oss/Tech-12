"""
Tests Package for Ethiosadat Furniture

This package contains all test modules for the Ethiosadat Furniture application.
Tests include API testing, model testing, route testing, and service testing.

To run all tests:
    pytest

To run specific test file:
    pytest tests/test_models.py

To run with coverage:
    pytest --cov=app tests/
"""

# ==================== TEST CONFIGURATION ====================

# Test environment variables
import os

# Set test environment
os.environ['TESTING'] = 'True'
os.environ['DEBUG'] = 'False'

# ==================== PACKAGE EXPORTS ====================

# Import key fixtures and helpers for easier access
from tests.conftest import app, client, auth, sample_product

# ==================== PACKAGE METADATA ====================

__version__ = '1.0.0'
__all__ = [
    'app',
    'client', 
    'auth',
    'sample_product'
]

# ==================== INITIALIZATION LOG ====================

print("✅ Tests package initialized")
print(f"   - Test files: test_api.py, test_models.py, test_routes.py, test_services.py")
print(f"   - Run with: pytest")
print(f"   - Coverage: pytest --cov=app tests/")
