"""
SEMIRA AI Agent — v2.0
Powered by Groq llama-3.3-70b-versatile with smart rule-based fallback.
Improvements: richer product context, Amharic keyword mapping, better caching,
smarter order lookup, and comprehensive fallback patterns.
"""
import os
import re
import time
import logging
from flask import Blueprint, request, jsonify, session
from database.db import get_db
from routes.shared import WHATSAPP_NUMBER, FREE_SHIPPING_THRESHOLD, SHIPPING_COST, USER_DISCOUNT_RATE
from extensions import limiter

try:
    from groq import Groq as _GroqClient
    _GROQ_AVAILABLE = True
except ImportError:
    _GroqClient = None
    _GROQ_AVAILABLE = False

ai_bp = Blueprint('ai', __name__)
logger = logging.getLogger(__name__)

# ── Cache ────────────────────────────────────────────────────────────────────
_cache: dict = {}
_CACHE_TTL_SHORT = 120   # 2 min  — per-query product results
_CACHE_TTL_LONG  = 600   # 10 min — popular/category lists


def _cget(key: str):
    e = _cache.get(key)
    return e['v'] if e and (time.time() - e['t']) < e['ttl'] else None


def _cset(key: str, val, ttl: int = _CACHE_TTL_SHORT):
    _cache[key] = {'v': val, 't': time.time(), 'ttl': ttl}


# ── Amharic / English keyword → category/field mapping ───────────────────────
# Maps common words users type to search signals
AMHARIC_CATEGORY_MAP = {
    # Dresses
    'ቀሚስ': 1,  'ቀሚሶች': 1,  'ቀሚስ ': 1,  'habesha': 1, 'ሀበሻ': 1,
    'dress': 1, 'gown': 1,   'ምሽት ቀሚስ': 1, 'ጀለቢያ': 1,
    # Tops & Shirts
    'ሸሚዝ': 2,  'ብሎዝ': 2,   'ቲሸርት': 2,  'ቶፕ': 2,
    'shirt': 2, 'blouse': 2, 'top': 2,    't-shirt': 2,
    # Trousers & Shorts
    'ሱሪ': 3,   'ቁምጣ': 3,   'trouser': 3, 'pant': 3, 'short': 3, 'jean': 3,
    'denim': 3, 'chino': 3,
    # Jackets & Knitwear
    'ጃኬት': 4,  'ካርዲጋን': 4, 'ሹራብ': 4,   'jacket': 4, 'coat': 4,
    'cardigan': 4, 'knitwear': 4, 'sweater': 4,
    # Underwear & Nightwear
    'ፒጃማ': 5,  'ናይትዌር': 5, 'pajama': 5, 'nightwear': 5, 'underwear': 5,
    # Baby
    'ሕፃን': 6,  'ህፃን': 6,   'ልጅ': 6,    'baby': 6, 'kid': 6,   'child': 6,
    'romper': 6, 'ሮምፐር': 6,
    # Activewear
    'ስፖርት': 7, 'ጂም': 7,    'ሌጊንስ': 7,  'sport': 7, 'gym': 7,
    'activewear': 7, 'hoodie': 7, 'legging': 7,
    # Traditional
    'ባህላዊ': 8, 'ነጠላ': 8,   'ጋቢ': 8,    'ኩታ': 8,   'ጥልፍ': 8,
    'netela': 8, 'gabi': 8,  'kuta': 8,  'traditional': 8, 'habesha kemis': 1,
}

AMHARIC_PRICE_WORDS = [
    'ዋጋ', 'ብር', 'etb', 'price', 'cost', 'ዋጋው', 'ምን ያህል', 'ስንት ብር',
    'cheap', 'affordable', 'ርካሽ', 'expensive', 'ውድ',
]

AMHARIC_ORDER_WORDS = [
    'ትዕዛዝ', 'ትዕዛዜ', 'order', 'ደረሰ', 'arrived', 'track',
    'ደረሰኝ', 'ተላከ', 'shipped', 'where is',
    'order number', 'ትዕዛዝ ቁጥር',
]

AMHARIC_SHIPPING_WORDS = [
    'ማጓጓዝ', 'ማድረስ', 'shipping', 'delivery', 'deliver', 'አድርስ',
    'free shipping', 'ነጻ ማጓጓዝ', 'ዋጋ ማጓጓዝ',
]

AMHARIC_RETURN_WORDS = [
    'መመለስ', 'ቅሬታ', 'refund', 'return', 'exchange', 'ልቀይር',
    'አልወደድኩም', 'ልቀይረው', 'ይቀየር', 'wrong', 'damaged',
]

