"""
AI Agent Route for SEMIRA FASHION
Powered by Groq llama-3.3-70b-versatile
Falls back to smart rule-based responses if no API key.
"""
import os
import re
import time
import logging
from flask import Blueprint, request, jsonify, session
from database.db import get_db
from routes.shared import WHATSAPP_NUMBER, FREE_SHIPPING_THRESHOLD, SHIPPING_COST
from extensions import limiter

# Top-level import with graceful fallback
try:
    from groq import Groq as _GroqClient
    _GROQ_AVAILABLE = True
except ImportError:
    _GroqClient = None
    _GROQ_AVAILABLE = False

ai_bp = Blueprint('ai', __name__)
logger = logging.getLogger(__name__)

# ── Simple in-process product cache (5-minute TTL) ──────────────────────────
_product_cache: dict = {}
_CACHE_TTL = 300  # seconds


def _cache_get(key: str):
    entry = _product_cache.get(key)
    if entry and (time.time() - entry['ts']) < _CACHE_TTL:
        return entry['val']
    return None


def _cache_set(key: str, val):
    _product_cache[key] = {'val': val, 'ts': time.time()}


# ── Status labels in all 3 languages ────────────────────────────────────────
STATUS_LABELS = {
    'pending':    {'am': '⏳ በመጠባበቅ ላይ',  'en': '⏳ Pending',    'ar': '⏳ قيد الانتظار'},
    'confirmed':  {'am': '✅ ተረጋግጧል',      'en': '✅ Confirmed',  'ar': '✅ مؤكد'},
    'processing': {'am': '🔧 በሂደት ላይ',     'en': '🔧 Processing', 'ar': '🔧 قيد المعالجة'},
    'shipped':    {'am': '🚚 ተላከ',          'en': '🚚 Shipped',    'ar': '🚚 تم الشحن'},
    'delivered':  {'am': '📦 ደረሰ',          'en': '📦 Delivered',  'ar': '📦 تم التسليم'},
    'cancelled':  {'am': '❌ ተሰርዟል',        'en': '❌ Cancelled',  'ar': '❌ ملغى'},
}

STORE_SYSTEM_PROMPT = """You are SEMIRA (ሰሚራ), the friendly AI shopping assistant for SEMIRA FASHION store.

STORE INFO:
- Name: SEMIRA FASHION (ሰሚራ ፋሽን)
- Location: Wollo Dessie Kutaber, Ethiopia (ወሎ ደሴ ኩታበር)
- Speciality: Women's and children's clothing (የሴቶች እና የልጆች ልብስ)
- WhatsApp: {whatsapp}
- Free shipping on orders over {free_ship} ETB
- Standard shipping: {ship_cost} ETB
- Payment: Cash on Delivery (COD)
- Return policy: 7 days for unused items

CURRENT PRODUCTS IN STORE:
{products}

CUSTOMER ORDER HISTORY:
{orders}

ORDER STATUS RULES:
- If the customer asks about their order, look at ORDER HISTORY above and report exactly.
- If they mention a specific order number (e.g. 20260626-HK3MF6), find it and give the status.
- If no orders found, tell them politely and suggest they log in or contact WhatsApp.
- Never invent order statuses — only use what is shown in ORDER HISTORY.

LANGUAGE RULE: Detect the language the user writes in and ALWAYS respond in the SAME language.
- Amharic → Amharic | English → English | Arabic → Arabic
- Keep responses SHORT (2-5 sentences), friendly, and helpful.
- For product recommendations, mention name and price.
- For unresolved issues, suggest WhatsApp: {whatsapp}
- Never make up products not in the list above.
- Use 🌸 or 👗 emojis occasionally.
- Sizes: XS–3XL for women, 0–14 years for children.
"""


