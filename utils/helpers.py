"""
Helpers Module for Ethiosadat Furniture

This module provides utility functions for:
- Price formatting
- Text manipulation
- Cart operations
- Date formatting
- String helpers
"""

import os
import re
import uuid
import secrets
import html
from datetime import datetime
from flask import session

# ==================== PRICE FORMATTING ====================

def format_price(price):
    """
    Format price with thousand separators and currency.
    
    Args:
        price (str or int or float): Price value
    
    Returns:
        str: Formatted price string (e.g., "15,000 ETB")
    """
    try:
        price_float = float(price)
        formatted = f"{price_float:,.0f}".replace(',', ',')
        return f"{formatted} ETB"
    except (ValueError, TypeError):
        return f"{price} ETB"


def format_price_number(price):
    """
    Format price as number only (without currency).
    
    Args:
        price (str or int or float): Price value
    
    Returns:
        str: Formatted number with thousand separators
    """
    try:
        price_float = float(price)
        return f"{price_float:,.0f}".replace(',', ',')
    except (ValueError, TypeError):
        return str(price)


def calculate_discount(price, old_price):
    """
    Calculate discount percentage.
    
    Args:
        price (float): Current price
        old_price (float): Original price
    
    Returns:
        int: Discount percentage (0 if no discount)
    """
    try:
        current = float(price)
        original = float(old_price) if old_price else 0
        
        if original > 0 and current < original:
            return int(((original - current) / original) * 100)
        return 0
    except (ValueError, TypeError):
        return 0


# ==================== TEXT FORMATTING ====================

def truncate_text(text, length=50, ellipsis='...'):
    """
    Truncate text to specified length with ellipsis.
    
    Args:
        text (str): Text to truncate
        length (int): Maximum length
        ellipsis (str): Ellipsis string to append
    
    Returns:
        str: Truncated text
    """
    if not text:
        return ''
    
    if len(text) <= length:
        return text
    
    return text[:length].rstrip() + ellipsis


def slugify(text):
    """
    Convert text to URL-friendly slug.
    
    Args:
        text (str): Text to slugify
    
    Returns:
        str: URL-friendly slug
    """
    if not text:
        return ''
    
    # Convert to lowercase
    text = text.lower()
    
    # Simple Amharic to Latin transliteration
    amharic_map = {
        'አ': 'a', 'ሀ': 'a', 'ሐ': 'a', 'ሃ': 'a', 'ሓ': 'a',
        'ለ': 'le', 'ሉ': 'lu', 'ሊ': 'li', 'ላ': 'la', 'ሌ': 'le',
        'ል': 'l', 'ሎ': 'lo', 'መ': 'me', 'ሙ': 'mu', 'ሚ': 'mi',
        'ማ': 'ma', 'ሜ': 'me', 'ም': 'm', 'ሞ': 'mo', 'ሠ': 'se',
        'ሡ': 'su', 'ሢ': 'si', 'ሣ': 'sa', 'ሤ': 'se', 'ሥ': 's', 'ሦ': 'so',
        'ረ': 're', 'ሩ': 'ru', 'ሪ': 'ri', 'ራ': 'ra', 'ሬ': 're',
        'ር': 'r', 'ሮ': 'ro', 'ሰ': 'se', 'ሱ': 'su', 'ሲ': 'si',
        'ሳ': 'sa', 'ሴ': 'se', 'ስ': 's', 'ሶ': 'so', 'ሸ': 'she',
        'ሹ': 'shu', 'ሺ': 'shi', 'ሻ': 'sha', 'ሼ': 'she', 'ሽ': 'sh', 'ሾ': 'sho'
    }
    
    for am, en in amharic_map.items():
        text = text.replace(am, en)
    
    # Replace non-alphanumeric with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    
    return text if text else 'product'


# ==================== CART FUNCTIONS ====================

def get_cart_count():
    """
    Get total number of items in cart.
    Cart is stored as {product_id_str: quantity} dict in session.

    Returns:
        int: Total item count
    """
    cart = session.get('cart', {})
    if isinstance(cart, dict):
        return sum(int(qty) for qty in cart.values())
    return 0


def get_cart_subtotal():
    """
    Calculate cart subtotal.
    Cart is stored as {product_id_str: quantity} dict — price lookup not
    available here, so returns 0 (subtotal calculation requires DB).
    Use cart_routes.get_cart_total() for accurate totals.

    Returns:
        float: 0 (stub — cart dict has no price data)
    """
    return 0.0


def get_shipping_cost():
    """
    Calculate shipping cost based on subtotal.
    
    Returns:
        float: Shipping cost (0 if subtotal >= threshold)
    """
    subtotal = get_cart_subtotal()
    threshold = int(os.environ.get('FREE_SHIPPING_THRESHOLD', '5000'))
    cost = int(os.environ.get('SHIPPING_COST', '200'))
    return 0 if subtotal >= threshold else cost