AMHARIC_SIZE_WORDS = [
    'ሳይዝ', 'መጠን', 'size', 'fit', 'large', 'small', 'medium',
    'xl', 'xxl', 'xs', 'ትልቅ', 'ትንሽ', 'ምን ሳይዝ',
]

AMHARIC_GREETING_WORDS = [
    'ሰላም', 'selam', 'hello', 'hi', 'hey', 'good morning', 'good afternoon',
    'مرحبا', 'السلام',
]

AMHARIC_PAYMENT_WORDS = [
    'ክፍያ', 'payment', 'pay', 'ከፍያ', 'cash', 'ካርድ', 'card',
    'telebirr', 'ቴሌብር', 'cbe', 'bank', 'ባንክ',
]

AMHARIC_CONTACT_WORDS = [
    'whatsapp', 'ስልክ', 'phone', 'call', 'contact', 'ደውል',
    'አድራሻ', 'address', 'location', 'ቦታ', 'ሱቅ', 'store',
]

AMHARIC_DISCOUNT_WORDS = [
    'ቅናሽ', 'discount', 'sale', 'offer', 'promo', 'ልዩ', 'special',
    'ቀናሽ', 'reduced',
]

# ── Order status labels ──────────────────────────────────────────────────────
STATUS_LABELS = {
    'pending':    {'am': '⏳ በመጠባበቅ ላይ',  'en': '⏳ Pending',    'ar': '⏳ قيد الانتظار'},
    'confirmed':  {'am': '✅ ተረጋግጧል',      'en': '✅ Confirmed',  'ar': '✅ مؤكد'},
    'processing': {'am': '🔧 በሂደት ላይ',     'en': '🔧 Processing', 'ar': '🔧 قيد المعالجة'},
    'shipped':    {'am': '🚚 ተላከ',          'en': '🚚 Shipped',    'ar': '🚚 تم الشحن'},
    'delivered':  {'am': '📦 ደረሰ',          'en': '📦 Delivered',  'ar': '📦 تم التسليم'},
    'cancelled':  {'am': '❌ ተሰርዟል',        'en': '❌ Cancelled',  'ar': '❌ ملغى'},
}

PAYMENT_LABELS = {
    'pending':  {'am': '⏳ ያልተከፈለ',  'en': '⏳ Unpaid',    'ar': '⏳ غير مدفوع'},
    'paid':     {'am': '✅ ተከፍሏል',    'en': '✅ Paid',      'ar': '✅ مدفوع'},
    'cod':      {'am': '💵 በደረሰ ጊዜ', 'en': '💵 Cash on Delivery', 'ar': '💵 الدفع عند الاستلام'},
    'refunded': {'am': '↩️ ተመልሷል',   'en': '↩️ Refunded',  'ar': '↩️ مسترد'},
}

# ── System prompt (kept compact to fit Groq free-tier TPM limits) ─────────────
STORE_SYSTEM_PROMPT = """You are SEMIRA, AI assistant for SEMIRA FASHION (Ethiopian clothing store). Reply in the customer's language (Amharic/English/Arabic). Note: ነጻ ማጓጓዝ=free shipping, ዋጋ=price, ትዕዛዝ=order, ክፍያ=payment, ሳይዝ=size, ቅሬታ=return.

Store: Wollo, Dessie — Ethiopia | WA: {whatsapp} | Mon–Sat 8AM–8PM
Shipping: Free ≥{free_ship} ETB, else {ship_cost} ETB, 2–5 days. Payment: COD (pay on arrival). Discount: {discount_pct}% off when logged in. Returns: 7 days unused with tags.
Sizes: Women XS–3XL | Kids 0m–14yr.

PRODUCTS ({product_count}):
{products}

ORDERS: {orders}

Rules: (1) Only quote prices/products shown above—never invent. (2) If ORDERS has ⚠️ or "not logged in" → tell customer to log in at /login, never guess status. (3) If unsure → WhatsApp {whatsapp}. (4) Concise, warm, max 2 emojis."""


def _extract_price_range(msg: str):
    """Extract min/max price hints from user message."""
    msg_clean = msg.lower().replace(',', '')
    # "under 1000", "ከ1000 በታች", "below 1000"
    under = re.search(r'(?:under|below|ከ|less than|አነስ|ያነሰ)\s*(\d+)', msg_clean)
    # "above 2000", "over 2000", "ከ2000 በላይ"
    over = re.search(r'(?:above|over|ከ|more than|በላይ)\s*(\d+)', msg_clean)
    # "between 500 and 2000"
    between = re.search(r'between\s*(\d+)\s*and\s*(\d+)', msg_clean)
    # plain number like "ለ1000 ብር" or "1000 ETB"
    plain = re.search(r'(\d{3,})', msg_clean)

    if between:
        return int(between.group(1)), int(between.group(2))
    if under:
        return 0, int(under.group(1))
    if over:
        return int(over.group(1)), 999999
    if plain:
        n = int(plain.group(1))
        if n >= 50:
            return 0, n  # assume "under N" for product searches
    return None, None


