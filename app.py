# ==================== 1. IMPORTS ====================

import os
import sys
import json
import uuid
import time
import logging
import atexit
import urllib.parse
import re
import threading
from datetime import datetime, timedelta
from functools import wraps
from decimal import Decimal
import datetime as datetime_

from flask import (
    Flask, render_template, request, redirect, url_for,
    abort, session, flash, jsonify, send_from_directory, make_response, g
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import limiter

from config import Config
from database.db import get_db, init_db, commit_or_rollback, _get_database_url
from database.models import (
    User, Category, Product, CartItem, Order, OrderItem, Advertisement, Branch, Notification
)
from middleware.auth import login_required, admin_required, user_login_required, get_current_user, is_authenticated
from middleware.platform import get_platform, is_android_app
from utils.translation_cache import translate_text, batch_translate, clear_translation_cache, get_translation_stats, FALLBACK_TEXTS
from routes.shared import WHATSAPP_NUMBER, USER_DISCOUNT_RATE
from utils.csrf import generate_csrf, validate_csrf


# ==================== 2. APP INITIALIZATION ====================

app = Flask(__name__)


# ---- Live Visitor Tracking (in-memory, 5-minute window) ----
_visitor_lock = threading.Lock()
_active_visitors = {}   # {session_id: last_seen_timestamp}


class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if hasattr(obj, '__class__') and 'Undefined' in str(obj.__class__):
            return None
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


app.json_encoder = SafeJSONEncoder


def format_price_number(value):
    try:
        num = float(value)
        return f"{num:,.0f}"
    except (ValueError, TypeError):
        return str(value)


def format_price(value):
    try:
        num = float(value)
        return f"{num:,.0f} ETB"
    except (ValueError, TypeError):
        return str(value)


app.jinja_env.filters["format_price_number"] = format_price_number
app.jinja_env.filters["format_price"] = format_price
app.jinja_env.globals["format_price"] = format_price
app.jinja_env.globals["format_price_number"] = format_price_number

app.config.from_object(Config)
app.config['DATABASE_URL'] = _get_database_url()
_secret_key = os.environ.get('SECRET_KEY') or os.environ.get('SESSION_SECRET')
if not _secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Set it in the Replit Secrets panel to a long random string."
    )
app.secret_key = _secret_key

# Rate Limiter — shared via extensions.py so blueprints can import it
limiter.init_app(app)

# Upload configuration
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm', 'mov'}
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB — supports large ad images & videos

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'products'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'ads'), exist_ok=True)
os.makedirs('logs', exist_ok=True)