def get_order_context(user_id, user_message: str, lang: str = 'am') -> str:
    """Fetch order history for the logged-in customer."""
    if not user_id:
        msgs = {
            'ar': "الزبون غير مسجل الدخول — لا يمكن عرض الطلبات.",
            'en': "Customer is not logged in — cannot retrieve orders.",
            'am': "ደንበኛ አልገቡም — ትዕዛዞችን ማሳየት አይቻልም።",
        }
        return msgs.get(lang, msgs['am'])

    try:
        db = get_db()
        cursor = db.cursor()

        order_num_match = re.search(r'\b(\d{8}-[A-Z0-9]{6})\b', user_message.upper())
        specific_order_num = order_num_match.group(1) if order_num_match else None

        if specific_order_num:
            cursor.execute("""
                SELECT o.order_number, o.status, o.payment_status, o.total,
                       o.shipping_city, o.tracking_number, o.estimated_delivery,
                       o.created_at, COUNT(oi.id) AS item_count
                FROM orders o
                LEFT JOIN order_items oi ON oi.order_id = o.id
                WHERE o.user_id = %s AND UPPER(o.order_number) = %s
                GROUP BY o.id LIMIT 1
            """, (user_id, specific_order_num))
        else:
            cursor.execute("""
                SELECT o.order_number, o.status, o.payment_status, o.total,
                       o.shipping_city, o.tracking_number, o.estimated_delivery,
                       o.created_at, COUNT(oi.id) AS item_count
                FROM orders o
                LEFT JOIN order_items oi ON oi.order_id = o.id
                WHERE o.user_id = %s
                GROUP BY o.id ORDER BY o.created_at DESC LIMIT 5
            """, (user_id,))

        rows = cursor.fetchall()
        if not rows:
            msgs = {
                'ar': "لا توجد طلبات مسجلة لهذا الحساب.",
                'en': "No orders found for this account.",
                'am': "በዚህ መለያ ምንም ትዕዛዝ አልተገኘም።",
            }
            return msgs.get(lang, msgs['am'])

        lines = []
        for r in rows:
            status_raw = r['status'] or 'pending'
            status_display = STATUS_LABELS.get(status_raw, {}).get(lang, status_raw)
            total = float(r['total'] or 0)
            date_str = r['created_at'].strftime('%Y-%m-%d') if r['created_at'] else '?'
            est_del = r['estimated_delivery'].strftime('%Y-%m-%d') if r['estimated_delivery'] else None
            tracking = r['tracking_number'] or None
            city = r['shipping_city'] or ''
            items = int(r['item_count'] or 0)
            line = (
                f"• Order #{r['order_number']} | Date: {date_str} | "
                f"Status: {status_display} | Payment: {r['payment_status'] or 'pending'} | "
                f"Total: {total:,.0f} ETB | Items: {items} | City: {city}"
            )
            if tracking:
                line += f" | Tracking: {tracking}"
            if est_del:
                line += f" | Est. Delivery: {est_del}"
            lines.append(line)

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"AI order context error: {e}")
        return "Could not retrieve order information at this time."


def get_product_context(user_message: str) -> str:
    """Query DB for relevant products — cached 5 min, with price filtering."""
    cache_key = f"prod:{user_message[:60]}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        db = get_db()
        cursor = db.cursor()

        # Extract price limit from message (e.g. "ለ1000 ብር", "under 500")
        price_match = re.search(r'(\d[\d,]*)', user_message.replace(',', ''))
        price_hint = int(price_match.group(1).replace(',', '')) if price_match else None

        # Keyword search — use up to 80 chars of message
        search_term = f"%{user_message[:80]}%"

        if price_hint and price_hint >= 50:
            # Filter by price when customer mentions a number ≥ 50 ETB
            cursor.execute("""
                SELECT p.name_am, p.name, p.price, p.stock_quantity, c.name_am as cat_am
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1
                  AND p.price <= %s
                  AND (p.name_am ILIKE %s OR p.name ILIKE %s
                       OR p.description ILIKE %s OR c.name_am ILIKE %s OR c.name ILIKE %s)
                ORDER BY p.price ASC, p.sales_count DESC
                LIMIT 6
            """, (price_hint, search_term, search_term, search_term, search_term, search_term))
        else:
            cursor.execute("""
                SELECT p.name_am, p.name, p.price, p.stock_quantity, c.name_am as cat_am
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1
                  AND (p.name_am ILIKE %s OR p.name ILIKE %s
                       OR p.description ILIKE %s OR c.name_am ILIKE %s OR c.name ILIKE %s)
                ORDER BY p.sales_count DESC
                LIMIT 6
            """, (search_term, search_term, search_term, search_term, search_term))

        keyword_products = cursor.fetchall()

        # Always include featured/popular products as fallback context
        pop_cache_key = "prod:popular"
        popular_products = _cache_get(pop_cache_key)
        if popular_products is None:
            cursor.execute("""
                SELECT p.name_am, p.name, p.price, p.stock_quantity, c.name_am as cat_am
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1
                ORDER BY p.is_featured DESC, p.sales_count DESC
                LIMIT 8
            """)
            popular_products = cursor.fetchall()
            _cache_set(pop_cache_key, popular_products)

        # Merge and deduplicate
        seen = set()
        all_products = []
        for p in list(keyword_products) + list(popular_products):
            key = p['name_am'] or p['name']
            if key not in seen:
                seen.add(key)
                all_products.append(p)
            if len(all_products) >= 10:
                break

        if not all_products:
            result = "No products currently available."
        else:
            lines = []
            for p in all_products:
                name = p['name_am'] or p['name'] or 'Unknown'
                price = float(p['price'])
                cat = p['cat_am'] or ''
                stock = int(p['stock_quantity'] or 0)
                avail = "In stock" if stock > 0 else "Out of stock"
                lines.append(f"- {name} ({cat}) — {price:,.0f} ETB | {avail}")
            result = "\n".join(lines)

        _cache_set(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"AI product context error: {e}")
        return "Women's and children's clothing available in various categories."


