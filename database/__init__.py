"""
Database Package for SEMIRA FASHION

This package provides database connection management and ORM models
for users, products, advertisements, orders, and branches.
"""

# ==================== DATABASE CONNECTION ====================
from database.db import get_db, init_db, commit_or_rollback

# ==================== DATABASE MODELS ====================
from database.models import (
    User,
    Category,
    Product,
    CartItem,
    Order,
    OrderItem,
    Advertisement,
    Branch,
    Notification
)

# ==================== PACKAGE METADATA ====================
__version__ = '1.0.0'
__all__ = [
    # Database functions
    'get_db',
    'init_db',
    'commit_or_rollback',
    # Models
    'User',
    'Category',
    'Product',
    'CartItem',
    'Order',
    'OrderItem',
    'Advertisement',
    'Branch',
    'Notification'
]

# ==================== INITIALIZATION LOG ====================
print("[OK] Database package initialized successfully")
print(f"   - init_db: Database initializer")
print(f"   - get_db: Database session manager")
print(f"   - commit_or_rollback: Transaction handler")
print(f"   - Models: User, Category, Product, CartItem, Order, OrderItem, Advertisement, Branch, Notification")