def _detect_category(msg: str) -> int | None:
    """Return category_id if message matches a known category keyword."""
    msg_l = msg.lower()
    for kw, cat_id in AMHARIC_CATEGORY_MAP.items():
        if kw in msg_l:
            return cat_id
    return None


def get_product_context(user_message: str, lang: str = 'am') -> tuple[str, int]:
    """
    Return (formatted_product_string, product_count).
    Searches by keyword + category + price range. Falls back to popular items.
    """
    cache_key = f"prod:{lang}:{user_message[:80]}"
    cached = _cget(cache_key)
    if cached:
        return cached

    try:
        db = get_db()
        cursor = db.cursor()

        price_min, price_max = _extract_price_range(user_message)
        cat_id = _detect_category(user_message)
        search_term = f"%{user_message[:100]}%"

        # Language-specific column names (safe: only from fixed set, no user input)
        if lang == 'ar':
            name_col = 'p.name_ar'
            desc_col = 'p.description_ar'
            cat_col  = 'c.name_ar'
        elif lang == 'en':
            name_col = 'p.name_en'
            desc_col = 'p.description_en'
            cat_col  = 'c.name'
        else:  # 'am' default
            name_col = 'p.name_am'
            desc_col = 'p.description_am'
            cat_col  = 'c.name_am'

        keyword_products = []

        # Build query conditions
        base_conditions = "p.is_active = 1"
        params = []

        if cat_id:
            base_conditions += " AND p.category_id = %s"
            params.append(cat_id)

        if price_min is not None and price_max is not None and price_max < 999999:
            base_conditions += " AND p.price BETWEEN %s AND %s"
            params.extend([price_min, price_max])
        elif price_min is not None and price_min > 0:
            base_conditions += " AND p.price >= %s"
            params.append(price_min)

        # Keyword search — always search all name/desc fields for best recall
        kw_params = params + [search_term] * 7
        cursor.execute(f"""
            SELECT p.id, p.name_am, p.name_en, p.name_ar, p.price, p.compare_price,
                   p.stock_quantity, p.is_featured, p.is_new, p.material, p.color,
                   p.sizes, p.gender, {cat_col} as cat_name,
                   LEFT(COALESCE({desc_col}, p.description_am, p.description), 80) as desc_snippet,
                   p.thumbnail
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE {base_conditions}
              AND (p.name_am ILIKE %s OR p.name_en ILIKE %s OR p.name_ar ILIKE %s
                   OR p.description_am ILIKE %s OR p.description_en ILIKE %s
                   OR c.name_am ILIKE %s OR p.material ILIKE %s)
            ORDER BY p.is_featured DESC, p.sales_count DESC
            LIMIT 6
        """, kw_params)
        keyword_products = cursor.fetchall()

        # Popular products fallback (cached longer)
        pop_cache_key = f"pop:{lang}"
        popular = _cget(pop_cache_key)
        if popular is None:
            cursor.execute(f"""
                SELECT p.id, p.name_am, p.name_en, p.name_ar, p.price, p.compare_price,
                       p.stock_quantity, p.is_featured, p.is_new, p.sizes,
                       {cat_col} as cat_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1
                ORDER BY p.is_featured DESC, p.is_new DESC, p.sales_count DESC
                LIMIT 6
            """)
            popular = cursor.fetchall()
            _cset(pop_cache_key, popular, ttl=_CACHE_TTL_LONG)

        # Merge, deduplicate — cap at 8 total
        seen_ids = set()
        all_products = []
        for p in list(keyword_products) + list(popular):
            if p['id'] not in seen_ids:
                seen_ids.add(p['id'])
                all_products.append(p)
            if len(all_products) >= 8:
                break

        if not all_products:
            result = "No products found."
            _cset(cache_key, (result, 0))
            return result, 0

        lines = []
        for p in all_products:
            if lang == 'am':
                name = p['name_am'] or p['name_en'] or 'Unknown'
            elif lang == 'ar':
                name = p['name_ar'] or p['name_en'] or 'Unknown'
            else:
                name = p['name_en'] or p['name_am'] or 'Unknown'

            price = float(p['price'])
            compare = float(p['compare_price']) if p['compare_price'] else None
            stock = int(p['stock_quantity'] or 0)
            avail = 'in stock' if stock > 0 else 'OUT OF STOCK'
            sizes = p.get('sizes') or ''

            line = f"- {name}: {price:,.0f} ETB"
            if compare and compare > price:
                line += f" (was {compare:,.0f})"
            line += f" [{avail}]"
            if sizes:
                line += f" sizes:{sizes}"
            line += f" → /products/{p['id']}"
            lines.append(line)

        result = "\n".join(lines)
        count = len(all_products)
        _cset(cache_key, (result, count), ttl=_CACHE_TTL_SHORT)
        return result, count

    except Exception as e:
        logger.error(f"AI product context error: {e}")
        return "Ethiopian women's and children's fashion available.", 0