def smart_fallback(message: str, user_id=None, lang: str = 'am') -> str:
    """Rule-based fallback when no Groq key is set or API fails."""
    msg = message.lower()

    if any(w in msg for w in ['order', 'ትዕዛዝ', 'track', 'status', 'ሁኔታ', 'ደረሰ', 'where is']):
        if user_id:
            order_info = get_order_context(user_id, message, lang)
            if 'Order #' in order_info:
                return f"📦 የትዕዛዝ ሁኔታ:\n{order_info}\n\nተጨማሪ እርዳታ ከፈለጉ <a href='/orders'>ትዕዛዞቼ →</a>"
        return f"📦 ትዕዛዝዎን ለማወቅ <a href='/orders'>ትዕዛዞቼ →</a> ወይም WhatsApp: wa.me/{WHATSAPP_NUMBER}"

    if any(w in msg for w in ['hello', 'hi ', 'ሰላም', 'selam', 'hey', 'good', 'مرحبا', 'السلام']):
        return "ሰላም! 👋 ወደ SEMIRA FASHION እንኳን ደህና መጡ። ምን ልርዳዎ?"

    if any(w in msg for w in ['shipping', 'delivery', 'ማድረስ', 'ሰጪ', 'አድርስ', 'شحن', 'توصيل']):
        return f"🚚 ከ{FREE_SHIPPING_THRESHOLD:,} ብር በላይ ትዕዛዝ → ነጻ ማድረሻ! ከዚያ ያነሰ → {SHIPPING_COST} ብር ክፍያ።"

    if any(w in msg for w in ['return', 'exchange', 'መመለስ', 'ቅሬታ', 'refund', 'إرجاع']):
        return "↩️ ያልለበሱ ምርቶችን በ7 ቀን ውስጥ መመለስ ይቻላል። ለዝርዝር WhatsApp ያግኙን።"

    if any(w in msg for w in ['whatsapp', 'call', 'phone', 'ስልክ', 'ደውል', 'contact', 'اتصل', 'هاتف']):
        return f"📱 WhatsApp: wa.me/{WHATSAPP_NUMBER}"

    if any(w in msg for w in ['size', 'መጠን', 'ሳይዝ', 'fit', 'large', 'small', 'medium', 'مقاس']):
        return "👗 XS–3XL (ለሴቶች) እና 0–14 ዓመት (ለልጆች) ይገኛሉ።"

    if any(w in msg for w in ['product', 'ምርት', 'ልብስ', 'dress', 'ቀሚስ', 'price', 'ዋጋ', 'show', 'أ']):
        return "👗 <a href='/products'>ሁሉም ምርቶች →</a>"

    return f"ሰላም! 🌸 ምን ልርዳዎ? ምርቶች፣ ዋጋ፣ ትዕዛዝ ሁኔታ ሁሉን ልረዳ እችላለሁ። WhatsApp: wa.me/{WHATSAPP_NUMBER}"