def get_cart_total():
    """
    Calculate cart total including shipping.
    
    Returns:
        float: Total amount
    """
    return get_cart_subtotal() + get_shipping_cost()


def add_to_cart(product_id, name, price, quantity=1, image=''):
    """
    Add product to cart.
    Cart is stored as {product_id_str: quantity} dict in session.
    Note: name/price/image are not stored in the session dict; they are
    fetched from the DB when rendering the cart (see cart_routes).

    Args:
        product_id (str): Product identifier
        name (str): Product name (not stored — for API compat only)
        price (float): Product price (not stored — for API compat only)
        quantity (int): Quantity to add
        image (str): Product image (not stored — for API compat only)
    """
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    key = str(product_id)
    cart[key] = cart.get(key, 0) + int(quantity)
    session['cart'] = cart
    session.modified = True


def remove_from_cart(product_id):
    """
    Remove product from cart.

    Args:
        product_id (str): Product identifier
    """
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    cart.pop(str(product_id), None)
    session['cart'] = cart
    session.modified = True


def update_cart_item(product_id, quantity):
    """
    Update quantity of a cart item.

    Args:
        product_id (str): Product identifier
        quantity (int): New quantity (if < 1, removes item)
    """
    if quantity < 1:
        remove_from_cart(product_id)
        return
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    key = str(product_id)
    if key in cart:
        cart[key] = int(quantity)
        session['cart'] = cart
        session.modified = True


def clear_cart():
    """Clear all items from cart."""
    session.pop('cart', None)
    session.modified = True


def get_cart_items():
    """
    Get a minimal list of cart entries {id, quantity}.
    Price/name lookups require a DB query — use cart_routes for full data.

    Returns:
        list[dict]: Each entry has 'id' and 'quantity'.
    """
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        return []
    return [{'id': k, 'quantity': v} for k, v in cart.items()]


def cart_is_empty():
    """
    Check if cart is empty.

    Returns:
        bool: True if cart is empty
    """
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        return True
    return len(cart) == 0


# ==================== DATE FORMATTING ====================

def format_datetime(dt, format_str='%Y-%m-%d %H:%M'):
    """
    Format datetime for display.
    
    Args:
        dt (datetime): Datetime object
        format_str (str): Format string
    
    Returns:
        str: Formatted datetime string
    """
    if not dt:
        return ''
    
    return dt.strftime(format_str)


def format_date(dt, format_type='short'):
    """
    Format date for display.
    
    Args:
        dt (datetime): Date object
        format_type (str): 'short', 'long', or 'full'
    
    Returns:
        str: Formatted date string
    """
    if not dt:
        return ''
    
    if format_type == 'short':
        return dt.strftime('%d/%m/%Y')
    elif format_type == 'long':
        return dt.strftime('%B %d, %Y')
    else:
        return dt.strftime('%Y-%m-%d %H:%M:%S')


def time_ago(dt):
    """
    Get human readable time ago string.
    
    Args:
        dt (datetime): Past datetime
    
    Returns:
        str: Time ago description
    """
    if not dt:
        return ''
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


# ==================== STRING HELPERS ====================

def generate_order_number():
    """
    Generate a unique order number.
    
    Returns:
        str: Unique order number (e.g., ORD-20241225-ABCD)
    """
    date_str = datetime.now().strftime('%Y%m%d')
    random_part = secrets.token_hex(3).upper()
    return f"ORD-{date_str}-{random_part}"


def sanitize_input(text):
    """
    Sanitize user input to prevent XSS.
    
    Args:
        text (str): Input text
    
    Returns:
        str: Sanitized text
    """
    if not text:
        return ''
    
    return html.escape(str(text))


def generate_random_id(length=8):
    """
    Generate a random ID.
    
    Args:
        length (int): Length of the ID
    
    Returns:
        str: Random ID
    """
    return secrets.token_hex(length // 2)


def is_valid_email(email):
    """
    Validate email format.
    
    Args:
        email (str): Email address to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def extract_numbers(text):
    """
    Extract numbers from text.
    
    Args:
        text (str): Text containing numbers
    
    Returns:
        str: Only the numeric characters
    """
    if not text:
        return ''
    
    return ''.join(re.findall(r'\d+', text))


# ==================== TEMPLATE FILTERS ====================

def nl2br(text):
    """
    Convert newlines to HTML line breaks.
    
    Args:
        text (str): Text with newlines
    
    Returns:
        str: HTML with <br> tags
    """
    if not text:
        return ''
    
    return text.replace('\n', '<br>')


def truncate_chars(text, length=50):
    """
    Alias for truncate_text for backward compatibility.
    """
    return truncate_text(text, length)