"""
Validators Module for Ethiosadat Furniture

This module provides validation functions for:
- Phone numbers (Ethiopian format)
- Email addresses
- Prices and numeric values
- Input sanitization
- Ethiopian tax ID (TIN)
- Ethiopian postal codes
"""

import re
import html
from datetime import datetime


# ==================== PHONE VALIDATION ====================

def validate_phone(phone):
    """
    Validate Ethiopian phone number.
    
    Supports formats:
    - 09xxxxxxxx (Ethio Telecom)
    - 07xxxxxxxx (Ethio Telecom)
    - 2519xxxxxxxx (International format without +)
    
    Args:
        phone (str): Phone number to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone:
        return False
    
    # Remove any spaces, dashes, or parentheses
    cleaned = re.sub(r'[\s\-\(\)\+]', '', str(phone))
    
    # Ethiopian phone number patterns
    patterns = [
        r'^(09)[0-9]{8}$',      # 09xxxxxxxx
        r'^(07)[0-9]{8}$',      # 07xxxxxxxx
        r'^(2519)[0-9]{8}$',    # 2519xxxxxxxx
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True
    
    return False


def format_phone(phone):
    """
    Format Ethiopian phone number to standard format.
    
    Args:
        phone (str): Phone number to format
    
    Returns:
        str: Formatted phone number (e.g., 0912345678)
    """
    if not phone:
        return ''
    
    # Remove all non-digit characters
    cleaned = re.sub(r'[^0-9]', '', str(phone))
    
    # Handle international format
    if cleaned.startswith('251') and len(cleaned) == 12:
        cleaned = '0' + cleaned[3:]
    
    # Ensure proper length
    if len(cleaned) == 10 and cleaned.startswith(('09', '07')):
        return cleaned
    
    return phone


def get_phone_digits(phone):
    """
    Extract only digits from phone number.
    
    Args:
        phone (str): Phone number
    
    Returns:
        str: Only digits
    """
    if not phone:
        return ''
    return re.sub(r'[^0-9]', '', str(phone))


# ==================== EMAIL VALIDATION ====================

def validate_email(email):
    """
    Validate email address.
    
    Args:
        email (str): Email address to validate
    
    Returns:
        bool: True if valid, False otherwise (None returns False)
    """
    if not email:
        return False
    
    # RFC 5322 compliant email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_email_optional(email):
    """
    Validate email address (optional field).
    
    Args:
        email (str): Email address to validate
    
    Returns:
        bool: True if valid or empty, False otherwise
    """
    if not email:
        return True  # Optional field
    return validate_email(email)


def get_email_domain(email):
    """
    Extract domain from email address.
    
    Args:
        email (str): Email address
    
    Returns:
        str: Domain name, or empty string if invalid
    """
    if not email or not validate_email(email):
        return ''
    
    return email.split('@')[-1].lower()


# ==================== PRICE AND NUMBER VALIDATION ====================

def validate_price(price):
    """
    Validate price is a positive number.
    
    Args:
        price (str or int or float): Price to validate
    
    Returns:
        bool: True if positive number, False otherwise
    """
    if price is None or price == '':
        return False
    
    try:
        return float(price) > 0
    except (ValueError, TypeError):
        return False


def validate_quantity(quantity):
    """
    Validate quantity is a positive integer.
    
    Args:
        quantity (str or int): Quantity to validate
    
    Returns:
        bool: True if positive integer, False otherwise
    """
    if quantity is None or quantity == '':
        return False
    
    try:
        qty = int(quantity)
        return qty > 0
    except (ValueError, TypeError):
        return False


def validate_discount(discount):
    """
    Validate discount percentage (0-100).
    
    Args:
        discount (str or int or float): Discount percentage
    
    Returns:
        bool: True if between 0 and 100, False otherwise
    """
    if discount is None or discount == '':
        return True
    
    try:
        disc = float(discount)
        return 0 <= disc <= 100
    except (ValueError, TypeError):
        return False


def validate_year(year):
    """
    Validate year (reasonable range).
    
    Args:
        year (str or int): Year to validate
    
    Returns:
        bool: True if between 1900 and current year + 10
    """
    try:
        year_int = int(year)
        current_year = datetime.now().year
        return 1900 <= year_int <= current_year + 10
    except (ValueError, TypeError):
        return False


# ==================== TEXT VALIDATION ====================

def validate_name(name):
    """
    Validate person name (minimum 2 characters, no special chars).
    
    Args:
        name (str): Name to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not name:
        return False
    
    name = name.strip()
    if len(name) < 2:
        return False
    
    # Allow letters, spaces, hyphens, and apostrophes
    pattern = r'^[a-zA-Zአ-ፐ\s\-\.\']+$'
    return bool(re.match(pattern, name))


