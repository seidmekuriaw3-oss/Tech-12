"""
Shared constants and helpers for all SEMIRA FASHION route modules.

Single source of truth — import from here, never re-declare in individual route files.
"""

import os
from flask import session

# ==================== LANGUAGE ====================

SUPPORTED_LANGUAGES = ['am', 'en', 'ar']
DEFAULT_LANGUAGE = 'am'


def get_lang():
    """Return the active language for the current request, defaulting to Amharic."""
    lang = session.get('lang', DEFAULT_LANGUAGE)
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


# ==================== CONTACT / WHATSAPP ====================

WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '251987957957')

# Branch / store contact numbers (comma-separated env var, e.g. "251906080606,251906090606")
_branch_phones_env = os.environ.get('BRANCH_PHONE_NUMBERS', '')
BRANCH_PHONE_NUMBERS: list[str] = [p.strip() for p in _branch_phones_env.split(',') if p.strip()]

# ==================== SHIPPING & PRICING ====================

FREE_SHIPPING_THRESHOLD = int(os.environ.get('FREE_SHIPPING_THRESHOLD', '5000'))
SHIPPING_COST = int(os.environ.get('SHIPPING_COST', '200'))
USER_DISCOUNT_RATE = 0.10          # 10 % discount for logged-in users


def calc_cart_totals(subtotal, is_logged_in: bool) -> dict:
    """
    Compute discount, shipping and grand total from a cart subtotal.

    Returns a dict with keys:
        subtotal, discount, subtotal_after_discount,
        shipping_cost, total, free_shipping, free_shipping_threshold
    """
    subtotal = float(subtotal or 0)
    discount = round(subtotal * USER_DISCOUNT_RATE, 2) if is_logged_in else 0.0
    subtotal_after_discount = round(subtotal - discount, 2)
    free_shipping = subtotal_after_discount >= FREE_SHIPPING_THRESHOLD
    shipping = 0 if free_shipping else SHIPPING_COST
    total = round(subtotal_after_discount + shipping, 2)
    return {
        'subtotal': round(subtotal, 2),
        'discount': discount,
        'subtotal_after_discount': subtotal_after_discount,
        'shipping_cost': shipping,
        'total': total,
        'free_shipping': free_shipping,
        'free_shipping_threshold': FREE_SHIPPING_THRESHOLD,
    }
