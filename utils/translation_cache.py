"""
Translation Cache Module for Ethiosadat / Semira Fashion

Static translation fallbacks for Amharic (am), English (en), and Arabic (ar).
Dynamic translation via googletrans has been removed — it was unreliable due to
frequent Google API changes. All UI strings are served from the static dictionary
below; product content uses the pre-stored multilingual columns in the database
(name, name_am, name_ar / description, description_am, description_ar).
"""

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

FALLBACK_TEXTS = {
    'am': {
        'error': 'ስህተት አለ',
        'loading': 'በመጫን ላይ...',
        'sorry': 'ይቅርታ',
        'try_again': 'እንደገና ይሞክሩ',
        'home': 'መነሻ',
        'products': 'ምርቶች',
        'cart': 'ጋሪ',
        'account': 'አካውንት',
        'search': 'ፈልግ',
        'all': 'ሁሉም',
        'add': 'ጨምር',
        'delete': 'ሰርዝ',
        'edit': 'ቀይር',
        'save': 'አስቀምጥ',
        'cancel': 'ሰርዝ',
        'close': 'ዝጋ',
        'submit': 'ላክ',
        'logout': 'ውጣ',
        'login': 'ግባ',
        'register': 'ተመዝገብ',
        'categories': 'ምድቦች',
        'orders': 'ትዕዛዞች',
        'settings': 'ቅንብሮች',
        'dashboard': 'ዳሽቦርድ',
        'admin': 'አስተዳዳሪ',
        'profile': 'መገለጫ',
        'wishlist': 'የምወዳቸው',
        'reviews': 'ግምገማዎች',
        'branches': 'ቅርንጫፎች',
        'contact': 'ያግኙን',
        'about': 'ስለ እኛ',
        'price': 'ዋጋ',
        'stock': 'ክምችት',
        'quantity': 'ብዛት',
        'total': 'ድምር',
        'shipping': 'ማጓጓዣ',
        'free_shipping': 'ነፃ ማጓጓዣ',
        'checkout': 'ክፍያ',
        'order_placed': 'ትዕዛዝ ተቀበለ',
        'out_of_stock': 'አልቋል',
        'in_stock': 'አለ',
        'featured': 'ተለዩ',
        'new': 'አዲስ',
        'sale': 'ቅናሽ',
        'no_products': 'ምርቶች አልተገኙም',
        'add_to_cart': 'ወደ ጋሪ ጨምር',
        'buy_now': 'አሁን ግዛ',
        'continue_shopping': 'ግዢ ቀጥል',
        'empty_cart': 'ጋሪ ባዶ ነው',
        'language': 'ቋንቋ',
        'currency': 'ምንዛሬ',
        'whatsapp_order': 'በ WhatsApp ትዕዛዝ',
        'payment_method': 'የክፍያ ዘዴ',
        'cash_on_delivery': 'ሲደርስ ይከፈላል',
        'address': 'አድራሻ',
        'phone': 'ስልክ',
        'name': 'ስም',
        'email': 'ኢሜይል',
        'password': 'የይለፍ ቃል',
        'confirm_password': 'የይለፍ ቃል አረጋግጥ',
        'forgot_password': 'የይለፍ ቃልዎን ረሱ?',
        'sign_in': 'ግቡ',
        'sign_up': 'ተመዝገቡ',
        'welcome': 'እንኳን ደህና መጡ',
        'thank_you': 'አመሰግናለሁ',
        'success': 'ተሳካ',
        'failed': 'አልተሳካም',
        'page_not_found': 'ገጽ አልተገኘም',
        'server_error': 'የሰርቨር ስህተት',
        'no_results': 'ምንም ውጤት አልተገኘም',
        'view_all': 'ሁሉንም ይመልከቱ',
        'read_more': 'ተጨማሪ አንብብ',
        'share': 'አጋራ',
        'copy_link': 'ሊንክ ቅዳ',
        'color': 'ቀለም',
        'material': 'ቁሳቁስ',
        'dimensions': 'መጠኖች',
        'weight': 'ክብደት',
        'description': 'መግለጫ',
        'related_products': 'ተዛማጅ ምርቶች',
        'recently_viewed': 'በቅርቡ የታዩ',
        'notifications': 'ማሳወቂያዎች',
        'mark_all_read': 'ሁሉንም እንደተነበበ ምልክት አድርግ',
        'no_notifications': 'ምንም ማሳወቂያ የለም',
        'filter': 'አጣራ',
        'sort_by': 'ደርድር',
        'newest': 'አዲስ',
        'oldest': 'ቀድሞ',
        'price_low_high': 'ዋጋ: ዝቅ ወደ ላይ',
        'price_high_low': 'ዋጋ: ከፍ ወደ ታች',
        'popular': 'ታዋቂ',
    },
    'en': {
        'error': 'An error occurred',
        'loading': 'Loading...',
        'sorry': 'Sorry',
        'try_again': 'Try again',
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
        'categories': 'Categories',
        'orders': 'Orders',
        'settings': 'Settings',
        'dashboard': 'Dashboard',
        'admin': 'Admin',
        'profile': 'Profile',
        'wishlist': 'Wishlist',
        'reviews': 'Reviews',
        'branches': 'Branches',
        'contact': 'Contact Us',
        'about': 'About Us',
        'price': 'Price',
        'stock': 'Stock',
        'quantity': 'Quantity',
        'total': 'Total',
        'shipping': 'Shipping',
        'free_shipping': 'Free Shipping',
        'checkout': 'Checkout',
        'order_placed': 'Order Placed',
        'out_of_stock': 'Out of Stock',
        'in_stock': 'In Stock',
        'featured': 'Featured',
        'new': 'New',
        'sale': 'Sale',
        'no_products': 'No products found',
        'add_to_cart': 'Add to Cart',
        'buy_now': 'Buy Now',
        'continue_shopping': 'Continue Shopping',
        'empty_cart': 'Your cart is empty',
        'language': 'Language',
        'currency': 'Currency',
        'whatsapp_order': 'Order via WhatsApp',
        'payment_method': 'Payment Method',
        'cash_on_delivery': 'Cash on Delivery',
        'address': 'Address',
        'phone': 'Phone',
        'name': 'Name',
        'email': 'Email',
        'password': 'Password',
        'confirm_password': 'Confirm Password',
        'forgot_password': 'Forgot your password?',
        'sign_in': 'Sign In',
        'sign_up': 'Sign Up',
        'welcome': 'Welcome',
        'thank_you': 'Thank You',
        'success': 'Success',
        'failed': 'Failed',
        'page_not_found': 'Page Not Found',
        'server_error': 'Server Error',
        'no_results': 'No results found',
        'view_all': 'View All',
        'read_more': 'Read More',
        'share': 'Share',
        'copy_link': 'Copy Link',
        'color': 'Color',
        'material': 'Material',
        'dimensions': 'Dimensions',
        'weight': 'Weight',
        'description': 'Description',
        'related_products': 'Related Products',
        'recently_viewed': 'Recently Viewed',
        'notifications': 'Notifications',
        'mark_all_read': 'Mark all as read',
        'no_notifications': 'No notifications',
        'filter': 'Filter',
        'sort_by': 'Sort By',
        'newest': 'Newest',
        'oldest': 'Oldest',
        'price_low_high': 'Price: Low to High',
        'price_high_low': 'Price: High to Low',
        'popular': 'Popular',
    },
    'ar': {
        'error': 'حدث خطأ',
        'loading': 'جاري التحميل...',
        'sorry': 'عذرا',
        'try_again': 'حاول مجددا',
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
        'categories': 'الفئات',
        'orders': 'الطلبات',
        'settings': 'الإعدادات',
        'dashboard': 'لوحة التحكم',
        'admin': 'الإدارة',
        'profile': 'الملف الشخصي',
        'wishlist': 'قائمة الأمنيات',
        'reviews': 'التقييمات',
        'branches': 'الفروع',
        'contact': 'اتصل بنا',
        'about': 'من نحن',
        'price': 'السعر',
        'stock': 'المخزون',
        'quantity': 'الكمية',
        'total': 'الإجمالي',
        'shipping': 'الشحن',
        'free_shipping': 'شحن مجاني',
        'checkout': 'الدفع',
        'order_placed': 'تم تقديم الطلب',
        'out_of_stock': 'غير متوفر',
        'in_stock': 'متوفر',
        'featured': 'مميز',
        'new': 'جديد',
        'sale': 'خصم',
        'no_products': 'لا توجد منتجات',
        'add_to_cart': 'أضف إلى السلة',
        'buy_now': 'اشتر الآن',
        'continue_shopping': 'مواصلة التسوق',
        'empty_cart': 'السلة فارغة',
        'language': 'اللغة',
        'currency': 'العملة',
        'whatsapp_order': 'الطلب عبر واتساب',
        'payment_method': 'طريقة الدفع',
        'cash_on_delivery': 'الدفع عند الاستلام',
        'address': 'العنوان',
        'phone': 'الهاتف',
        'name': 'الاسم',
        'email': 'البريد الإلكتروني',
        'password': 'كلمة المرور',
        'confirm_password': 'تأكيد كلمة المرور',
        'forgot_password': 'نسيت كلمة المرور؟',
        'sign_in': 'تسجيل الدخول',
        'sign_up': 'إنشاء حساب',
        'welcome': 'مرحبا',
        'thank_you': 'شكرا',
        'success': 'نجح',
        'failed': 'فشل',
        'page_not_found': 'الصفحة غير موجودة',
        'server_error': 'خطأ في الخادم',
        'no_results': 'لا توجد نتائج',
        'view_all': 'عرض الكل',
        'read_more': 'اقرأ المزيد',
        'share': 'مشاركة',
        'copy_link': 'نسخ الرابط',
        'color': 'اللون',
        'material': 'المادة',
        'dimensions': 'الأبعاد',
        'weight': 'الوزن',
        'description': 'الوصف',
        'related_products': 'منتجات ذات صلة',
        'recently_viewed': 'شاهدته مؤخرا',
        'notifications': 'الإشعارات',
        'mark_all_read': 'تعليم الكل كمقروء',
        'no_notifications': 'لا توجد إشعارات',
        'filter': 'تصفية',
        'sort_by': 'ترتيب حسب',
        'newest': 'الأحدث',
        'oldest': 'الأقدم',
        'price_low_high': 'السعر: من الأقل للأعلى',
        'price_high_low': 'السعر: من الأعلى للأقل',
        'popular': 'الأكثر شعبية',
    }
}