def validate_address(address):
    """
    Validate address (minimum 5 characters).
    
    Args:
        address (str): Address to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not address:
        return True  # Address may be optional
    
    return len(address.strip()) >= 5


def validate_postal_code(code):
    """
    Validate Ethiopian postal code format.
    
    Args:
        code (str): Postal code
    
    Returns:
        bool: True if valid format
    """
    if not code:
        return True
    
    # Ethiopian postal codes are typically 4 digits
    pattern = r'^[0-9]{4}$'
    return bool(re.match(pattern, str(code)))


def validate_tin(tin):
    """
    Validate Ethiopian Tax Identification Number (TIN).
    
    Args:
        tin (str): TIN number
    
    Returns:
        bool: True if valid format
    """
    if not tin:
        return True
    
    # TIN is typically 10 digits
    pattern = r'^[0-9]{10}$'
    return bool(re.match(pattern, str(tin)))


# ==================== STRING SANITIZATION ====================

def sanitize_input(text):
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        text (str): Input text to sanitize
    
    Returns:
        str: Sanitized text
    """
    if not text:
        return ''
    
    return html.escape(str(text))


def sanitize_html(text, allow_tags=None):
    """
    Sanitize HTML content (allow basic formatting).
    
    Args:
        text (str): HTML content
        allow_tags (list): List of allowed HTML tags
    
    Returns:
        str: Sanitized HTML
    """
    if not text:
        return ''
    
    allowed = allow_tags or []
    
    # Simple sanitization - can be extended with bleach library
    text = html.escape(text)
    
    # Restore allowed tags if any
    for tag in allowed:
        text = text.replace(f'&lt;{tag}&gt;', f'<{tag}>')
        text = text.replace(f'&lt;/{tag}&gt;', f'</{tag}>')
    
    return text


def truncate_text(text, max_length=100, suffix='...'):
    """
    Truncate text to maximum length.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        suffix (str): Suffix to add when truncated
    
    Returns:
        str: Truncated text
    """
    if not text:
        return ''
    
    text = str(text)
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)].rstrip() + suffix


# ==================== URL VALIDATION ====================

def validate_url(url):
    """
    Validate URL format.
    
    Args:
        url (str): URL to validate
    
    Returns:
        bool: True if valid URL format
    """
    if not url:
        return True
    
    pattern = r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$'
    return bool(re.match(pattern, url.strip()))


def validate_image_url(url):
    """
    Validate image URL (checks for image extensions).
    
    Args:
        url (str): Image URL
    
    Returns:
        bool: True if appears to be an image URL
    """
    if not url:
        return True
    
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')
    return url.lower().endswith(image_extensions)


# ==================== DATE VALIDATION ====================

def validate_date(date_str, format='%Y-%m-%d'):
    """
    Validate date string against format.
    
    Args:
        date_str (str): Date string
        format (str): Expected date format
    
    Returns:
        bool: True if valid date
    """
    if not date_str:
        return True
    
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def validate_future_date(date_str, format='%Y-%m-%d'):
    """
    Validate that date is in the future.
    
    Args:
        date_str (str): Date string
        format (str): Date format
    
    Returns:
        bool: True if date is in the future
    """
    if not date_str:
        return True
    
    try:
        date_obj = datetime.strptime(date_str, format)
        return date_obj > datetime.now()
    except ValueError:
        return False


# ==================== COMPOSITE VALIDATION ====================

def validate_order_form(data):
    """
    Validate complete order form data.
    
    Args:
        data (dict): Form data with keys:
            - customer_name
            - customer_phone
            - customer_address (optional)
            - customer_email (optional)
    
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = {}
    
    # Validate name
    if not validate_name(data.get('customer_name', '')):
        errors['customer_name'] = 'Please enter a valid name (minimum 2 characters)'
    
    # Validate phone
    if not validate_phone(data.get('customer_phone', '')):
        errors['customer_phone'] = 'Please enter a valid Ethiopian phone number'
    
    # Validate email if provided
    email = data.get('customer_email', '')
    if email and not validate_email(email):
        errors['customer_email'] = 'Please enter a valid email address'
    
    return len(errors) == 0, errors


def validate_product_form(data):
    """
    Validate product form data.
    
    Args:
        data (dict): Product data with price, name, etc.
    
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = {}
    
    # Validate name
    if not data.get('name_am') and not data.get('name_en'):
        errors['name'] = 'Product name is required in at least one language'
    
    # Validate price
    if not validate_price(data.get('price', '')):
        errors['price'] = 'Please enter a valid price'
    
    # Validate stock if present
    stock = data.get('stock')
    if stock is not None and stock != '':
        try:
            if int(stock) < 0:
                errors['stock'] = 'Stock cannot be negative'
        except ValueError:
            errors['stock'] = 'Please enter a valid stock quantity'
    
    return len(errors) == 0, errors