"""
Translators Module for Ethiosadat Furniture

This module provides translation functionality for:
- Amharic to English translation
- English to Amharic translation
- Currency conversion
- Date localization
- Number localization
"""

import re
from datetime import datetime

# ==================== AMHARIC TO ENGLISH MAPPINGS ====================

# Basic Amharic to Latin transliteration mapping
AMHARIC_TO_LATIN = {
    # Vowels and consonants
    'አ': 'a', 'ሀ': 'a', 'ሐ': 'a', 'ሃ': 'a', 'ሓ': 'a',
    'ለ': 'le', 'ሉ': 'lu', 'ሊ': 'li', 'ላ': 'la', 'ሌ': 'le',
    'ል': 'l', 'ሎ': 'lo', 'ሏ': 'lwa',
    'መ': 'me', 'ሙ': 'mu', 'ሚ': 'mi', 'ማ': 'ma', 'ሜ': 'me',
    'ም': 'm', 'ሞ': 'mo', 'ሟ': 'mwa',
    'ሠ': 'se', 'ሡ': 'su', 'ሢ': 'si', 'ሣ': 'sa', 'ሤ': 'se',
    'ሥ': 's', 'ሦ': 'so', 'ሧ': 'swa',
    'ረ': 're', 'ሩ': 'ru', 'ሪ': 'ri', 'ራ': 'ra', 'ሬ': 're',
    'ር': 'r', 'ሮ': 'ro', 'ሯ': 'rwa',
    'ሰ': 'se', 'ሱ': 'su', 'ሲ': 'si', 'ሳ': 'sa', 'ሴ': 'se',
    'ስ': 's', 'ሶ': 'so', 'ሷ': 'swa',
    'ሸ': 'she', 'ሹ': 'shu', 'ሺ': 'shi', 'ሻ': 'sha', 'ሼ': 'she',
    'ሽ': 'sh', 'ሾ': 'sho', 'ሿ': 'shwa',
    'ቀ': 'qe', 'ቁ': 'qu', 'ቂ': 'qi', 'ቃ': 'qa', 'ቄ': 'qe',
    'ቅ': 'q', 'ቆ': 'qo', 'ቋ': 'qwa',
    'በ': 'be', 'ቡ': 'bu', 'ቢ': 'bi', 'ባ': 'ba', 'ቤ': 'be',
    'ብ': 'b', 'ቦ': 'bo', 'ቧ': 'bwa',
    'ተ': 'te', 'ቱ': 'tu', 'ቲ': 'ti', 'ታ': 'ta', 'ቴ': 'te',
    'ት': 't', 'ቶ': 'to', 'ቷ': 'twa',
    'ቸ': 'che', 'ቹ': 'chu', 'ቺ': 'chi', 'ቻ': 'cha', 'ቼ': 'che',
    'ች': 'ch', 'ቾ': 'cho', 'ቿ': 'chwa',
    'ሃ': 'ha', 'ሁ': 'hu', 'ሂ': 'hi', 'ሄ': 'he',
    'ህ': 'h', 'ሆ': 'ho', 'ሏ': 'hwa',
    'ነ': 'ne', 'ኑ': 'nu', 'ኒ': 'ni', 'ና': 'na', 'ኔ': 'ne',
    'ን': 'n', 'ኖ': 'no', 'ኗ': 'nwa',
    'ኘ': 'nye', 'ኙ': 'nyu', 'ኚ': 'nyi', 'ኛ': 'nya', 'ኜ': 'nye',
    'ኝ': 'ny', 'ኞ': 'nyo', 'ኟ': 'nywa',
    'አ': 'a', 'ኡ': 'u', 'ኢ': 'i', 'ኣ': 'a', 'ኤ': 'e',
    'እ': 'e', 'ኦ': 'o', 'ኧ': 'a',
    'ከ': 'ke', 'ኩ': 'ku', 'ኪ': 'ki', 'ካ': 'ka', 'ኬ': 'ke',
    'ክ': 'k', 'ኮ': 'ko', 'ኳ': 'kwa',
    'ወ': 'we', 'ዉ': 'wu', 'ዊ': 'wi', 'ዋ': 'wa', 'ዌ': 'we',
    'ው': 'w', 'ዎ': 'wo',
    'ዐ': 'a', 'ዑ': 'u', 'ዒ': 'i', 'ዓ': 'a', 'ዔ': 'e',
    'ዕ': 'e', 'ዖ': 'o',
    'ዘ': 'ze', 'ዙ': 'zu', 'ዚ': 'zi', 'ዛ': 'za', 'ዜ': 'ze',
    'ዝ': 'z', 'ዞ': 'zo', 'ዟ': 'zwa',
    'ዠ': 'zhe', 'ዡ': 'zhu', 'ዢ': 'zhi', 'ዣ': 'zha', 'ዤ': 'zhe',
    'ዥ': 'zh', 'ዦ': 'zho', 'ዧ': 'zhwa',
    'የ': 'ye', 'ዩ': 'yu', 'ዪ': 'yi', 'ያ': 'ya', 'ዬ': 'ye',
    'ይ': 'y', 'ዮ': 'yo',
    'ደ': 'de', 'ዱ': 'du', 'ዲ': 'di', 'ዳ': 'da', 'ዴ': 'de',
    'ድ': 'd', 'ዶ': 'do', 'ዷ': 'dwa',
    'ጀ': 'je', 'ጁ': 'ju', 'ጂ': 'ji', 'ጃ': 'ja', 'ጄ': 'je',
    'ጅ': 'j', 'ጆ': 'jo', 'ጇ': 'jwa',
    'ገ': 'ge', 'ጉ': 'gu', 'ጊ': 'gi', 'ጋ': 'ga', 'ጌ': 'ge',
    'ግ': 'g', 'ጎ': 'go', 'ጓ': 'gwa',
    'ጠ': 'te', 'ጡ': 'tu', 'ጢ': 'ti', 'ጣ': 'ta', 'ጤ': 'te',
    'ጥ': 't', 'ጦ': 'to', 'ጧ': 'twa',
    'ጨ': 'che', 'ጩ': 'chu', 'ጪ': 'chi', 'ጫ': 'cha', 'ጬ': 'che',
    'ጭ': 'ch', 'ጮ': 'cho', 'ጯ': 'chwa',
    'ጰ': 'pe', 'ጱ': 'pu', 'ጲ': 'pi', 'ጳ': 'pa', 'ጴ': 'pe',
    'ጵ': 'p', 'ጶ': 'po', 'ጷ': 'pwa',
    'ጸ': 'tse', 'ጹ': 'tsu', 'ጺ': 'tsi', 'ጻ': 'tsa', 'ጼ': 'tse',
    'ጽ': 'ts', 'ጾ': 'tso', 'ጿ': 'tswa',
    'ፀ': 'tse', 'ፁ': 'tsu', 'ፂ': 'tsi', 'ፃ': 'tsa', 'ፄ': 'tse',
    'ፅ': 'ts', 'ፆ': 'tso',
    'ፈ': 'fe', 'ፉ': 'fu', 'ፊ': 'fi', 'ፋ': 'fa', 'ፌ': 'fe',
    'ፍ': 'f', 'ፎ': 'fo', 'ፏ': 'fwa',
    'ፐ': 'pe', 'ፑ': 'pu', 'ፒ': 'pi', 'ፓ': 'pa', 'ፔ': 'pe',
    'ፕ': 'p', 'ፖ': 'po', 'ፗ': 'pwa'
}