def allowed_file(filename):
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler = logging.FileHandler('logs/app.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
security_handler = logging.FileHandler('logs/security.log')
security_handler.setLevel(logging.WARNING)
security_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
app.logger.addHandler(file_handler)
app.logger.addHandler(security_handler)

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    raise RuntimeError(
        "ADMIN_PASSWORD environment variable is not set. "
        "Set it in the Replit Secrets panel."
    )
if ADMIN_PASSWORD == '1234':
    import warnings
    warnings.warn(
        "⚠️  SECURITY WARNING: Admin password is still the default '1234'. "
        "Change ADMIN_PASSWORD in the Replit Secrets panel before deploying!",
        stacklevel=2
    )
    app.logger.warning("⚠️  SECURITY: Default admin password '1234' detected — change it before going live!")

# ── CSRF Protection ──────────────────────────────────────────────────────────
app.jinja_env.globals['csrf_token'] = generate_csrf

_CSRF_EXEMPT_PREFIXES = ('/api/', '/static/')


@app.before_request
def csrf_protect():
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return
    for prefix in _CSRF_EXEMPT_PREFIXES:
        if request.path.startswith(prefix):
            return
    validate_csrf()


# ==================== 3. DATABASE INITIALIZATION ====================
# (Tables and seed data are handled by database/db.py → init_db())

# ==================== 4. LANGUAGE & TEXTS ====================

TEXTS = {
    'am': {
        'search_results': '🔍 የፍለጋ ውጤቶች',
        'find_perfect': 'ለቤትዎ ምርጥ የቤት እቃ ያግኙ',
        'showing_results_for': '🔎 ውጤቶች ለ',
        'products_found': 'ምርቶች ተገኝተዋል',
        'no_products_found': 'ምርት አልተገኘም',
        'we_couldnt_find': 'ለሚፈልጉት ቃል ምርት አልተገኘም',
        'try_tips': '💡 ይሞክሩ:',
        'tip_different_keywords': '• ሌሎች ቃላት ይጠቀሙ',
        'tip_check_spelling': '• ፊደሉን ያረጋግጡ',
        'tip_browse_categories': '• ምድቦቹን ያስሱ',
        'back_to_home': '← ወደ መነሻ ተመለስ',
        'popular_searches': '💡 ተወዳጅ ፍለጋዎች:',
        'try_searching_for': '💡 ለፍለጋ ይሞክሩ:',
        'sort_relevance': '📌 ተዛማጅነት',
        'sort_price_low_high': '💰 ዋጋ: ዝቅ → ከፍ',
        'sort_price_high_low': '💰 ዋጋ: ከፍ → ዝቅ',
        'sort_name_az': '📝 ስም: ሀ-ፐ',
        'sort_name_za': '📝 ስም: ፐ-ሀ',
        'filter_products': '🔍 ምርቶችን አጣራ',
        'search': 'እቃዎችን እዚህ ይፈልጉ...',
        'home': 'መነሻ',
        'products': 'ምርቶች',
        'contact': 'አግኙን',
        'about_us': 'ስለ እኛ',
        'our_branches': 'ቅርንጫፎቻችን',
        'all': 'ሁሉም',
        'all_products': 'ሁሉም ምርቶች',
        'categories': 'ምድቦች',
        'featured_products': '⭐ ተመራጭ ምርቶች',
        'new_arrivals': '🆕 አዲስ ምርቶች',
        'add_to_cart': '🛒 ወደ ጋሪ ጨምር',
        'view_details': 'ዝርዝር ይመልከቱ →',
        'shop_now': 'አሁን ይግዙ →',
        'login': 'ግባ',
        'register': 'ተመዝገብ',
        'logout': 'ውጣ',
        'profile': 'መገለጫ',
        'my_orders': 'የእኔ ትዕዛዞች',
        'my_cart': 'የእኔ ጋሪ',
        'in_stock': 'አለ',
        'out_of_stock': 'የለም',
        'quick_links': 'ፈጣን አገናኞች',
        'call_us': 'ይደውሉልን',
        'quality_tagline': 'ጥራቱን የጠበቀ የሴቶች እና የልጆች ልብስ በተመጣጣኝ ዋጋ እኛ ጋር ያገኛሉ',
        'free_shipping_msg': '🚚 ከ5,000 ብር በላይ ትዕዛዝ ነጻ ማጓጓዝ',
        'copyright_text': 'መብቱ በህግ የተጠበቀ ነው',
        'order_now': 'አሁን እዘዝ',
        'address': 'አድራሻ፦ አዲስ አበባ',
        'promo': 'ልዩ ቅናሽ!',
        'sofa': 'ሶፋ', 'bed': 'አልጋ', 'mejlis': 'መጅሊስ',
        'curtain': 'መጋረጃ', 'wardrobe': 'ቁምሳጥን',
        'admin_title': 'የአስተዳዳሪ ፓነል',
        'products_manage': 'ምርቶች', 'add_product': 'ምርት ጨምር',
        'ads_manage': 'ማስታወቂያዎች',
        'cart': 'ጋሪ', 'account': 'አካውንት', 'checkout': 'ትዕዛዝ አስገባ',
        'total': 'ጠቅላላ', 'subtotal': 'ንዑስ ድምር',
        'shipping': 'ማጓጓዝ', 'free_shipping': 'ነጻ ማጓጓዝ',
        'full_name': 'ሙሉ ስም', 'phone_number': 'ስልክ ቁጥር',
        'address_label': 'አድራሻ', 'additional_notes': 'ተጨማሪ ማብራሪያ',
        'submit_order': 'ትዕዛዝ ላክ', 'added_to_cart': 'ወደ ጋሪ ተጨምሯል',
        'password': 'የይለፍ ቃል', 'confirm_password': 'የይለፍ ቃል አረጋግጥ',
        'no_account': 'አካውንት የለም', 'have_account': 'አካውንት አለ',
        'edit_profile': 'መገለጫ አርትዕ',
        # product detail
        'product_description': '📝 የምርት መግለጫ',
        'features': '✨ ባህሪያት:',
        'specifications': '📏 ዝርዝር መረጃ:',
        'quantity': 'ብዛት:',
        'material': 'ቁሳቁስ:',
        'color_label': 'ቀለም:',
        'dimensions': 'ልኬቶች:',
        'weight_label': 'ክብደት:',
        'continue_shopping': '← ግዢ ቀጥሉ',
        'customer_reviews': '⭐ የደንበኛ ግምገማዎች',
        'write_review': '✍️ ግምገማ ጻፍ',
        'you_may_also_like': '🔗 ሌሎቹን ይወዱ ይሆናል',
        'no_description': 'መግለጫ አልተገኘም። ለተጨማሪ መረጃ ያግኙን።',
        'high_quality': '✓ ከፍተኛ ጥራት ያለው ጨርቃጨርቅ',
        'modern_design': '✓ ዘመናዊ ዲዛይን',
        'durable': '✓ ዘላቂ ጥራት',
        'easy_to_clean': '✓ ለማጽዳት ቀላል',
        'login_for_discount': 'ለ <strong>10% ቅናሽ</strong>',
        'shopping_cart': '🛒 ጋሪ',
        'empty_cart': 'ጋሪ ባዶ ነው',
        'return_to_shop': '← ወደ ሱቅ ተመለስ',
        'order_summary': 'የትዕዛዝ ማጠቃለያ',
        'proceed_to_checkout': 'ወደ ትዕዛዝ ቀጥል →',
        'only_left': 'ብቻ ቀርቷል — በፍጥነት ይዘዙ!',
        'bulk_import': '📥 በብዛት አስገባ (CSV/Excel)',
    },
    'en': {
        'search_results': '🔍 Search Results',
        'find_perfect': 'Find the perfect fashion for you and your family',
        'showing_results_for': '🔎 Showing results for',
        'products_found': 'product(s) found',
        'no_products_found': 'No products found',
        'we_couldnt_find': "We couldn't find any products matching",
        'try_tips': '💡 Try:', 'tip_different_keywords': '• Using different keywords',
        'tip_check_spelling': '• Checking the spelling',
        'tip_browse_categories': '• Browsing our categories',
        'back_to_home': '← Back to Home',
        'popular_searches': '💡 Popular searches:',
        'try_searching_for': '💡 Try searching for:',
        'sort_relevance': '📌 Relevance',
        'sort_price_low_high': '💰 Price: Low to High',
        'sort_price_high_low': '💰 Price: High to Low',
        'sort_name_az': '📝 Name: A to Z', 'sort_name_za': '📝 Name: Z to A',
        'filter_products': '🔍 Filter Products',
        'search': 'Search products here...',
        'home': 'Home', 'products': 'Products', 'contact': 'Contact Us',
        'about_us': 'About Us', 'our_branches': 'Our Branches',
        'all': 'All', 'all_products': 'All Products', 'categories': 'Categories',
        'featured_products': '⭐ Featured Products', 'new_arrivals': '🆕 New Arrivals',
        'add_to_cart': '🛒 Add to Cart', 'view_details': 'View Details →',
        'shop_now': 'Shop Now →', 'login': 'Login', 'register': 'Register',
        'logout': 'Logout', 'profile': 'Profile',
        'my_orders': 'My Orders', 'my_cart': 'My Cart',
        'in_stock': 'In Stock', 'out_of_stock': 'Out of Stock',
        'quick_links': 'Quick Links', 'call_us': 'Call Us',
        'quality_tagline': 'Premium women\'s and children\'s clothing at affordable prices',
        'free_shipping_msg': '🚚 Free shipping on orders over 5,000 ETB',
        'copyright_text': 'All Rights Reserved',
        'order_now': 'Order Now', 'address': 'Address: ወሎ ደሴ ኩታበር', 'promo': 'Special Offer!',
        'sofa': 'Sofa', 'bed': 'Bed', 'mejlis': 'Mejlis',
        'curtain': 'Curtain', 'wardrobe': 'Wardrobe',
        'admin_title': 'Admin Panel', 'products_manage': 'Products',
        'add_product': 'Add Product', 'ads_manage': 'Advertisements',
        'cart': 'Cart', 'account': 'Account', 'checkout': 'Checkout',
        'total': 'Total', 'subtotal': 'Subtotal', 'shipping': 'Shipping',
        'free_shipping': 'Free Shipping', 'full_name': 'Full Name',
        'phone_number': 'Phone Number', 'address_label': 'Address',
        'additional_notes': 'Additional Notes', 'submit_order': 'Submit Order',
        'added_to_cart': 'Added to cart', 'password': 'Password',
        'confirm_password': 'Confirm Password', 'no_account': 'No account',
        'have_account': 'Have account', 'edit_profile': 'Edit Profile',
        'product_description': '📝 Product Description',
        'features': '✨ Features:',
        'specifications': '📏 Specifications:',
        'quantity': 'Quantity:',
        'material': 'Material:',
        'color_label': 'Color:',
        'dimensions': 'Dimensions:',
        'weight_label': 'Weight:',
        'continue_shopping': '← Continue Shopping',
        'customer_reviews': '⭐ Customer Reviews',
        'write_review': '✍️ Write a Review',
        'you_may_also_like': '🔗 You May Also Like',
        'no_description': 'No description available. Please contact us for more information.',
        'high_quality': '✓ High-quality materials',
        'modern_design': '✓ Modern design',
        'durable': '✓ Durable construction',
        'easy_to_clean': '✓ Easy to clean',
        'login_for_discount': 'for <strong>10% off</strong>',
        'shopping_cart': '🛒 Shopping Cart',
        'empty_cart': 'Your cart is empty',
        'return_to_shop': '← Return to Shop',
        'order_summary': 'Order Summary',
        'proceed_to_checkout': 'Proceed to Checkout →',
        'only_left': 'left in stock — Order soon!',
        'bulk_import': '📥 Bulk Import (CSV/Excel)',
    },
    'ar': {
        'search_results': '🔍 نتائج البحث',
        'find_perfect': 'ابحث عن الأثاث المثالي لمنزلك',
        'showing_results_for': '🔎 نتائج عن',
        'products_found': 'منتج وجد', 'no_products_found': 'لم يتم العثور على منتجات',
        'we_couldnt_find': 'لم نجد أي منتجات تطابق',
        'try_tips': '💡 جرب:', 'tip_different_keywords': '• استخدام كلمات مختلفة',
        'tip_check_spelling': '• التحقق من الإملاء',
        'tip_browse_categories': '• تصفح فئاتنا',
        'back_to_home': 'العودة للرئيسية →',
        'popular_searches': '💡 عمليات البحث الشائعة:',
        'try_searching_for': '💡 جرب البحث عن:',
        'sort_relevance': '📌 الصلة',
        'sort_price_low_high': '💰 السعر: من الأدنى',
        'sort_price_high_low': '💰 السعر: من الأعلى',
        'sort_name_az': '📝 الاسم: أ-ي', 'sort_name_za': '📝 الاسم: ي-أ',
        'filter_products': '🔍 تصفية المنتجات',
        'search': 'ابحث عن المنتجات هنا...',
        'home': 'الرئيسية', 'products': 'المنتجات', 'contact': 'اتصل بنا',
        'about_us': 'معلومات عنا', 'our_branches': 'فروعنا',
        'all': 'الجميع', 'all_products': 'جميع المنتجات', 'categories': 'الفئات',
        'featured_products': '⭐ المنتجات المميزة', 'new_arrivals': '🆕 وصل حديثاً',
        'add_to_cart': '🛒 أضف إلى السلة', 'view_details': 'عرض التفاصيل ←',
        'shop_now': 'تسوق الآن ←', 'login': 'تسجيل الدخول', 'register': 'تسجيل',
        'logout': 'تسجيل الخروج', 'profile': 'الملف الشخصي',
        'my_orders': 'طلباتي', 'my_cart': 'سلتي',
        'in_stock': 'متوفر', 'out_of_stock': 'غير متوفر',
        'quick_links': 'روابط سريعة', 'call_us': 'اتصل بنا',
        'quality_tagline': 'ملابس نسائية وأطفال عالية الجودة بأسعار معقولة',
        'free_shipping_msg': '🚚 شحن مجاني للطلبات التي تتجاوز 5,000 بر إثيوبي',
        'copyright_text': 'جميع الحقوق محفوظة',
        'order_now': 'اطلب الآن', 'address': 'العنوان: أديس أبابا', 'promo': 'عرض خاص!',
        'sofa': 'أريكة', 'bed': 'سرير', 'mejlis': 'مجلس',
        'curtain': 'ستارة', 'wardrobe': 'خزانة',
        'cart': 'السلة', 'account': 'الحساب', 'checkout': 'الدفع',
        'total': 'المجموع', 'subtotal': 'المجموع الفرعي', 'shipping': 'الشحن',
        'free_shipping': 'شحن مجاني', 'full_name': 'الاسم الكامل',
        'phone_number': 'رقم الهاتف', 'address_label': 'العنوان',
        'additional_notes': 'ملاحظات إضافية', 'submit_order': 'تقديم الطلب',
        'added_to_cart': 'تمت الإضافة إلى السلة', 'password': 'كلمة المرور',
        'confirm_password': 'تأكيد كلمة المرور', 'no_account': 'لا يوجد حساب',
        'have_account': 'لديك حساب', 'edit_profile': 'تعديل الملف الشخصي',
        'product_description': '📝 وصف المنتج',
        'features': '✨ المميزات:',
        'specifications': '📏 المواصفات:',
        'quantity': 'الكمية:',
        'material': 'المادة:',
        'color_label': 'اللون:',
        'dimensions': 'الأبعاد:',
        'weight_label': 'الوزن:',
        'continue_shopping': 'مواصلة التسوق →',
        'customer_reviews': '⭐ آراء العملاء',
        'write_review': '✍️ اكتب تقييماً',
        'you_may_also_like': '🔗 قد يعجبك أيضاً',
        'no_description': 'لا يوجد وصف متاح. يرجى التواصل معنا للمزيد من المعلومات.',
        'high_quality': '✓ مواد عالية الجودة',
        'modern_design': '✓ تصميم عصري',
        'durable': '✓ متين وطويل الأمد',
        'easy_to_clean': '✓ سهل التنظيف',
        'login_for_discount': 'للحصول على <strong>خصم 10%</strong>',
        'shopping_cart': '🛒 سلة التسوق',
        'empty_cart': 'سلتك فارغة',
        'return_to_shop': 'العودة للمتجر →',
        'order_summary': 'ملخص الطلب',
        'proceed_to_checkout': 'الانتقال إلى الدفع →',
        'only_left': 'فقط متبقٍ — اطلب الآن!',
        'bulk_import': '📥 استيراد مجمع (CSV/Excel)',
    }
}

DEFAULT_LANGUAGE = 'am'
SUPPORTED_LANGUAGES = ['am', 'en', 'ar']


def get_lang():
    lang = session.get('lang', DEFAULT_LANGUAGE)
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def get_text(key, lang=None):
    if lang is None:
        lang = get_lang()
    if lang == 'en':
        return key
    manual_translation = TEXTS.get(lang, {}).get(key)
    if manual_translation:
        return manual_translation
    try:
        return translate_text(key, lang)
    except Exception:
        return key


def set_lang(lang):
    if lang in SUPPORTED_LANGUAGES:
        session['lang'] = lang
        return True
    return False


# ==================== 5. CONTEXT PROCESSORS ====================

def get_google_translate_widget():
    return '''
    <div id="google_translate_element" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;"></div>
    <script type="text/javascript">
        function googleTranslateElementInit() {
            new google.translate.TranslateElement({
                pageLanguage: 'am', includedLanguages: 'am,en,ar',
                layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
                autoDisplay: false
            }, 'google_translate_element');
        }
    </script>
    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
    '''


@app.context_processor
def inject_globals():
    lang = session.get('lang', 'am')
    current_user = get_current_user()
    platform = get_platform()

    pending_orders_count = 0
    low_stock_count = 0
    unread_messages_count = 0
    products_count = 0
    ads_count = 0
    if session.get('admin'):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM orders WHERE status = 'pending') AS pending_orders,
                    (SELECT COUNT(*) FROM products
                     WHERE stock_quantity <= low_stock_threshold AND stock_quantity > 0) AS low_stock,
                    (SELECT COUNT(*) FROM contact_messages WHERE is_read = 0) AS unread_messages,
                    (SELECT COUNT(*) FROM products WHERE is_active = 1) AS products_count,
                    (SELECT COUNT(*) FROM advertisements WHERE is_active = 1) AS ads_count
            """)
            row = cur.fetchone()
            if row:
                pending_orders_count  = row[0] or 0
                low_stock_count       = row[1] or 0
                unread_messages_count = row[2] or 0
                products_count        = row[3] or 0
                ads_count             = row[4] or 0
        except Exception:
            pass

    return {
        'current_year': datetime_.datetime.now().year,
        'lang': lang,
        'current_user': current_user,
        'is_authenticated': is_authenticated(),
        'is_admin': session.get('admin', False),
        'is_android_app': is_android_app(),
        'platform': platform,
        'whatsapp_number': WHATSAPP_NUMBER,
        'google_translate_widget': get_google_translate_widget(),
        'app_name': 'SEMIRA FASHION',
        'pending_orders_count': pending_orders_count,
        'low_stock_count': low_stock_count,
        'unread_messages_count': unread_messages_count,
        'products_count': products_count,
        'ads_count': ads_count,
        'user_discount_rate': USER_DISCOUNT_RATE,
        'member_discount_multiplier': round(1 - USER_DISCOUNT_RATE, 4),
    }


@app.context_processor
def inject_language():
    current_lang = get_lang()

    def _(key):
        return get_text(key, current_lang)

    def product_name(product, lang=None):
        lng = lang or current_lang
        try:
            if lng == 'am':
                return product['name_am'] or product['name'] or ''
            elif lng == 'ar':
                return product['name_ar'] or product['name'] or ''
            else:
                return product.get('name_en') or product['name'] or ''
        except (KeyError, TypeError):
            return ''

    def product_description(product, lang=None):
        lng = lang or current_lang
        try:
            if lng == 'am':
                return product['description_am'] or product.get('description') or ''
            elif lng == 'ar':
                return product['description_ar'] or product.get('description') or ''
            else:
                return product.get('description_en') or product.get('description') or ''
        except (KeyError, TypeError):
            return ''

    def _get_ad_field_value(ad, field_names, default=''):
        if ad is None:
            return default
        if isinstance(ad, dict):
            for field in field_names:
                value = ad.get(field)
                if value not in (None, ''):
                    return value
            return default
        for field in field_names:
            value = getattr(ad, field, None)
            if value not in (None, ''):
                return value
        return default

    def localized_ad_title(ad, lang=None):
        lng = (lang or current_lang or '').lower()
        if lng == 'am':
            return _get_ad_field_value(ad, ['title_am', 'title', 'title_en', 'title_ar'], '')
        if lng == 'ar':
            return _get_ad_field_value(ad, ['title_ar', 'title', 'title_am', 'title_en'], '')
        return _get_ad_field_value(ad, ['title_en', 'title', 'title_am', 'title_ar'], '')

    def localized_ad_description(ad, lang=None):
        lng = (lang or current_lang or '').lower()
        if lng == 'am':
            return _get_ad_field_value(ad, ['description_am', 'description', 'description_en', 'description_ar', 'text'], '')
        if lng == 'ar':
            return _get_ad_field_value(ad, ['description_ar', 'description', 'description_am', 'description_en', 'text'], '')
        return _get_ad_field_value(ad, ['description_en', 'description', 'description_am', 'description_ar', 'text'], '')

    def category_name(cat, lang=None):
        lng = lang or current_lang
        try:
            if lng == 'am':
                return cat['name_am'] or cat['name'] or ''
            elif lng == 'ar':
                return cat['name_ar'] or cat['name'] or ''
            else:
                return cat['name'] or ''
        except (KeyError, TypeError):
            return ''

    return {
        'lang': current_lang,
        't': TEXTS.get(current_lang, TEXTS[DEFAULT_LANGUAGE]),
        '_': _,
        'product_name': product_name,
        'product_description': product_description,
        'localized_ad_title': localized_ad_title,
        'localized_ad_description': localized_ad_description,
        'category_name': category_name,
    }


# ==================== 6. TEMPLATE FILTERS ====================

@app.template_filter('format_price')
def format_price_filter(price):
    try:
        return f"{float(price):,.0f} ETB"
    except (ValueError, TypeError):
        return str(price)


@app.template_filter('format_number')
def format_number_filter(price):
    try:
        return f"{float(price):,.0f}"
    except (ValueError, TypeError):
        return str(price)


@app.template_filter('truncate_text')
def truncate_filter(text, length=50):
    if not text:
        return ''
    return text if len(text) <= length else text[:length].rstrip() + '...'


@app.template_filter('format_datetime')
def datetime_filter(dt):
    if not dt:
        return ''
    if isinstance(dt, str):
        try:
            dt = datetime_.datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except Exception:
            return dt
    return dt.strftime('%Y-%m-%d %H:%M')


@app.template_filter('format_date')
def format_date_filter(date_obj, format_type='short'):
    if not date_obj:
        return ''
    if isinstance(date_obj, str):
        try:
            date_obj = datetime_.datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
        except Exception:
            return date_obj
    if format_type == 'short':
        return date_obj.strftime('%d/%m/%Y')
    elif format_type == 'long':
        return date_obj.strftime('%B %d, %Y')
    return date_obj.strftime('%Y-%m-%d %H:%M:%S')


@app.template_filter('nl2br')
def nl2br_filter(text):
    if not text:
        return ''
    import html
    from markupsafe import Markup
    escaped = html.escape(str(text))
    return Markup(escaped.replace('\n', '<br>'))


@app.template_filter('default_value')
def default_filter(value, default_value=''):
    if value is None or value == '':
        return default_value
    return value


@app.template_filter('currency_symbol')
def currency_symbol_filter(price):
    return "ETB"


@app.template_filter('safe_text')
def safe_text_filter(text):
    if not text:
        return ''
    import html
    return html.escape(str(text))


# ==================== 7. ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(error):
    app.logger.warning(f"404 Error: {request.url}")
    lang = get_lang()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'error': 'Page not found'}), 404
    titles = {'am': 'ገጹ አልተገኘም', 'en': 'Page Not Found', 'ar': 'الصفحة غير موجودة'}
    messages = {
        'am': 'ይቅርታ፣ እርስዎ የፈለጉት ገጽ የለም።',
        'en': 'Sorry, the page you are looking for does not exist.',
        'ar': 'عذرًا، الصفحة التي تبحث عنها غير موجودة.'
    }
    title = titles.get(lang, titles['en'])
    message = messages.get(lang, messages['en'])
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>404 - {title}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:Arial,sans-serif;background:linear-gradient(135deg,#1a73e8,#0d47a1);display:flex;justify-content:center;align-items:center;height:100vh;}}
.box{{background:white;padding:40px;border-radius:20px;text-align:center;max-width:400px;}}
h1{{color:#1a73e8;font-size:80px;margin:0;}}p{{margin:20px 0;color:#666;}}
a{{display:inline-block;background:#1a73e8;color:white;padding:12px 24px;text-decoration:none;border-radius:30px;}}</style>
</head><body><div class="box"><h1>404</h1><p>{message}</p><a href="/">Home</a></div></body></html>''', 404


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error(f"500 Error: {request.url} - {error}")
    import traceback
    app.logger.error(traceback.format_exc())
    lang = get_lang()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    messages = {
        'am': 'ችግር ተፈጥሯል። እባክዎ ቆይተው ይሞክሩ።',
        'en': 'Something went wrong. Please try again later.',
        'ar': 'حدث خطأ ما. يرجى المحاولة مرة أخرى لاحقًا.'
    }
    message = messages.get(lang, messages['en'])
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>500 - Server Error</title>
<style>*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:Arial,sans-serif;background:linear-gradient(135deg,#e44d26,#c0392b);display:flex;justify-content:center;align-items:center;height:100vh;}}
.box{{background:white;padding:40px;border-radius:20px;text-align:center;max-width:400px;}}
h1{{color:#e44d26;font-size:80px;margin:0;}}p{{margin:20px 0;color:#666;}}
a{{display:inline-block;background:#e44d26;color:white;padding:12px 24px;text-decoration:none;border-radius:30px;}}</style>
</head><body><div class="box"><h1>500</h1><p>{message}</p><a href="/">Home</a></div></body></html>''', 500


@app.errorhandler(429)
def ratelimit_exceeded(error):
    app.logger.warning(f"Rate limit exceeded: {request.remote_addr} - {request.path}")
    lang = get_lang()
    messages = {
        'am': 'በጣም ብዙ ጥያቄዎችን በአጭር ጊዜ ውስጥ ልከዋል። እባክዎ ቆይተው ይሞክሩ።',
        'en': 'Too many requests. Please try again later.',
        'ar': 'عدد كبير جدًا من الطلبات. يرجى المحاولة مرة أخرى لاحقًا.'
    }
    message = messages.get(lang, messages['en'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'error': message}), 429
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>429 - Too Many Requests</title>
<style>*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:Arial,sans-serif;background:linear-gradient(135deg,#ff9800,#f57c00);display:flex;justify-content:center;align-items:center;height:100vh;}}
.box{{background:white;padding:40px;border-radius:20px;text-align:center;max-width:400px;}}
h1{{color:#ff9800;font-size:80px;margin:0;}}p{{margin:20px 0;color:#666;}}
a{{display:inline-block;background:#ff9800;color:white;padding:12px 24px;text-decoration:none;border-radius:30px;}}</style>
</head><body><div class="box"><h1>429</h1><p>{message}</p><a href="/">Home</a></div></body></html>''', 429


# ==================== 9. REQUEST HOOKS ====================

@app.before_request
def start_request_timer():
    request.start_time = time.time()


@app.before_request
def set_secure_headers():
    pass


@app.after_request
def compress_response(response):
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.after_request
def add_security_headers(response):
    # X-Frame-Options — prevents clickjacking
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    # Prevent MIME-type sniffing
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    # Legacy XSS protection for older browsers
    response.headers.setdefault('X-XSS-Protection', '1; mode=block')
    # Referrer policy
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    # HSTS — only over HTTPS; 1 year max-age
    if request.is_secure:
        response.headers.setdefault(
            'Strict-Transport-Security', 'max-age=31536000; includeSubDomains'
        )
    # Content-Security-Policy — HTML responses only
    if 'text/html' in response.headers.get('Content-Type', ''):
        csp = {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' 'unsafe-eval' https://translate.google.com https://cdn.jsdelivr.net",
            'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
            'img-src': "'self' data: https:",
            'font-src': "'self' https://fonts.gstatic.com",
            'connect-src': "'self' https://server7.mp3quran.net https://server8.mp3quran.net",
            'media-src': "'self' https://server7.mp3quran.net https://server8.mp3quran.net",
            'frame-src': "https://translate.google.com",
        }
        response.headers['Content-Security-Policy'] = '; '.join(f"{k} {v}" for k, v in csp.items())
    return response


@app.after_request
def log_request_performance(response):
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        if elapsed > 1.0:
            app.logger.warning(f"Slow request: {request.method} {request.path} - {elapsed:.2f}s")
            response.headers['X-Response-Time'] = f"{elapsed:.3f}s"
    return response


@app.teardown_appcontext
def close_db_connection(exception=None):
    try:
        from database.db import close_db
        close_db(exception)
    except Exception as e:
        app.logger.error(f"Error closing database connection: {str(e)}")


# ==================== 10. APP STARTUP ====================

app.start_time = time.time()


def initialize_app():
    app.logger.info("Initializing Semira Fashion Application")
    try:
        init_db()
        app.logger.info("Database initialized successfully")
    except Exception as e:
        app.logger.error(f"Database initialization error: {str(e)}")

    # Load GROQ_API_KEY from DB settings if not already in environment
    if not os.environ.get('GROQ_API_KEY'):
        try:
            from database.db import get_db as _get_db
            _cursor = _get_db().cursor()
            _cursor.execute("SELECT value FROM settings WHERE key = 'groq_api_key'")
            _row = _cursor.fetchone()
            if _row and _row[0]:
                os.environ['GROQ_API_KEY'] = _row[0]
                app.logger.info("GROQ_API_KEY loaded from database settings")
        except Exception as _e:
            app.logger.debug(f"Could not load GROQ_API_KEY from DB: {_e}")
    for directory in ['logs', 'backups', 'static/uploads', 'static/uploads/products',
                      'static/uploads/ads', 'static/images', 'static/css', 'static/js']:
        os.makedirs(directory, exist_ok=True)
    app.logger.info("Application initialized successfully")


# ==================== 11. REGISTER BLUEPRINTS ====================

from routes import register_routes
register_routes(app)


# ==================== 12. INITIALIZE ====================

with app.app_context():
    initialize_app()


# ==================== 13. DAILY DIGEST SCHEDULER ====================

def _run_daily_digest(app_ref):
    """Gather yesterday's stats and email the admin digest."""
    with app_ref.app_context():
        try:
            from database.db import get_db as _get_db
            from services.email_service import (
                is_email_configured, send_email,
                build_digest_html, build_digest_text
            )
            import os as _os
            import datetime as _dt

            if not is_email_configured():
                app_ref.logger.info("Daily digest skipped — SMTP not configured.")
                return

            conn   = _get_db()
            cursor = conn.cursor()
            yesterday = (_dt.datetime.now() - _dt.timedelta(days=1)).date()

            # New orders yesterday
            cursor.execute(
                "SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders "
                "WHERE created_at::date = %s", (yesterday,)
            )
            row = cursor.fetchone()
            new_orders    = row[0] or 0
            total_revenue = float(row[1] or 0)

            # All pending orders
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status='pending'")
            pending_orders = cursor.fetchone()[0] or 0

            # Low stock products
            cursor.execute("""
                SELECT name, name_am, stock_quantity, low_stock_threshold
                FROM products
                WHERE is_active=1 AND stock_quantity <= low_stock_threshold
                ORDER BY stock_quantity ASC LIMIT 10
            """)
            low_stock = [dict(zip(['name','name_am','stock_quantity','low_stock_threshold'], r))
                         for r in cursor.fetchall()]

            # AI conversations yesterday
            cursor.execute(
                "SELECT COUNT(*) FROM ai_conversations WHERE created_at::date = %s",
                (yesterday,)
            )
            ai_conversations = cursor.fetchone()[0] or 0

            # Top 5 products by orders yesterday
            cursor.execute("""
                SELECT p.name, p.name_am, COUNT(oi.id) AS order_count
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                JOIN products p ON p.id = oi.product_id
                WHERE o.created_at::date = %s
                GROUP BY p.id, p.name, p.name_am
                ORDER BY order_count DESC LIMIT 5
            """, (yesterday,))
            top_products = [dict(zip(['name','name_am','order_count'], r))
                            for r in cursor.fetchall()]

            # Admin email from settings
            cursor.execute("SELECT value FROM settings WHERE key='admin_email'")
            row = cursor.fetchone()
            admin_email = (row[0] if row else None) or _os.environ.get('ADMIN_EMAIL', '')

            if not admin_email:
                app_ref.logger.warning("Daily digest: no admin_email configured in settings.")
                return

            data = {
                'date': yesterday.strftime('%B %d, %Y'),
                'new_orders': new_orders,
                'total_revenue': total_revenue,
                'pending_orders': pending_orders,
                'low_stock_products': low_stock,
                'ai_conversations': ai_conversations,
                'top_products': top_products,
            }

            subject = f"📊 SEMIRA Daily Digest — {yesterday.strftime('%b %d, %Y')}"
            ok = send_email(
                admin_email, subject,
                build_digest_html(data),
                build_digest_text(data)
            )
            if ok:
                app_ref.logger.info(f"Daily digest sent to {admin_email}")
            else:
                app_ref.logger.warning("Daily digest failed — check SMTP config.")
        except Exception as _e:
            app_ref.logger.error(f"Daily digest error: {_e}")


try:
    from apscheduler.schedulers.background import BackgroundScheduler
    import pytz

    _scheduler = BackgroundScheduler(timezone=pytz.utc)
    # Run at 05:00 UTC = 08:00 EAT (Ethiopia Africa/Addis_Ababa)
    _scheduler.add_job(
        func=_run_daily_digest,
        args=[app],
        trigger='cron',
        hour=5, minute=0,
        id='daily_digest',
        replace_existing=True,
        misfire_grace_time=3600,
    )
    _scheduler.start()
    atexit.register(lambda: _scheduler.shutdown(wait=False))
    app.logger.info("Daily digest scheduler started — runs at 05:00 UTC (08:00 EAT)")
except Exception as _sched_err:
    app.logger.warning(f"Scheduler could not start: {_sched_err}")


# ==================== 14. MAIN ENTRY POINT ====================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Semira Fashion Application')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    print(f"\nStarting Semira Fashion at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