def _log_conversation(message: str, reply: str, source: str, lang: str,
                       user_id=None, user_name: str = None, ip: str = None):
    """Persist a chat turn to ai_conversations table (best-effort, never raises)."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO ai_conversations
                (user_id, user_name, user_message, ai_reply, source, lang, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, user_name, message[:1000], reply[:2000], source, lang, ip))
        db.commit()
    except Exception as _e:
        logger.debug(f"AI conversation log failed (non-fatal): {_e}")


@ai_bp.route('/ai-chat', methods=['POST'])
@limiter.limit("20 per minute; 100 per hour")
def ai_chat():
    """Main AI chat endpoint — rate limited, Groq LLM with smart fallback."""
    message = ''
    try:
        data = request.get_json(silent=True) or {}
        message = (data.get('message') or '').strip()
        history = data.get('history') or []
        lang = session.get('lang', 'am')

        if not message:
            return jsonify({'success': False, 'error': 'Empty message'}), 400

        if len(message) > 500:
            message = message[:500]

        api_key = os.environ.get('GROQ_API_KEY', '').strip()
        user_id   = session.get('user_id')
        user_name = session.get('username') or session.get('full_name')
        ip        = request.remote_addr

        if not api_key or not _GROQ_AVAILABLE:
            reply = smart_fallback(message, user_id=user_id, lang=lang)
            _log_conversation(message, reply, 'fallback', lang, user_id, user_name, ip)
            return jsonify({'success': True, 'reply': reply, 'source': 'fallback'})

        products_context = get_product_context(message)
        orders_context = get_order_context(user_id, message, lang)

        system_content = STORE_SYSTEM_PROMPT.format(
            whatsapp=WHATSAPP_NUMBER,
            free_ship=FREE_SHIPPING_THRESHOLD,
            ship_cost=SHIPPING_COST,
            products=products_context,
            orders=orders_context,
        )

        messages = [{'role': 'system', 'content': system_content}]
        for h in history[-8:]:
            role = h.get('role', 'user')
            content = h.get('content', '')
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': str(content)[:300]})
        messages.append({'role': 'user', 'content': message})

        client = _GroqClient(api_key=api_key)
        completion = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=messages,
            max_tokens=400,
            temperature=0.7,
        )
        reply = completion.choices[0].message.content.strip()
        _log_conversation(message, reply, 'groq', lang, user_id, user_name, ip)
        return jsonify({'success': True, 'reply': reply, 'source': 'groq'})

    except Exception as e:
        logger.error(f"AI chat error: {e}")
        _lang = session.get('lang', 'am')
        _uid  = session.get('user_id')
        _name = session.get('username') or session.get('full_name')
        _ip   = request.remote_addr
        fallback = smart_fallback(message or '', user_id=_uid, lang=_lang)
        _log_conversation(message or '', fallback, 'error', _lang, _uid, _name, _ip)
        return jsonify({'success': True, 'reply': fallback, 'source': 'fallback'})


@ai_bp.route('/ai-chat/suggestions', methods=['GET'])
def ai_suggestions():
    """Return quick suggestion prompts based on language."""
    lang = session.get('lang', 'am')
    logged_in = bool(session.get('user_id'))

    base = {
        'am': {
            True:  ["የእኔ ትዕዛዝ ደረሰ?", "ለ1000 ብር ምን ቀሚስ አለ?", "ለልጆች ምን ምርቶች አሉ?", "ዋጋ እና ማድረሻ ሁኔታ"],
            False: ["ለ1000 ብር ምን ቀሚስ አለ?", "ለልጆች ምን ምርቶች አሉ?", "ዋጋ እና ማድረሻ ሁኔታ", "ስልክ ቁጥር ስጠኝ"],
        },
        'ar': {
            True:  ["ما حالة طلبي?", "ماذا يوجد تحت 1000 بر؟", "ملابس الأطفال المتوفرة", "معلومات الشحن"],
            False: ["ماذا يوجد تحت 1000 بر؟", "ملابس الأطفال المتوفرة", "معلومات الشحن والتوصيل", "تواصل معنا"],
        },
        'en': {
            True:  ["Where is my order?", "Show dresses under 1000 ETB", "What kids clothing do you have?", "Shipping info"],
            False: ["Show dresses under 1000 ETB", "What kids clothing do you have?", "Shipping & delivery info", "Contact us"],
        },
    }
    lang_suggestions = base.get(lang, base['am'])
    suggestions = lang_suggestions[logged_in]
    return jsonify({'success': True, 'suggestions': suggestions})