# Common words and phrases translation
COMMON_TRANSLATIONS = {
    # Greetings
    'ሰላም': 'Hello',
    'እንደምን አለህ': 'How are you',
    'ደህና ነኝ': 'I am fine',
    'አመሰግናለሁ': 'Thank you',
    'እንኳን ደህና መጡ': 'Welcome',
    
    # Shopping
    'ምርት': 'Product',
    'ምርቶች': 'Products',
    'ዋጋ': 'Price',
    'ቅናሽ': 'Discount',
    'ጋሪ': 'Cart',
    'ትዕዛዝ': 'Order',
    'ክፍያ': 'Payment',
    'ማጓጓዝ': 'Shipping',
    'ነጻ': 'Free',
    
    # Furniture
    'ሶፋ': 'Sofa',
    'አልጋ': 'Bed',
    'መጅሊስ': 'Mejlis',
    'መጋረጃ': 'Curtain',
    'ቁምሳጥን': 'Wardrobe',
    'ወንበር': 'Chair',
    'ጠረጴዛ': 'Table',
    
    # Actions
    'ጨምር': 'Add',
    'አስወግድ': 'Remove',
    'ዘምን': 'Update',
    'ፈልግ': 'Search',
    'ግዛ': 'Buy',
    'ተመልከት': 'View',
    'አርትዕ': 'Edit',
    'ሰርዝ': 'Delete',
    
    # Status
    'በመጠባበቅ ላይ': 'Pending',
    'ተረጋግጧል': 'Confirmed',
    'ተልኳል': 'Shipped',
    'ደርሷል': 'Delivered',
    'ተሰርዟል': 'Cancelled',
    
    # Days
    'ሰኞ': 'Monday',
    'ማክሰኞ': 'Tuesday',
    'ረቡዕ': 'Wednesday',
    'ሐሙስ': 'Thursday',
    'አርብ': 'Friday',
    'ቅዳሜ': 'Saturday',
    'እሁድ': 'Sunday'
}


