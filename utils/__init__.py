"""
Utils Package for Ethiosadat Furniture

This package provides utility functions for:
- Price formatting
- Text manipulation
- File handling
- Data validation
- Date formatting
- Cart operations
"""

# ==================== HELPER FUNCTIONS ====================
from utils.helpers import (
    # Price formatting
    format_price,
    format_price_number,
    calculate_discount,
    # Text formatting
    truncate_text,
    slugify,
    # Cart functions
    get_cart_count,
    get_cart_subtotal,
    get_cart_total,
    add_to_cart,
    remove_from_cart,
    clear_cart,
    # Date functions
    format_datetime,
    time_ago,
    # String helpers
    generate_order_number,
    sanitize_input
)

# ==================== VALIDATORS ====================
from utils.validators import (
    validate_phone,
    validate_email,
    validate_price,
    sanitize_input as validate_sanitize
)

# ==================== FILE HANDLERS ====================
from utils.file_handler import (
    allowed_file,
    save_file,
    delete_file
)

# ==================== PACKAGE METADATA ====================
__version__ = '1.0.0'

__all__ = [
    # Price formatting
    'format_price',
    'format_price_number',
    'calculate_discount',
    # Text formatting
    'truncate_text',
    'slugify',
    # Cart functions
    'get_cart_count',
    'get_cart_subtotal',
    'get_cart_total',
    'add_to_cart',
    'remove_from_cart',
    'clear_cart',
    # Date functions
    'format_datetime',
    'time_ago',
    # String helpers
    'generate_order_number',
    'sanitize_input',
    # Validators
    'validate_phone',
    'validate_email',
    'validate_price',
    # File handlers
    'allowed_file',
    'save_file',
    'delete_file'
]

# ==================== INITIALIZATION LOG ====================
print("[OK] Utils package initialized successfully")
print(f"   - Price helpers loaded")
print(f"   - Cart helpers loaded")
print(f"   - Validation helpers loaded")
print(f"   - File handlers loaded")