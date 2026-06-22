"""
Translation Cache Module for Ethiosadat Furniture

This module provides cached backend translation using googletrans.
Supports Amharic (am), English (en), and Arabic (ar).
"""

import logging
from functools import lru_cache
from datetime import datetime

logger = logging.getLogger(__name__)

# Language code mappings for googletrans
LANGUAGE_CODES = {
    'am': 'am',      # Amharic
    'en': 'en',      # English
    'ar': 'ar',      # Arabic
}

# Fallback translations for critical errors and common UI elements
FALLBACK_TEXTS = {
    'am': {
        # Errors
        'error': 'ስህተት አለ',
        'loading': 'በመጫን ላይ...',
        'sorry': 'ይቅርታ',
        'try_again': 'እንደገና ይሞክሩ',
        # Common UI
        'home': 'መነሻ',
        'products': 'ምርቶች',
        'cart': 'ጋሪ',
        'account': 'አካውንት',
        'search': 'ፈልግ',
        'all': 'ሁሉም',
        'add': 'ጨምር',
        'delete': 'ሰርዝ',
        'edit': 'ቀይር',
        'save': 'ያስቀምጡ',
        'cancel': 'ይቅርታ',
        'close': 'ዝጋ',
        'submit': 'ላክ',
        'logout': 'ውጣ',
        'login': 'ገባ',
        'register': 'ተመዝገብ',
    },
    'en': {
        # Errors
        'error': 'An error occurred',
        'loading': 'Loading...',
        'sorry': 'Sorry',
        'try_again': 'Try again',
        # Common UI
        'home': 'Home',
        'products': 'Products',
        'cart': 'Cart',
        'account': 'Account',
        'search': 'Search',
        'all': 'All',
        'add': 'Add',
        'delete': 'Delete',
        'edit': 'Edit',
        'save': 'Save',
        'cancel': 'Cancel',
        'close': 'Close',
        'submit': 'Submit',
        'logout': 'Logout',
        'login': 'Login',
        'register': 'Register',
    },
    'ar': {
        # Errors
        'error': 'حدث خطأ',
        'loading': 'جاري التحميل...',
        'sorry': 'عذرا',
        'try_again': 'حاول مجددا',
        # Common UI
        'home': 'الرئيسية',
        'products': 'المنتجات',
        'cart': 'السلة',
        'account': 'الحساب',
        'search': 'بحث',
        'all': 'جميع',
        'add': 'إضافة',
        'delete': 'حذف',
        'edit': 'تعديل',
        'save': 'حفظ',
        'cancel': 'إلغاء',
        'close': 'إغلاق',
        'submit': 'تقديم',
        'logout': 'تسجيل الخروج',
        'login': 'تسجيل الدخول',
        'register': 'تسجيل',
    }
}

# Initialize googletrans translator with safe fallback
translator = None
GOOGLETRANS_AVAILABLE = False

try:
    from googletrans import Translator
    translator = Translator()
    GOOGLETRANS_AVAILABLE = True
    logger.info("googletrans initialized successfully")
except ImportError:
    logger.info("googletrans not available - using fallback translations only (safe for Python 3.14)")
except ModuleNotFoundError:
    logger.info("googletrans module not found - using fallback translations only (safe for Python 3.14)")
except Exception as e:
    logger.warning(f"Failed to initialize googletrans: {str(e)} - Using fallback translations")


@lru_cache(maxsize=2000)
def translate_text(text, target_lang='en'):
    """
    Translate text to target language with intelligent caching and fallback.
    
    Supports: Amharic (am), English (en), Arabic (ar)
    Falls back gracefully to manual translations if googletrans unavailable.
    
    Args:
        text (str): Text to translate
        target_lang (str): Target language code ('am', 'en', 'ar')
    
    Returns:
        str: Translated text or original text if translation fails
    """
    # Validate inputs
    if not text or not isinstance(text, str):
        return text
    
    text = text.strip()
    if not text:
        return text
    
    # Validate language code
    if target_lang not in LANGUAGE_CODES:
        logger.debug(f"Unsupported language code: {target_lang}. Using English.")
        target_lang = 'en'
    
    # If target is English, return original text
    if target_lang == 'en':
        return text
    
    # Check fallback translations first (faster and more reliable)
    fallback_dict = FALLBACK_TEXTS.get(target_lang, {})
    if text.lower() in fallback_dict:
        return fallback_dict[text.lower()]
    
    # Try googletrans if available
    if GOOGLETRANS_AVAILABLE and translator:
        try:
            result = translator.translate(text, src_language='en', dest_language=LANGUAGE_CODES[target_lang])
            if result:
                translated = result.get('text', text) if isinstance(result, dict) else getattr(result, 'text', text)
                if translated and translated != text:
                    logger.debug(f"Translated to {target_lang}: {text[:40]}... -> {translated[:40]}...")
                    return translated
        except Exception as e:
            logger.debug(f"Translation failed for '{text[:40]}...': {str(e)}")
    
    # Return original text as final fallback
    return text


def get_text(key, lang='en', default=None):
    """
    Get text from fallback translations.
    
    Args:
        key (str): Text key to look up
        lang (str): Target language ('am', 'en', 'ar')
        default: Default text if key not found
    
    Returns:
        str: Translated text or default
    """
    fallback = FALLBACK_TEXTS.get(lang, FALLBACK_TEXTS['en'])
    return fallback.get(key.lower(), default or key)


def batch_translate(texts, target_lang='en'):
    """
    Translate multiple texts at once.
    
    Args:
        texts (list): List of strings to translate
        target_lang (str): Target language code
    
    Returns:
        dict: Dictionary mapping original text to translated text
    """
    translations = {}
    for text in texts:
        if text:
            translations[text] = translate_text(text, target_lang)
    return translations


def get_fallback_text(key, lang='en'):
    """
    Get fallback text for critical UI elements.
    
    Args:
        key (str): Text key
        lang (str): Language code
    
    Returns:
        str: Fallback text or key itself
    """
    return FALLBACK_TEXTS.get(lang, {}).get(key, key)


def clear_translation_cache():
    """Clear the translation cache."""
    translate_text.cache_clear()
    logger.info("Translation cache cleared")


def get_translation_stats():
    """Get statistics about the translation cache."""
    cache_info = translate_text.cache_info()
    return {
        'hits': cache_info.hits,
        'misses': cache_info.misses,
        'maxsize': cache_info.maxsize,
        'currsize': cache_info.currsize,
        'hit_rate': cache_info.hits / (cache_info.hits + cache_info.misses) if (cache_info.hits + cache_info.misses) > 0 else 0
    }