# ==================== MONTH TRANSLATIONS ====================

AMHARIC_MONTHS = {
    1: 'ጥር',
    2: 'የካቲት',
    3: 'መጋቢት',
    4: 'ሚያዝያ',
    5: 'ግንቦት',
    6: 'ሰኔ',
    7: 'ሐምሌ',
    8: 'ነሐሴ',
    9: 'መስከረም',
    10: 'ጥቅምት',
    11: 'ህዳር',
    12: 'ታህሳስ'
}

ENGLISH_MONTHS = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}


# ==================== TRANSLATION FUNCTIONS ====================

def translate_am_to_en(text):
    """
    Transliterate Amharic text to Latin characters (approximate).
    
    Args:
        text (str): Amharic text
    
    Returns:
        str: Latin transliteration
    """
    if not text:
        return ''
    
    result = text
    for am, en in AMHARIC_TO_LATIN.items():
        result = result.replace(am, en)
    
    # Clean up multiple spaces
    result = re.sub(r'\s+', ' ', result)
    return result.strip()


def translate_word(word):
    """
    Translate common Amharic words to English.
    
    Args:
        word (str): Amharic word
    
    Returns:
        str: English translation (or original if not found)
    """
    return COMMON_TRANSLATIONS.get(word, word)


def translate_phrase(phrase):
    """
    Translate a phrase by replacing known words.
    
    Args:
        phrase (str): Amharic phrase
    
    Returns:
        str: English translation with unknown words preserved
    """
    if not phrase:
        return ''
    
    words = phrase.split()
    translated_words = [translate_word(word) for word in words]
    return ' '.join(translated_words)


# ==================== DATE LOCALIZATION ====================

def localize_date(date_obj, target_lang='am'):
    """
    Localize date to target language.
    
    Args:
        date_obj (datetime): Date object
        target_lang (str): 'am' or 'en'
    
    Returns:
        str: Localized date string
    """
    if not date_obj:
        return ''
    
    if target_lang == 'am':
        month_name = AMHARIC_MONTHS.get(date_obj.month, '')
        return f"{date_obj.day} {month_name} {date_obj.year}"
    else:
        month_name = ENGLISH_MONTHS.get(date_obj.month, '')
        return f"{month_name} {date_obj.day}, {date_obj.year}"


def localize_datetime(dt_obj, target_lang='am'):
    """
    Localize datetime to target language.
    
    Args:
        dt_obj (datetime): Datetime object
        target_lang (str): 'am' or 'en'
    
    Returns:
        str: Localized datetime string
    """
    if not dt_obj:
        return ''
    
    date_str = localize_date(dt_obj, target_lang)
    time_str = dt_obj.strftime('%H:%M')
    
    return f"{date_str} {time_str}"


# ==================== NUMBER LOCALIZATION ====================

def format_number_ethiopian(number):
    """
    Format number with Ethiopian digit separators.
    
    Args:
        number (int or float): Number to format
    
    Returns:
        str: Formatted number string
    """
    try:
        num_float = float(number)
        
        # Convert to Ethiopian number format (using regular digits)
        # Note: For actual Ge'ez numerals, additional mapping would be needed
        
        parts = f"{num_float:,.0f}".split('.')
        integer_part = parts[0]
        
        # Add Ethiopian-style separators (every 2 digits from right)
        result = []
        for i, char in enumerate(reversed(integer_part)):
            if i > 0 and i % 2 == 0:
                result.append(',')
            result.append(char)
        
        formatted = ''.join(reversed(result))
        
        if len(parts) > 1:
            formatted += f".{parts[1]}"
        
        return formatted
    except (ValueError, TypeError):
        return str(number)


def format_currency(amount, currency='ETB', lang='am'):
    """
    Format currency amount.
    
    Args:
        amount (float): Amount to format
        currency (str): Currency code (ETB, USD)
        lang (str): Language for formatting
    
    Returns:
        str: Formatted currency string
    """
    try:
        amount_float = float(amount)
        formatted = f"{amount_float:,.2f}"
        
        if lang == 'am':
            return f"{formatted} {currency}"
        else:
            return f"{currency} {formatted}"
    except (ValueError, TypeError):
        return f"{amount} {currency}"