def get_order_context(user_id, user_message: str, lang: str = 'am') -> str:
    """Fetch order history with item details for logged-in customers."""
    if not user_id:
        return {
            'ar': "الزبون غير مسجل الدخول — استخدم /login للدخول.",
            'en': "You're not logged in. Please log in at /login to view your orders.",
            'am': "ወደ መለያዎ አልገቡም። ትዕዛዞችን ለማየት /login ላይ ይግቡ።",
        }.get(lang, "Not logged in.")

    try:
        db = get_db()
        cursor = db.cursor()

        # Detect specific order number
        order_num_match = re.search(r'\b(\d{8}-[A-Z0-9]{6})\b', user_message.upper())
        specific_order_num = order_num_match.group(1) if order_num_match else None

        if specific_order_num:
            cursor.execute("""
                SELECT o.id, o.order_number, o.status, o.payment_status, o.total,
                       o.shipping_city, o.tracking_number, o.estimated_delivery,
                       o.created_at, o.notes
                FROM orders o
                WHERE o.user_id = %s AND UPPER(o.order_number) = %s
                LIMIT 1
            """, (user_id, specific_order_num))
        else:
            cursor.execute("""
                SELECT o.id, o.order_number, o.status, o.payment_status, o.total,
                       o.shipping_city, o.tracking_number, o.estimated_delivery,
                       o.created_at, o.notes
                FROM orders o
                WHERE o.user_id = %s
                ORDER BY o.created_at DESC
                LIMIT 5
            """, (user_id,))

        orders = cursor.fetchall()
        if not orders:
            return {
                'ar': "لا توجد طلبات بعد. تسوق الآن على /products",
                'en': "No orders yet. Start shopping at /products",
                'am': "ምንም ትዕዛዝ የለም። /products ላይ ይጀምሩ",
            }.get(lang, "No orders found.")

        lines = []
        for o in orders:
            # Fetch items for this order
            cursor.execute("""
                SELECT oi.quantity, oi.price_at_time,
                       COALESCE(p.name_am, p.name_en, p.name) as product_name
                FROM order_items oi
                LEFT JOIN products p ON p.id = oi.product_id
                WHERE oi.order_id = %s
                LIMIT 5
            """, (o['id'],))
            items = cursor.fetchall()

            status_raw = o['status'] or 'pending'
            pay_raw    = o['payment_status'] or 'pending'
            status_lbl = STATUS_LABELS.get(status_raw, {}).get(lang, status_raw)
            pay_lbl    = PAYMENT_LABELS.get(pay_raw, {}).get(lang, pay_raw)
            total      = float(o['total'] or 0)
            date_str   = o['created_at'].strftime('%Y-%m-%d') if o['created_at'] else '?'
            est_del    = o['estimated_delivery'].strftime('%Y-%m-%d') if o['estimated_delivery'] else 'N/A'
            city       = o['shipping_city'] or 'N/A'
            tracking   = o['tracking_number'] or 'Not assigned yet'

            items_str = ', '.join(
                f"{i['product_name']} x{i['quantity']} ({float(i['price_at_time']):,.0f} ETB)"
                for i in items
            ) if items else 'N/A'

            lines.append(
                f"Order #{o['order_number']}\n"
                f"  Date: {date_str} | Status: {status_lbl} | Payment: {pay_lbl}\n"
                f"  Total: {total:,.0f} ETB | City: {city}\n"
                f"  Tracking: {tracking} | Est. Delivery: {est_del}\n"
                f"  Items: {items_str}"
            )

        return "\n\n".join(lines)

    except Exception as e:
        logger.error(f"AI order context error: {e}")
        return "Could not load order information at this time."


