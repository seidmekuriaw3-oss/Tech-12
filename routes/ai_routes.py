"""
AI Agent Route for SEMIRA FASHION
Powered by Groq llama-3.3-70b-versatile
Falls back to smart rule-based responses if no API key.
"""
import os
import re
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from database.db import get_db
from routes.shared import WHATSAPP_NUMBER, FREE_SHIPPING_THRESHOLD, SHIPPING_COST

ai_bp = Blueprint('ai', __name__)
logger = logging.getLogger(__name__)

# Status labels in all 3 languages
STATUS_LABELS = {
    'pending':    {'am': '⏳ በመጠባበቅ ላይ',    'en': '⏳ Pending',    'ar': '⏳ قيد الانتظار'},
    'confirmed':  {'am': '✅ ተረጋግጧል',        'en': '✅ Confirmed',  'ar': '✅ مؤكد'},
    'processing': {'am': '🔧 በሂደት ላይ',       'en': '🔧 Processing', 'ar': '🔧 قيد المعالجة'},
    'shipped':    {'am': '🚚 ተላከ',            'en': '🚚 Shipped',    'ar': '🚚 تم الشحن'},
    'delivered':  {'am': '📦 ደረሰ',            'en': '📦 Delivered',  'ar': '📦 تم التسليم'},
    'cancelled':  {'am': '❌ ተሰርዟል',          'en': '❌ Cancelled',  'ar': '❌ ملغى'},
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
- If the customer asks about their order (e.g. "ትዕዛዝ ደረሰ?", "my order status", "where is my order"), look at the ORDER HISTORY above and report exactly.
- If they mention a specific order number (e.g. 20260626-HK3MF6), find it in the order history and give the status.
- If no orders are found for this customer, tell them politely and suggest they log in or contact WhatsApp.
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
    """Fetch order history for the logged-in customer, optionally filtered by order number."""
    if not user_id:
        if lang == 'ar':
            return "الزبون غير مسجل الدخول — لا يمكن عرض الطلبات."
        elif lang == 'en':
            return "Customer is not logged in — cannot retrieve orders."
        else:
            return "ደንበኛ አልገቡም — ትዕዛዞችን ማሳየት አይቻልም።"

    try:
        db = get_db()
        cursor = db.cursor()

        # Check if a specific order number is mentioned
        order_num_match = re.search(r'\b(\d{8}-[A-Z0-9]{6})\b', user_message.upper())
        specific_order_num = order_num_match.group(1) if order_num_match else None

        if specific_order_num:
            cursor.execute("""
                SELECT o.order_number, o.status, o.payment_status, o.total,
                       o.shipping_city, o.tracking_number, o.estimated_delivery,
                       o.created_at,
                       COUNT(oi.id) AS item_count
                FROM orders o
                LEFT JOIN order_items oi ON oi.order_id = o.id
                WHERE o.user_id = %s AND UPPER(o.order_number) = %s
                GROUP BY o.id
                LIMIT 1
            """, (user_id, specific_order_num))
        else:
            cursor.execute("""
                SELECT o.order_number, o.status, o.payment_status, o.total,
                       o.shipping_city, o.tracking_number, o.estimated_delivery,
                       o.created_at,
                       COUNT(oi.id) AS item_count
                FROM orders o
                LEFT JOIN order_items oi ON oi.order_id = o.id
                WHERE o.user_id = %s
                GROUP BY o.id
                ORDER BY o.created_at DESC
                LIMIT 5
            """, (user_id,))

        rows = cursor.fetchall()
        if not rows:
            if lang == 'ar':
                return "لا توجد طلبات مسجلة لهذا الحساب."
            elif lang == 'en':
                return "No orders found for this account."
            else:
                return "በዚህ መለያ ምንም ትዕዛዝ አልተገኘም።"

        lines = []
        for r in rows:
            status_raw = r['status'] or 'pending'
            status_display = STATUS_LABELS.get(status_raw, {}).get(lang, status_raw)
            pay_status = r['payment_status'] or 'unpaid'
            total = float(r['total'] or 0)
            date_str = r['created_at'].strftime('%Y-%m-%d') if r['created_at'] else '?'
            est_del = r['estimated_delivery'].strftime('%Y-%m-%d') if r['estimated_delivery'] else None
            tracking = r['tracking_number'] or None
            city = r['shipping_city'] or ''
            items = int(r['item_count'] or 0)

            line = (
                f"• Order #{r['order_number']} | Date: {date_str} | "
                f"Status: {status_display} | Payment: {pay_status} | "
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
    """Query DB for relevant products and return formatted context."""
    try:
        db = get_db()
        cursor = db.cursor()

        # Extract price hints from message
        price_match = re.search(r'(\d+)', user_message)
        price_hint = int(price_match.group(1)) if price_match else None

        # Search by keyword
        search_term = f"%{user_message[:40]}%"
        cursor.execute("""
            SELECT p.name_am, p.name, p.price, p.stock_quantity, c.name_am as cat_am
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
            AND (p.name_am ILIKE %s OR p.name ILIKE %s OR p.description ILIKE %s
                 OR c.name_am ILIKE %s OR c.name ILIKE %s)
            ORDER BY p.sales_count DESC
            LIMIT 6
        """, (search_term, search_term, search_term, search_term, search_term))
        keyword_products = cursor.fetchall()

        # Also get featured/popular products for general context
        cursor.execute("""
            SELECT p.name_am, p.name, p.price, p.stock_quantity, c.name_am as cat_am
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
            ORDER BY p.is_featured DESC, p.sales_count DESC
            LIMIT 8
        """)
        popular_products = cursor.fetchall()

        # Merge, deduplicate
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
            return "No products currently available."

        lines = []
        for p in all_products:
            name = p['name_am'] or p['name'] or 'Unknown'
            price = float(p['price'])
            cat = p['cat_am'] or ''
            stock = int(p['stock_quantity'] or 0)
            avail = "In stock" if stock > 0 else "Out of stock"
            lines.append(f"- {name} ({cat}) — {price:,.0f} ETB | {avail}")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"AI product context error: {e}")
        return "Women's and children's clothing available in various categories."


def smart_fallback(message: str, user_id=None, lang: str = 'am') -> str:
    """Rule-based fallback when no Groq key is set."""
    msg = message.lower()

    # Order status — query DB directly even in fallback mode
    if any(w in msg for w in ['order', 'ትዕዛዝ', 'track', 'status', 'ሁኔታ', 'ደረሰ', 'ዘፈን', 'where is']):
        if user_id:
            order_info = get_order_context(user_id, message, lang)
            if 'Order #' in order_info:
                return f"📦 የትዕዛዝ ሁኔታ:\n{order_info}\n\nተጨማሪ እርዳታ ከፈለጉ <a href='/orders' style='color:#1a7a4a;font-weight:600'>ትዕዛዞቼ →</a>"
        return f"📦 ትዕዛዝዎን ለማወቅ <a href='/orders' style='color:#1a7a4a;font-weight:600'>ትዕዛዞቼ →</a> ወይም WhatsApp: wa.me/{WHATSAPP_NUMBER}"

    # Greetings
    if any(w in msg for w in ['hello', 'hi ', 'ሰላም', 'selam', 'hey', 'good']):
        return "ሰላም! 👋 ወደ SEMIRA FASHION እንኳን ደህና መጡ። ምን ልርዳዎ?"

    # Shipping
    if any(w in msg for w in ['shipping', 'delivery', 'ማድረስ', 'ሰጪ', 'አድርስ']):
        return f"🚚 ከ{FREE_SHIPPING_THRESHOLD:,} ብር በላይ ትዕዛዝ → ነጻ ማድረሻ! ከዚያ ያነሰ → {SHIPPING_COST} ብር ክፍያ።"

    # Return/exchange
    if any(w in msg for w in ['return', 'exchange', 'መመለስ', 'ቅሬታ', 'refund']):
        return "↩️ ያልለበሱ ምርቶችን በ7 ቀን ውስጥ መመለስ ይቻላል። ለዝርዝር WhatsApp ያግኙን።"

    # WhatsApp/contact
    if any(w in msg for w in ['whatsapp', 'call', 'phone', 'ስልክ', 'ደውል', 'contact']):
        return f"📱 WhatsApp: wa.me/{WHATSAPP_NUMBER}"

    # Size
    if any(w in msg for w in ['size', 'መጠን', 'ሳይዝ', 'fit', 'large', 'small', 'medium']):
        return "👗 XS–3XL (ለሴቶች) እና 0–14 ዓመት (ለልጆች) ይገኛሉ።"

    # Products
    if any(w in msg for w in ['product', 'ምርት', 'ልብስ', 'dress', 'ቀሚስ', 'price', 'ዋጋ', 'show', 'አሳይ']):
        return "👗 <a href='/products' style='color:#1a7a4a;font-weight:600'>ሁሉም ምርቶች →</a>"

    return f"ሰላም! 🌸 ምን ልርዳዎ? ምርቶች፣ ዋጋ፣ ትዕዛዝ ሁኔታ — ሁሉን ልረዳ እችላለሁ። WhatsApp: wa.me/{WHATSAPP_NUMBER}"


@ai_bp.route('/ai-chat', methods=['POST'])
def ai_chat():
    """Main AI chat endpoint."""
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

        if not api_key:
            reply = smart_fallback(message, user_id=session.get('user_id'), lang=lang)
            return jsonify({'success': True, 'reply': reply, 'source': 'fallback'})

        user_id = session.get('user_id')

        # Get product + order context in parallel logic
        products_context = get_product_context(message)
        orders_context = get_order_context(user_id, message, lang)

        # Build system prompt
        system_content = STORE_SYSTEM_PROMPT.format(
            whatsapp=WHATSAPP_NUMBER,
            free_ship=FREE_SHIPPING_THRESHOLD,
            ship_cost=SHIPPING_COST,
            products=products_context,
            orders=orders_context
        )

        # Build messages list
        messages = [{'role': 'system', 'content': system_content}]

        # Add conversation history (last 8 turns)
        for h in history[-8:]:
            role = h.get('role', 'user')
            content = h.get('content', '')
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': content[:300]})

        messages.append({'role': 'user', 'content': message})

        # Call Groq
        from groq import Groq
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=messages,
            max_tokens=400,
            temperature=0.7,
        )
        reply = completion.choices[0].message.content.strip()
        return jsonify({'success': True, 'reply': reply, 'source': 'groq'})

    except Exception as e:
        logger.error(f"AI chat error: {e}")
        fallback = smart_fallback(
            message if 'message' in locals() else '',
            user_id=session.get('user_id'),
            lang=session.get('lang', 'am')
        )
        return jsonify({'success': True, 'reply': fallback, 'source': 'fallback'})