# ==================== PRODUCT TRANSLATIONS ====================

def translate_product_name(product, target_lang='en'):
    """
    Get product name in target language.
    
    Args:
        product (dict or tuple): Product data
        target_lang (str): 'am' or 'en'
    
    Returns:
        str: Product name in target language
    """
    if target_lang == 'am':
        return product.get('name_am') or product.get('name_en', '')
    else:
        return product.get('name_en') or product.get('name_am', '')


def translate_product_description(product, target_lang='en'):
    """
    Get product description in target language.
    
    Args:
        product (dict or tuple): Product data
        target_lang (str): 'am' or 'en'
    
    Returns:
        str: Product description in target language
    """
    if target_lang == 'am':
        return product.get('description_am') or product.get('description_en', '')
    else:
        return product.get('description_en') or product.get('description_am', '')


# ==================== CATEGORY TRANSLATIONS ====================

CATEGORY_TRANSLATIONS = {
    'ሶፋ': {'en': 'Sofa', 'icon': '🛋️'},
    'አልጋ': {'en': 'Bed', 'icon': '🛏️'},
    'መጅሊስ': {'en': 'Mejlis', 'icon': '🪑'},
    'መጋረጃ': {'en': 'Curtain', 'icon': '🚪'},
    'ቁምሳጥን': {'en': 'Wardrobe', 'icon': '🗄️'},
    'ሌላ': {'en': 'Other', 'icon': '📦'},
    'Sofa': {'am': 'ሶፋ', 'icon': '🛋️'},
    'Bed': {'am': 'አልጋ', 'icon': '🛏️'},
    'Mejlis': {'am': 'መጅሊስ', 'icon': '🪑'},
    'Curtain': {'am': 'መጋረጃ', 'icon': '🚪'},
    'Wardrobe': {'am': 'ቁምሳጥን', 'icon': '🗄️'},
    'Other': {'am': 'ሌላ', 'icon': '📦'}
}


def translate_category(category, target_lang='en'):
    """
    Translate category name.
    
    Args:
        category (str): Category name in either language
        target_lang (str): 'am' or 'en'
    
    Returns:
        str: Translated category name
    """
    if category in CATEGORY_TRANSLATIONS:
        return CATEGORY_TRANSLATIONS[category].get(target_lang, category)
    
    return category


def get_category_icon(category):
    """
    Get icon for a category.
    
    Args:
        category (str): Category name
    
    Returns:
        str: Emoji icon for the category
    """
    if category in CATEGORY_TRANSLATIONS:
        return CATEGORY_TRANSLATIONS[category].get('icon', '📦')
    
    return '📦'


# ==================== STATUS TRANSLATIONS ====================

STATUS_TRANSLATIONS = {
    'pending': {'am': 'በመጠባበቅ ላይ', 'en': 'Pending', 'icon': '⏳'},
    'confirmed': {'am': 'ተረጋግጧል', 'en': 'Confirmed', 'icon': '✅'},
    'shipped': {'am': 'ተልኳል', 'en': 'Shipped', 'icon': '🚚'},
    'delivered': {'am': 'ደርሷል', 'en': 'Delivered', 'icon': '🎉'},
    'cancelled': {'am': 'ተሰርዟል', 'en': 'Cancelled', 'icon': '❌'},
    'active': {'am': 'ንቁ', 'en': 'Active', 'icon': '🟢'},
    'inactive': {'am': 'ንቁ ያልሆነ', 'en': 'Inactive', 'icon': '🔴'}
}


def translate_status(status, target_lang='en'):
    """
    Translate order/product status.
    
    Args:
        status (str): Status key
        target_lang (str): 'am' or 'en'
    
    Returns:
        str: Translated status
    """
    if status in STATUS_TRANSLATIONS:
        return STATUS_TRANSLATIONS[status].get(target_lang, status)
    
    return status


def get_status_icon(status):
    """
    Get icon for a status.
    
    Args:
        status (str): Status key
    
    Returns:
        str: Emoji icon for the status
    """
    if status in STATUS_TRANSLATIONS:
        return STATUS_TRANSLATIONS[status].get('icon', '📌')
    
    return '📌'


# ==================== GENERAL HELPER ====================

def get_text_by_lang(text_am, text_en, lang='am'):
    """
    Get text based on language.
    
    Args:
        text_am (str): Amharic text
        text_en (str): English text
        lang (str): Language code ('am' or 'en')
    
    Returns:
        str: Text in requested language
    """
    if lang == 'am' and text_am:
        return text_am
    elif text_en:
        return text_en
    return text_am or text_en or ''