def smart_fallback(message: str, user_id=None, lang: str = 'am', products_ctx: str = '') -> str:
    """Comprehensive rule-based fallback — handles 20+ intent patterns."""
    msg = message.lower().strip()

    def _has(*words):
        return any(w in msg for w in words)

    # Greeting
    if _has(*AMHARIC_GREETING_WORDS) and len(msg) < 30:
        greets = {
            'am': f"ሰላም! 👗 እኔ ሰሚራ ነኝ — የ SEMIRA FASHION AI አስተናጋጅ።\n"
                  f"ምን ልርዳዎ? ምርቶች ፣ ዋጋ ፣ ትዕዛዝ ሁኔታ ፣ ሳይዝ — ሁሉ ልረዳ እችላለሁ።",
            'en': f"Hello! 👗 I'm SEMIRA, your AI fashion assistant.\n"
                  f"I can help with products, prices, orders, sizing, and more!",
            'ar': f"أهلاً! 👗 أنا سيميرا، مساعدتك الذكية في SEMIRA FASHION.\n"
                  f"يمكنني مساعدتك في المنتجات والأسعار والطلبات والمقاسات.",
        }
        return greets.get(lang, greets['am'])

    # Order tracking — always show order context if logged in, otherwise prompt login
    if _has(*AMHARIC_ORDER_WORDS):
        if user_id:
            order_info = get_order_context(user_id, message, lang)
            prefix = {
                'am': "📦 የትዕዛዝ ሁኔታዎ:",
                'en': "📦 Your order details:",
                'ar': "📦 تفاصيل طلبك:",
            }.get(lang, "📦 Order info:")
            suffix = {
                'am': "ሁሉም ትዕዛዞች ለማየት → /orders",
                'en': "View all orders → /orders",
                'ar': "عرض جميع الطلبات → /orders",
            }.get(lang, "View orders → /orders")
            return f"{prefix}\n\n{order_info}\n\n{suffix}"
        # Not logged in
        return {
            'am': f"📦 ትዕዛዝዎን ለማወቅ ወደ /login ይግቡ ፣ ወይም WhatsApp ያግኙን: wa.me/{WHATSAPP_NUMBER}",
            'en': f"📦 Please log in at /login to track your order, or contact WhatsApp: wa.me/{WHATSAPP_NUMBER}",
            'ar': f"📦 يرجى تسجيل الدخول على /login لتتبع طلبك، أو تواصل عبر واتساب: wa.me/{WHATSAPP_NUMBER}",
        }.get(lang, f"Log in at /login or WhatsApp: wa.me/{WHATSAPP_NUMBER}")

    # Shipping
    if _has(*AMHARIC_SHIPPING_WORDS):
        return {
            'am': f"🚚 ከ{FREE_SHIPPING_THRESHOLD:,} ብር በላይ ትዕዛዝ → ነጻ ማጓጓዝ!\n"
                  f"ከዚያ ያነሰ → {SHIPPING_COST} ብር ክፍያ። ዲሊቨሪ 2–5 የሥራ ቀናት።",
            'en': f"🚚 Free shipping on orders ≥ {FREE_SHIPPING_THRESHOLD:,} ETB!\n"
                  f"Standard shipping: {SHIPPING_COST} ETB. Delivery in 2–5 business days.",
            'ar': f"🚚 شحن مجاني على الطلبات ≥ {FREE_SHIPPING_THRESHOLD:,} بر!\n"
                  f"الشحن العادي: {SHIPPING_COST} بر. التوصيل خلال 2–5 أيام عمل.",
        }.get(lang, f"Free shipping ≥ {FREE_SHIPPING_THRESHOLD:,} ETB. Standard: {SHIPPING_COST} ETB.")

    # Returns
    if _has(*AMHARIC_RETURN_WORDS):
        return {
            'am': f"↩️ ያልለበሱ ምርቶችን በ7 ቀን ውስጥ መመለስ ወይም መቀየር ይቻላል።\n"
                  f"ለዝርዝር WhatsApp ያግኙን: wa.me/{WHATSAPP_NUMBER}",
            'en': f"↩️ Unused items with tags can be returned/exchanged within 7 days.\n"
                  f"Contact WhatsApp: wa.me/{WHATSAPP_NUMBER}",
            'ar': f"↩️ يمكن إرجاع أو استبدال المنتجات غير المستخدمة خلال 7 أيام.\n"
                  f"تواصل عبر واتساب: wa.me/{WHATSAPP_NUMBER}",
        }.get(lang, f"7-day return policy. WhatsApp: wa.me/{WHATSAPP_NUMBER}")

    # Size guide
    if _has(*AMHARIC_SIZE_WORDS):
        return {
            'am': "👗 ሳይዝ መረጃ:\n• ሴቶች: XS, S, M, L, XL, XXL, 3XL\n• ልጆች: 0–14 ዓመት\n• ባህላዊ ልብሶች: One Size / ካስቶም\n\nለዝርዝር WhatsApp: wa.me/" + str(WHATSAPP_NUMBER),
            'en': "👗 Size guide:\n• Women: XS, S, M, L, XL, XXL, 3XL\n• Kids: 0–14 years\n• Traditional: One Size / Custom\n\nFor help: wa.me/" + str(WHATSAPP_NUMBER),
            'ar': "👗 دليل المقاسات:\n• نساء: XS, S, M, L, XL, XXL, 3XL\n• أطفال: 0–14 سنة\n• التقليدية: مقاس واحد / مخصص",
        }.get(lang, "Women: XS–3XL. Kids: 0–14yr.")

    # Payment
    if _has(*AMHARIC_PAYMENT_WORDS):
        return {
            'am': f"💵 ክፍያ: Cash on Delivery (COD) — ምርቱ ሲደርስ ይከፍላሉ።\n"
                  f"ወደ መለያ ከገቡ {int(USER_DISCOUNT_RATE * 100)}% ቅናሽ ያገኛሉ!",
            'en': f"💵 Payment: Cash on Delivery (COD) — pay when your order arrives.\n"
                  f"Log in to get {int(USER_DISCOUNT_RATE * 100)}% discount on all orders!",
            'ar': f"💵 الدفع: الدفع عند الاستلام (COD) — ادفع عند وصول طلبك.\n"
                  f"سجل الدخول للحصول على خصم {int(USER_DISCOUNT_RATE * 100)}%!",
        }.get(lang, "Cash on Delivery. Log in for discount!")

    # Discount inquiry
    if _has(*AMHARIC_DISCOUNT_WORDS):
        return {
            'am': f"🎉 አሁን ያሉ ቅናሾች:\n• ወደ መለያ ሲገቡ {int(USER_DISCOUNT_RATE * 100)}% ቅናሽ\n"
                  f"• ከ{FREE_SHIPPING_THRESHOLD:,} ብር በላይ → ነጻ ማጓጓዝ\n• /products ላይ ያሉ ምርቶች ቅናሽ ያላቸው ይፈልጉ",
            'en': f"🎉 Current offers:\n• {int(USER_DISCOUNT_RATE * 100)}% discount when logged in\n"
                  f"• Free shipping on orders ≥ {FREE_SHIPPING_THRESHOLD:,} ETB\n• Check /products for sale items",
            'ar': f"🎉 العروض الحالية:\n• خصم {int(USER_DISCOUNT_RATE * 100)}% عند تسجيل الدخول\n"
                  f"• شحن مجاني على الطلبات ≥ {FREE_SHIPPING_THRESHOLD:,} بر",
        }.get(lang, "Discounts available when logged in!")

    # Contact / Location
    if _has(*AMHARIC_CONTACT_WORDS):
        return {
            'am': f"📱 WhatsApp: wa.me/{WHATSAPP_NUMBER}\n📍 አድራሻ: ወሎ፣ ደሴ፣ ኩታበር — ኢትዮጵያ\n🕐 ሰዓት: ሰኞ–ቅዳሜ 8AM–8PM",
            'en': f"📱 WhatsApp: wa.me/{WHATSAPP_NUMBER}\n📍 Location: Wollo, Dessie, Kutaber — Ethiopia\n🕐 Hours: Mon–Sat 8AM–8PM",
            'ar': f"📱 واتساب: wa.me/{WHATSAPP_NUMBER}\n📍 العنوان: وولو، ديسي، كوتابر — إثيوبيا\n🕐 الساعات: الإثنين–السبت 8ص–8م",
        }.get(lang, f"WhatsApp: wa.me/{WHATSAPP_NUMBER} | Wollo, Dessie, Kutaber")

    # Category/product browse — show real product data if available
    cat_id = _detect_category(msg)
    price_min, price_max = _extract_price_range(msg)
    is_product_query = cat_id or _has(*AMHARIC_PRICE_WORDS) or \
        any(w in msg for w in ('product', 'ምርት', 'ልብስ', 'ምን አለ', 'አለ?', 'አለ '))

    if is_product_query:
        # If product context was passed in, show it directly
        if products_ctx and 'No products' not in products_ctx and len(products_ctx) > 20:
            intro = {
                'am': "👗 እነዚህ ምርቶች አሉ:",
                'en': "👗 Here are our products:",
                'ar': "👗 إليك منتجاتنا:",
            }.get(lang, "👗 Our products:")
            browse_url = "/products"
            if cat_id:
                browse_url += f"?category={cat_id}"
            if price_max and price_max < 999999:
                sep = '&' if '?' in browse_url else '?'
                browse_url += f"{sep}max_price={price_max}"
            footer = {
                'am': f"ሁሉም ምርቶች: {browse_url}",
                'en': f"See all: {browse_url}",
                'ar': f"عرض الكل: {browse_url}",
            }.get(lang, f"Browse: {browse_url}")
            return f"{intro}\n{products_ctx}\n\n{footer}"

        # No context — send to products page
        base_url = "/products"
        if cat_id:
            base_url += f"?category={cat_id}"
        if price_max and price_max < 999999:
            sep = '&' if '?' in base_url else '?'
            base_url += f"{sep}max_price={price_max}"
        return {
            'am': f"👗 ምርቶቻችንን ለማየት: {base_url}",
            'en': f"👗 Browse our products: {base_url}",
            'ar': f"👗 تصفح منتجاتنا: {base_url}",
        }.get(lang, f"Browse: {base_url}")

    # Default
    return {
        'am': f"ሰሚራ AI ለማገልገል ዝግጁ ነኝ! 🌸\n"
              f"ስለ ምርቶች፣ ዋጋ፣ ትዕዛዝ ሁኔታ፣ ሳይዝ፣ ወይም ማጓጓዝ ይጠይቁ።",
        'en': f"I'm here to help! Ask about products, prices, orders, sizes, or delivery. 🌸",
        'ar': f"أنا هنا للمساعدة! اسألني عن المنتجات والأسعار وطلباتك والمقاسات. 🌸",
    }.get(lang, f"How can I help? WhatsApp: wa.me/{WHATSAPP_NUMBER}")