@lru_cache(maxsize=2000)
def translate_text(text, target_lang='en'):
    """
    Return translation from the static dictionary.
    If the key is not found, return the original text unchanged.
    Product content should use the multilingual DB columns directly
    (name_am, name_ar, description_am, description_ar, etc.).
    """
    if not text or not isinstance(text, str):
        return text
    text = text.strip()
    if not text:
        return text
    if target_lang not in FALLBACK_TEXTS:
        target_lang = 'en'
    fallback = FALLBACK_TEXTS[target_lang]
    return fallback.get(text.lower(), text)


def get_text(key, lang='en', default=None):
    """Get a UI string by key and language."""
    fallback = FALLBACK_TEXTS.get(lang, FALLBACK_TEXTS['en'])
    return fallback.get(key.lower(), default or key)


def batch_translate(texts, target_lang='en'):
    """Translate a list of texts, returning a dict of original -> translated."""
    return {t: translate_text(t, target_lang) for t in texts if t}


def get_fallback_text(key, lang='en'):
    """Get fallback text for a key."""
    return FALLBACK_TEXTS.get(lang, {}).get(key, key)


def clear_translation_cache():
    """Clear the LRU translation cache."""
    translate_text.cache_clear()
    logger.info("Translation cache cleared")


def get_translation_stats():
    """Return cache hit/miss statistics."""
    info = translate_text.cache_info()
    total = info.hits + info.misses
    return {
        'hits': info.hits,
        'misses': info.misses,
        'maxsize': info.maxsize,
        'currsize': info.currsize,
        'hit_rate': info.hits / total if total > 0 else 0,
    }