@ai_bp.route('/ai-chat/suggestions', methods=['GET'])
def ai_suggestions():
    """Return quick suggestion prompts based on language."""
    lang = session.get('lang', 'am')
    logged_in = bool(session.get('user_id'))
    if lang == 'am':
        suggestions = [
            "የእኔ ትዕዛዝ ደረሰ?",
            "ለ1000 ብር ምን ቀሚስ አለ?",
            "ለልጆች ምን ምርቶች አሉ?",
            "ዋጋ እና ማድረሻ ሁኔታ",
        ] if logged_in else [
            "ለ1000 ብር ምን ቀሚስ አለ?",
            "ለልጆች ምን ምርቶች አሉ?",
            "ዋጋ እና ማድረሻ ሁኔታ",
            "ስልክ ቁጥር ስጠኝ",
        ]
    elif lang == 'ar':
        suggestions = [
            "ما حالة طلبي?",
            "ماذا يوجد تحت 1000 بر؟",
            "ملابس الأطفال المتوفرة",
            "معلومات الشحن والتوصيل",
        ] if logged_in else [
            "ماذا يوجد تحت 1000 بر؟",
            "ملابس الأطفال المتوفرة",
            "معلومات الشحن والتوصيل",
            "تواصل معنا",
        ]
    else:
        suggestions = [
            "Where is my order?",
            "Show dresses under 1000 ETB",
            "What kids clothing do you have?",
            "Shipping & delivery info",
        ] if logged_in else [
            "Show dresses under 1000 ETB",
            "What kids clothing do you have?",
            "Shipping & delivery info",
            "Contact us",
        ]
    return jsonify({'success': True, 'suggestions': suggestions})