def _log_conversation(message: str, reply: str, source: str, lang: str,
                       user_id=None, user_name: str = None, ip: str = None):
    """Persist chat turn to ai_conversations table."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO ai_conversations
                (user_id, user_name, user_message, ai_reply, source, lang, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, user_name, message[:1000], reply[:3000], source, lang, ip))
        db.commit()
    except Exception as e:
        logger.debug(f"AI conversation log failed (non-fatal): {e}")


# ── Main chat route ──────────────────────────────────────────────────────────
@ai_bp.route('/ai-chat', methods=['POST'])
@limiter.limit("25 per minute; 150 per hour")
def ai_chat():
    """Main AI chat endpoint — Groq LLM with comprehensive smart fallback."""
    message = ''
    products_ctx = ''   # ensure available in except scope
    try:
        data     = request.get_json(silent=True) or {}
        message  = (data.get('message') or '').strip()
        history  = data.get('history') or []
        lang     = session.get('lang', 'am')
        user_id  = session.get('user_id')
        user_name = session.get('username') or session.get('full_name')
        ip       = request.remote_addr

        if not message:
            return jsonify({'success': False, 'error': 'Empty message'}), 400

        message = message[:400]  # cap to keep tokens low

        api_key = os.environ.get('GROQ_API_KEY', '').strip()

        # If env var empty, try DB settings (survives server restarts)
        if not api_key and _GROQ_AVAILABLE:
            try:
                _db = get_db()
                _cur = _db.cursor()
                _cur.execute("SELECT value FROM settings WHERE key = %s", ('groq_api_key',))
                _row = _cur.fetchone()
                if _row and _row['value']:
                    api_key = _row['value'].strip()
                    os.environ['GROQ_API_KEY'] = api_key  # cache for next request
            except Exception:
                pass

        # Detect intent once — used by both fallback and LLM path
        msg_lower = message.lower()
        is_order_intent = any(w in msg_lower for w in AMHARIC_ORDER_WORDS)

        # Always fetch product context (cached, fast)
        products_ctx, product_count = get_product_context(message, lang)

        # Fetch order context only when message has order intent
        if is_order_intent:
            if user_id:
                orders_ctx = get_order_context(user_id, message, lang)
            else:
                # Not logged in — tell AI clearly so it directs them to /login
                orders_ctx = {
                    'am': "⚠️ ደንበኛው ወደ ስርዓቱ አልገቡም። ትዕዛዝ ለማየት /login ላይ መግባት አለባቸው። ትዕዛዝ ሁኔታ አታስብ — ፍጹም አታፈጥር።",
                    'en': "⚠️ Customer is NOT logged in. They must log in at /login to view orders. Do NOT guess or invent any order status.",
                    'ar': "⚠️ العميل غير مسجل الدخول. يجب تسجيل الدخول على /login. لا تخترع أي معلومات عن الطلب.",
                }.get(lang, "⚠️ NOT logged in — tell customer to log in at /login. Never invent order status.")
        else:
            orders_ctx = {
                'am': "ትዕዛዝ ጥያቄ አልተጠየቀም።",
                'en': "No order query in this message.",
                'ar': "لم يُطلب معلومات طلب.",
            }.get(lang, "No order query.")

        if not api_key or not _GROQ_AVAILABLE:
            reply = smart_fallback(message, user_id=user_id, lang=lang, products_ctx=products_ctx)
            _log_conversation(message, reply, 'fallback', lang, user_id, user_name, ip)
            return jsonify({'success': True, 'reply': reply, 'source': 'fallback'})

        # Build system prompt
        system_content = STORE_SYSTEM_PROMPT.format(
            whatsapp=WHATSAPP_NUMBER,
            free_ship=f"{FREE_SHIPPING_THRESHOLD:,}",
            ship_cost=f"{SHIPPING_COST:,}",
            discount_pct=int(USER_DISCOUNT_RATE * 100),
            product_count=product_count,
            products=products_ctx,
            orders=orders_ctx,
        )

        # Build message history (last 5 turns to save tokens)
        messages = [{'role': 'system', 'content': system_content}]
        for h in history[-5:]:
            role    = h.get('role', 'user')
            content = h.get('content', '')
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': str(content)[:200]})
        messages.append({'role': 'user', 'content': message})

        client = _GroqClient(api_key=api_key, timeout=15.0)
        completion = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=messages,
            max_tokens=380,
            temperature=0.25,
            top_p=0.9,
        )
        reply = completion.choices[0].message.content.strip()
        _log_conversation(message, reply, 'groq', lang, user_id, user_name, ip)
        return jsonify({'success': True, 'reply': reply, 'source': 'groq'})

    except Exception as e:
        logger.error(f"AI chat error: {e}")
        _lang     = session.get('lang', 'am')
        _uid      = session.get('user_id')
        _name     = session.get('username') or session.get('full_name')
        _ip       = request.remote_addr
        fallback  = smart_fallback(message or '', user_id=_uid, lang=_lang, products_ctx=products_ctx)
        _log_conversation(message or '', fallback, 'error', _lang, _uid, _name, _ip)
        return jsonify({'success': True, 'reply': fallback, 'source': 'fallback'})


# ── Suggestions route ─────────────────────────────────────────────────────────
@ai_bp.route('/ai-chat/suggestions', methods=['GET'])
def ai_suggestions():
    """Return smart suggestion chips based on language + login state."""
    lang      = session.get('lang', 'am')
    logged_in = bool(session.get('user_id'))

    base = {
        'am': {
            True: [
                "የእኔ ትዕዛዝ ሁኔታ ምንድን ነው?",
                "ለ2000 ብር ምን ቀሚሶች አሉ?",
                "ለሕፃናት ምን ምርቶች አሉ?",
                "ሀበሻ ቀሚስ ዋጋ ስንት ነው?",
            ],
            False: [
                "ለ1500 ብር ምን ቀሚሶች አሉ?",
                "ሀበሻ ቀሚስ ዋጋ ስንት ነው?",
                "ለልጆች ምን ምርቶች አሉ?",
                "ነጻ ማጓጓዝ ሁኔታ ምንድን ነው?",
            ],
        },
        'en': {
            True: [
                "Where is my order?",
                "Show me dresses under 2000 ETB",
                "Do you have traditional wear?",
                "What sizes are available?",
            ],
            False: [
                "Show dresses under 2000 ETB",
                "Do you have Habesha Kemis?",
                "What kids clothing is available?",
                "How does shipping work?",
            ],
        },
        'ar': {
            True: [
                "ما حالة طلبي؟",
                "أريد فستاناً بأقل من 2000 بر",
                "هل يوجد ملابس تقليدية؟",
                "معلومات الشحن والتوصيل",
            ],
            False: [
                "أريد فستاناً بأقل من 2000 بر",
                "هل يوجد هبشا كيميس؟",
                "ملابس الأطفال المتوفرة",
                "سياسة الشحن والإرجاع",
            ],
        },
    }

    lang_data   = base.get(lang, base['am'])
    suggestions = lang_data.get(logged_in, lang_data[False])
    return jsonify({'success': True, 'suggestions': suggestions})
