"""
AI Agent Route for SEMIRA FASHION
Powered by OpenAI gpt-4o-mini
Falls back to smart rule-based responses if no API key.
"""
import os
import re
import logging
from flask import Blueprint, request, jsonify, session
from database.db import get_db
from routes.shared import WHATSAPP_NUMBER, FREE_SHIPPING_THRESHOLD, SHIPPING_COST

ai_bp = Blueprint('ai', __name__)
logger = logging.getLogger(__name__)

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

LANGUAGE RULE: Detect the language the user writes in and ALWAYS respond in the SAME language.
- If they write in Amharic → respond in Amharic
- If they write in English → respond in English  
- If they write in Arabic → respond in Arabic
- Keep responses SHORT (2-4 sentences max), friendly, and helpful.
- For product recommendations, mention price and name.
- For order issues or complex problems, suggest WhatsApp: {whatsapp}
- Never make up products not in the list above.
- Use 🌸 or 👗 emojis occasionally to feel warm and friendly.
- If asked about sizes, we have all sizes (XS to 3XL for women, 0-14 years for children).
"""


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


def smart_fallback(message: str) -> str:
    """Rule-based fallback when no OpenAI key is set."""
    msg = message.lower()

    # Greetings
    if any(w in msg for w in ['hello', 'hi ', 'ሰላም', 'selam', 'hey', 'good']):
        return "ሰላም! 👋 ወደ SEMIRA FASHION እንኳን ደህና መጡ። ምን ልርዳዎ? ምርቶቻችንን ለማየት /products ይጫኑ።"

    # Price/shipping
    if any(w in msg for w in ['shipping', 'delivery', 'ማድረስ', 'አድራሻ', 'ሰጪ']):
        return f"🚚 ከ{FREE_SHIPPING_THRESHOLD:,} ብር በላይ ትዕዛዝ ሲደርግ ነጻ ማድረሻ ያግኛሉ! ከዚያ ያነሰ ትዕዛዝ {SHIPPING_COST} ብር ማድረሻ ክፍያ አለ።"

    # Orders/tracking
    if any(w in msg for w in ['order', 'ትዕዛዝ', 'track', 'status', 'ሁኔታ']):
        return f"📦 ትዕዛዝዎን ለማወቅ '/orders' ገጽ ይጎብኙ ወይም WhatsApp ይጠቀሙ: wa.me/{WHATSAPP_NUMBER}"

    # Return/exchange
    if any(w in msg for w in ['return', 'exchange', 'መመለስ', 'ቅሬታ', 'refund']):
        return "↩️ ያልለበሱ ምርቶችን በ7 ቀን ውስጥ መመለስ ይቻላል። ለዝርዝር WhatsApp ያግኙን።"

    # WhatsApp/contact
    if any(w in msg for w in ['whatsapp', 'call', 'phone', 'ስልክ', 'ደውል', 'contact']):
        return f"📱 WhatsApp: wa.me/{WHATSAPP_NUMBER}\nደስ ብሎን ሁልጊዜ ለማግኘት ይቻላል!"

    # Size
    if any(w in msg for w in ['size', 'መጠን', 'ሳይዝ', 'fit', 'large', 'small', 'medium']):
        return "👗 ምርቶቻችን ከ XS እስከ 3XL (ለሴቶች) እና ከ 0 እስከ 14 ዓመት (ለልጆች) ይገኛሉ። ዝርዝር ለማወቅ WhatsApp ያግኙን።"

    # Products
    if any(w in msg for w in ['product', 'ምርት', 'ልብስ', 'dress', 'ቀሚስ', 'price', 'ዋጋ', 'show', 'አሳይ']):
        return "👗 ምርቶቻችንን ለማየት ይህን ይጫኑ: <a href='/products' style='color:#1a7a4a;font-weight:600'>ሁሉም ምርቶች →</a>"

    # Default
    return f"ሰላም! 🌸 SEMIRA FASHION AI assistant ነኝ። ምርቶቻችንን፣ ዋጋ፣ ወይም ሌሎች ጥያቄዎች ቢኖሩዎ ልርዳዎ! ወይም WhatsApp: wa.me/{WHATSAPP_NUMBER}"


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
            reply = smart_fallback(message)
            return jsonify({'success': True, 'reply': reply, 'source': 'fallback'})

        # Get product context
        products_context = get_product_context(message)

        # Build system prompt
        system_content = STORE_SYSTEM_PROMPT.format(
            whatsapp=WHATSAPP_NUMBER,
            free_ship=FREE_SHIPPING_THRESHOLD,
            ship_cost=SHIPPING_COST,
            products=products_context
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
        fallback = smart_fallback(message if 'message' in locals() else '')
        return jsonify({'success': True, 'reply': fallback, 'source': 'fallback'})


@ai_bp.route('/ai-chat/suggestions', methods=['GET'])
def ai_suggestions():
    """Return quick suggestion prompts based on language."""
    lang = session.get('lang', 'am')
    if lang == 'am':
        suggestions = [
            "ለ1000 ብር ምን ቀሚስ አለ?",
            "ለልጆች ምን ምርቶች አሉ?",
            "ዋጋ እና ማድረሻ ሁኔታ",
            "ስልክ ቁጥር ስጠኝ"
        ]
    elif lang == 'ar':
        suggestions = [
            "ماذا يوجد تحت 1000 بر؟",
            "ملابس الأطفال المتوفرة",
            "معلومات الشحن والتوصيل",
            "تواصل معنا"
        ]
    else:
        suggestions = [
            "Show dresses under 1000 ETB",
            "What kids clothing do you have?",
            "Shipping & delivery info",
            "Contact us"
        ]
    return jsonify({'success': True, 'suggestions': suggestions})
