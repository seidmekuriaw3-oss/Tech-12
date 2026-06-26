import os
import urllib.parse
import re
import threading
from datetime import datetime
import logging
logger = logging.getLogger(__name__)


# Get WhatsApp number from environment variable with fallback
WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '251987957957')


# ==================== OWNER NOTIFICATION (CallMeBot) ====================

def _send_callmebot(phone: str, message: str, api_key: str):
    """Fire-and-forget HTTP call to CallMeBot — runs in background thread."""
    try:
        import requests as _req
        encoded = urllib.parse.quote(message)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded}&apikey={api_key}"
        resp = _req.get(url, timeout=10)
        if resp.status_code == 200:
            logger.warning(f"✅ WhatsApp notification sent to {phone}")
        else:
            logger.warning(f"⚠️  CallMeBot response {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"⚠️  WhatsApp notification failed: {e}")


def send_owner_order_notification(order_number: str, customer_name: str,
                                   customer_phone: str, items: list,
                                   total: float, notes: str = ''):
    """
    Send automatic WhatsApp notification to store owner when order is placed.
    Requires CALLMEBOT_API_KEY environment variable (get it free from CallMeBot).
    Runs in a background thread so it never blocks the order response.
    """
    api_key = os.environ.get('CALLMEBOT_API_KEY', '')
    owner_phone = os.environ.get('WHATSAPP_NUMBER', WHATSAPP_NUMBER)

    if not api_key:
        logger.warning("ℹ️  CALLMEBOT_API_KEY not set — WhatsApp owner notification skipped.")
        return

    # Build the message
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        "🛍️ *ትዕዛዝ ደረሰ — ሰሚራ ልብስ እስቶር*",
        "━" * 32,
        f"📋 ትዕዛዝ #: *{order_number}*",
        f"📅 ቀን: {now}",
        f"👤 ደንበኛ: *{customer_name}*",
        f"📞 ስልክ: {customer_phone}",
        "━" * 32,
        "*የተዘዘ ምርቶች:*",
    ]
    for item in items:
        name = item.get('name_am') or item.get('name', 'ምርት')
        qty = item.get('quantity', 1)
        price = item.get('price', item.get('price_at_time', 0))
        lines.append(f"  • {name}  x{qty}  — {price:,.0f} ETB")

    lines += [
        "━" * 32,
        f"💰 *ጠቅላላ: {total:,.0f} ETB*",
    ]
    if notes:
        lines.append(f"📝 ማስታወሻ: {notes}")
    store_phone = os.environ.get('WHATSAPP_NUMBER', WHATSAPP_NUMBER)
    phone_display = store_phone if store_phone.startswith('+') else f"+{store_phone}"
    lines += [
        "━" * 32,
        "✅ Admin: /admin/orders",
        f"📞 {phone_display}",
    ]
    message = "\n".join(lines)

    # Format phone: must start with + for CallMeBot
    phone_fmt = owner_phone if owner_phone.startswith('+') else f"+{owner_phone}"

    # Run in background so it never slows down the order
    t = threading.Thread(target=_send_callmebot, args=(phone_fmt, message, api_key), daemon=True)
    t.start()


BACKUP_WHATSAPP_NUMBERS = ['251906080606', '251906090606']


class WhatsAppService:
    """Service class for WhatsApp messaging integration"""
    
    @staticmethod
    def format_phone_number(phone):
        """
        Format phone number for WhatsApp (remove spaces, dashes, leading zeros).
        
        Args:
            phone (str): Raw phone number
        
        Returns:
            str: Formatted phone number
        """
        if not phone:
            return WHATSAPP_NUMBER
        
        # Convert to string if needed
        phone = str(phone)
        
        # Remove spaces, dashes, and other separators
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        
        # Remove leading '0' or '00' for Ethiopian numbers
        if cleaned.startswith('00'):
            cleaned = cleaned[2:]
        elif cleaned.startswith('0'):
            cleaned = cleaned[1:]
        
        # Ensure it starts with country code
        if not cleaned.startswith('251'):
            cleaned = '251' + cleaned
        
        return cleaned
    
    @staticmethod
    def validate_phone_number(phone):
        """
        Validate Ethiopian phone number format.
        
        Args:
            phone (str): Phone number to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not phone:
            return False
        
        # Remove any formatting
        cleaned = re.sub(r'[\s\-\(\)\+]', '', str(phone))
        
        # Check Ethiopian phone number pattern
        # 09xxxxxxxx or 07xxxxxxxx or 2519xxxxxxxx
        pattern = r'^(09|07|2519)[0-9]{8}$'
        return bool(re.match(pattern, cleaned))
    
    @staticmethod
    def get_store_numbers():
        """
        Get all store WhatsApp numbers.
        
        Returns:
            list: List of store phone numbers
        """
        return [WHATSAPP_NUMBER] + BACKUP_WHATSAPP_NUMBERS
    
    @staticmethod
    def send_order_message(customer_name, customer_phone, items, total, order_number=None):
        """
        Prepare WhatsApp order message.
        
        Args:
            customer_name (str): Customer's full name
            customer_phone (str): Customer's phone number
            items (list): List of ordered items with 'name', 'quantity', 'price'
            total (float): Order total amount
            order_number (str, optional): Order number
        
        Returns:
            str: WhatsApp URL with encoded message
        """
        try:
            message = "🛍️ *NEW ORDER - SEMIRA FASHION*\n"
            message += "=" * 40 + "\n\n"
            
            if order_number:
                message += f"📋 *Order #:* {order_number}\n"
            
            message += f"👤 *Customer:* {customer_name}\n"
            message += f"📞 *Phone:* {customer_phone}\n"
            message += f"📅 *Date:* {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            message += "─" * 35 + "\n"
            message += "*ORDER ITEMS:*\n"
            message += "─" * 35 + "\n"
            
            subtotal = 0
            for i, item in enumerate(items, 1):
                item_total = item['quantity'] * item.get('discounted_price', item['price'])
                subtotal += item_total
                message += f"{i}. {item.get('name', item.get('product_name', 'Product'))}\n"
                message += f"   {item['quantity']} x {item['price']} ETB = {item_total} ETB\n\n"
            
            message += "─" * 35 + "\n"
            message += f"💰 *Subtotal:* {subtotal} ETB\n"
            
            # Add discount if applicable
            if 'discount' in items or total < subtotal:
                discount = subtotal - total
                message += f"🎉 *Discount:* {discount} ETB\n"
            
            message += f"💵 *TOTAL:* {total} ETB\n"
            message += "=" * 40 + "\n"
            message += "🙏 Thank you for shopping with SEMIRA FASHION!\n"
            message += f"📞 For inquiries, call: +{WHATSAPP_NUMBER}"
            
            encoded = urllib.parse.quote(message)
            phone = WhatsAppService.format_phone_number(WHATSAPP_NUMBER)
            return f"https://wa.me/{phone}?text={encoded}"
            
        except Exception as e:
            logger.error(f"Error preparing order message: {e}")
            return f"https://wa.me/{WHATSAPP_NUMBER}"
    
    @staticmethod
    def send_contact_message(name, email, phone, message_text):
        """
        Prepare WhatsApp contact message.
        
        Args:
            name (str): Sender's name
            email (str): Sender's email (optional)
            phone (str): Sender's phone number (optional)
            message_text (str): Contact message
        
        Returns:
            str: WhatsApp URL with encoded message
        """
        try:
            msg = "📬 *New Contact Message - SEMIRA FASHION*\n"
            msg += "=" * 40 + "\n\n"
            msg += f"👤 *Name:* {name}\n"
            
            if email:
                msg += f"📧 *Email:* {email}\n"
            if phone:
                msg += f"📞 *Phone:* {phone}\n"
            
            msg += "\n" + "─" * 35 + "\n"
            msg += f"💬 *Message:*\n{message_text}\n"
            msg += "=" * 40 + "\n"
            msg += "🕒 We will respond within 24 hours.\n"
            msg += f"📞 Call us: +{WHATSAPP_NUMBER}"
            
            encoded = urllib.parse.quote(msg)
            phone = WhatsAppService.format_phone_number(WHATSAPP_NUMBER)
            return f"https://wa.me/{phone}?text={encoded}"
            
        except Exception as e:
            logger.error(f"Error preparing contact message: {e}")
            return f"https://wa.me/{WHATSAPP_NUMBER}"
    
    @staticmethod
    def send_custom_message(to_phone, message):
        """
        Send a custom message to any WhatsApp number.
        
        Args:
            to_phone (str): Recipient's phone number
            message (str): Message content
        
        Returns:
            str: WhatsApp URL with encoded message
        """
        try:
            encoded = urllib.parse.quote(message)
            phone = WhatsAppService.format_phone_number(to_phone)
            return f"https://wa.me/{phone}?text={encoded}"
        except Exception as e:
            logger.error(f"Error preparing custom message: {e}")
            return None
    
    @staticmethod
    def send_invoice(order_number, customer_name, customer_phone, items, subtotal, shipping, total, discount=0):
        """
        Prepare detailed invoice message.
        
        Args:
            order_number (str): Order number
            customer_name (str): Customer name
            customer_phone (str): Customer phone
            items (list): List of order items
            subtotal (float): Order subtotal
            shipping (float): Shipping cost
            total (float): Order total
            discount (float): Discount amount
        
        Returns:
            str: WhatsApp URL with encoded invoice
        """
        try:
            message = "🧾 *INVOICE - SEMIRA FASHION*\n"
            message += "=" * 40 + "\n\n"
            message += f"📋 *Order #:* {order_number}\n"
            message += f"👤 *Customer:* {customer_name}\n"
            message += f"📞 *Phone:* {customer_phone}\n"
            message += f"📅 *Date:* {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            message += "─" * 35 + "\n"
            message += "*ORDER SUMMARY*\n"
            message += "─" * 35 + "\n"
            
            for item in items:
                item_name = item.get('name', item.get('product_name', 'Product'))
                item_total = item['quantity'] * item.get('price_at_time', item.get('price', 0))
                message += f"• {item_name}\n"
                message += f"  {item['quantity']} x {item.get('price_at_time', item.get('price', 0))} ETB = {item_total} ETB\n\n"
            
            message += "─" * 35 + "\n"
            message += f"💰 *Subtotal:* {subtotal} ETB\n"
            
            if discount > 0:
                message += f"🎉 *Discount (10%):* {discount} ETB\n"
            
            message += f"🚚 *Shipping:* {shipping} ETB\n"
            message += "=" * 35 + "\n"
            message += f"💵 *TOTAL PAID:* {total} ETB\n"
            message += "=" * 35 + "\n\n"
            message += "✅ Thank you for your purchase!\n"
            message += "🔗 Track your order: semirafashion.com/orders\n"
            message += f"📞 Questions? Call: +{WHATSAPP_NUMBER}"
            
            encoded = urllib.parse.quote(message)
            phone = WhatsAppService.format_phone_number(customer_phone)
            return f"https://wa.me/{phone}?text={encoded}"
            
        except Exception as e:
            logger.error(f"Error preparing invoice: {e}")
            return f"https://wa.me/{WHATSAPP_NUMBER}"
    
    @staticmethod
    def send_status_update(order_number, customer_phone, status, notes=''):
        """
        Send order status update notification.
        
        Args:
            order_number (str): Order number
            customer_phone (str): Customer's phone number
            status (str): Order status
            notes (str): Additional notes
        
        Returns:
            str: WhatsApp URL with encoded message
        """
        status_emojis = {
            'pending': '⏳',
            'confirmed': '✅',
            'processing': '⚙️',
            'shipped': '🚚',
            'delivered': '🎉',
            'cancelled': '❌'
        }
        
        status_texts = {
            'pending': 'Your order has been received and is pending confirmation.',
            'confirmed': 'Your order has been confirmed! We are preparing it for shipment.',
            'processing': 'Your order is being processed and packed.',
            'shipped': 'Great news! Your order has been shipped and is on its way.',
            'delivered': 'Your order has been delivered. Enjoy your furniture!',
            'cancelled': 'Your order has been cancelled. Contact us for more information.'
        }
        
        try:
            emoji = status_emojis.get(status, '📦')
            text = status_texts.get(status, f'Order status updated to: {status}')
            
            message = f"{emoji} *Order Status Update - SEMIRA FASHION*\n"
            message += "=" * 40 + "\n\n"
            message += f"📋 *Order #:* {order_number}\n"
            message += f"📊 *Status:* {status.upper()}\n\n"
            message += f"{text}\n\n"
            
            if notes:
                message += f"📝 *Notes:* {notes}\n\n"
            
            message += "🔗 Track your order: semirafashion.com/orders\n"
            message += "📞 Questions? Call us: {WHATSAPP_NUMBER}\n"
            message += "🙏 Thank you for shopping with SEMIRA FASHION!"
            
            encoded = urllib.parse.quote(message)
            phone = WhatsAppService.format_phone_number(customer_phone)
            return f"https://wa.me/{phone}?text={encoded}"
            
        except Exception as e:
            logger.error(f"Error preparing status update: {e}")
            return None
    
    @staticmethod
    def get_qr_code(size=200):
        """
        Generate WhatsApp QR code link for business.
        
        Args:
            size (int): QR code size in pixels
        
        Returns:
            str: QR code URL (using API)
        """
        phone = WhatsAppService.format_phone_number(WHATSAPP_NUMBER)
        return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data=https://wa.me/{phone}"
    
    @staticmethod
    def get_whatsapp_link(phone=None, message=None):
        """
        Generate WhatsApp link with optional pre-filled message.
        
        Args:
            phone (str, optional): Phone number (defaults to store number)
            message (str, optional): Pre-filled message
        
        Returns:
            str: WhatsApp URL
        """
        target_phone = WhatsAppService.format_phone_number(phone or WHATSAPP_NUMBER)
        
        if message:
            encoded = urllib.parse.quote(message)
            return f"https://wa.me/{target_phone}?text={encoded}"
        
        return f"https://wa.me/{target_phone}"
    
    @staticmethod
    def get_click_to_chat_html(phone=None, button_text="Chat on WhatsApp", button_class="btn-whatsapp"):
        """
        Generate HTML for WhatsApp click-to-chat button.
        
        Args:
            phone (str, optional): Phone number
            button_text (str): Button text
            button_class (str): CSS class for button
        
        Returns:
            str: HTML button code
        """
        link = WhatsAppService.get_whatsapp_link(phone)
        return f'<a href="{link}" target="_blank" class="{button_class}"><i class="fab fa-whatsapp"></i> {button_text}</a>'
    
    @staticmethod
    def send_bulk_messages(phone_numbers, message):
        """
        Generate links for sending same message to multiple numbers.
        
        Args:
            phone_numbers (list): List of phone numbers
            message (str): Message to send
        
        Returns:
            list: List of WhatsApp URLs
        """
        links = []
        for phone in phone_numbers:
            link = WhatsAppService.send_custom_message(phone, message)
            if link:
                links.append(link)
        return links


# ==================== CUSTOMER ORDER STATUS NOTIFICATION ====================

def send_customer_status_notification(
    order_number: str,
    customer_name: str,
    customer_phone: str,
    status: str,
    notes: str = ''
):
    """
    Notify the customer when their order status changes.

    Strategy (two-layer):
      1. AUTO  — if CALLMEBOT_API_KEY is set, fire a background WhatsApp message
                 to the customer's number via CallMeBot and return auto_sent=True.
      2. MANUAL— always build a wa.me URL so the admin can tap it as a fallback.

    Returns:
        dict: {
            'auto_sent': bool,      # True when CallMeBot message was dispatched
            'wa_url':    str|None,  # pre-filled wa.me link for manual sending
        }
    """
    status_icons = {
        'pending':    '⏳', 'confirmed':  '✅', 'processing': '⚙️',
        'shipped':    '🚚', 'delivered':  '🎉', 'cancelled':  '❌',
    }
    # Amharic messages (primary)
    am_msgs = {
        'confirmed':  f'ሰላም {customer_name}! ትዕዛዝ #{order_number} ተቀብለናል — በዝግጅት ላይ ነው። ✅\nሰሚራ ፋሽን: {WHATSAPP_NUMBER}',
        'processing': f'ሰላም {customer_name}! ትዕዛዝ #{order_number} በሂደት ላይ ነው። ⚙️\nሰሚራ ፋሽን: {WHATSAPP_NUMBER}',
        'shipped':    f'ሰላም {customer_name}! ✈️ ትዕዛዝ #{order_number} ተላከ — በቅርቡ ይደርስዎታል! 🚚\nሰሚራ ፋሽን: {WHATSAPP_NUMBER}',
        'delivered':  f'ሰላም {customer_name}! 🎉 ትዕዛዝ #{order_number} ደረሰ። ጥሩ ጥቅም ይሁንልዎ!\nሰሚራ ፋሽን: {WHATSAPP_NUMBER}',
        'cancelled':  f'ሰላም {customer_name}! ትዕዛዝ #{order_number} ተሰርዟል። ❌\nለጥያቄ: {WHATSAPP_NUMBER}',
        'pending':    f'ሰላም {customer_name}! ትዕዛዝ #{order_number} ደርሶናል — በቅርቡ እናረጋግጣለን። ⏳\nሰሚራ ፋሽን: {WHATSAPP_NUMBER}',
    }
    icon = status_icons.get(status, '📦')
    message = am_msgs.get(status, f'{icon} ትዕዛዝ #{order_number} — {status}')
    if notes:
        message += f'\n📝 {notes}'

    # --- Build wa.me fallback URL ---
    wa_url = None
    phone_digits = ''.join(filter(str.isdigit, customer_phone or ''))
    if phone_digits.startswith('0'):
        phone_digits = '251' + phone_digits[1:]
    if phone_digits:
        wa_url = f"https://wa.me/{phone_digits}?text={urllib.parse.quote(message)}"

    # --- Auto-send via CallMeBot if API key is configured ---
    api_key = os.environ.get('CALLMEBOT_API_KEY', '')
    auto_sent = False
    if api_key and phone_digits:
        phone_fmt = f"+{phone_digits}"
        t = threading.Thread(
            target=_send_callmebot,
            args=(phone_fmt, message, api_key),
            daemon=True
        )
        t.start()
        auto_sent = True
        logger.warning(f"✅ Auto WhatsApp queued → {phone_fmt} [{status}] #{order_number}")
    else:
        if not api_key:
            logger.warning("ℹ️  CALLMEBOT_API_KEY not set — customer WhatsApp auto-send skipped.")
        if not phone_digits:
            logger.warning(f"ℹ️  No phone for order #{order_number} — customer WhatsApp skipped.")

    return {'auto_sent': auto_sent, 'wa_url': wa_url}


# ==================== LOW-STOCK ALERT ====================

def send_low_stock_alert(products: list):
    """
    Notify the store owner via WhatsApp when products drop to or below their
    low-stock threshold after an order.

    products: list of dicts with keys id, name_am, name, stock_quantity,
              low_stock_threshold.
    Always logs to console; sends WhatsApp only when CALLMEBOT_API_KEY is set.
    Runs its own background thread — safe to call from request context.
    """
    if not products:
        return

    # Always log — visible in server console even without CallMeBot
    logger.warning(f"⚠️  LOW STOCK ALERT — {len(products)} product(s) at/below threshold:")
    for p in products:
        qty = p['stock_quantity']
        thr = p.get('low_stock_threshold', 0)
        label = "OUT OF STOCK" if qty == 0 else f"LOW ({qty} left, threshold {thr})"
        logger.warning(f"   • [{p['id']}] {p.get('name_am') or p.get('name', 'Product')} — {label}")

    api_key = os.environ.get('CALLMEBOT_API_KEY', '')
    if not api_key:
        logger.warning("ℹ️  CALLMEBOT_API_KEY not set — WhatsApp low-stock alert skipped.")
        return

    owner_phone = os.environ.get('WHATSAPP_NUMBER', WHATSAPP_NUMBER)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    lines = [
        "⚠️ *ዕቃ አነስተኛ ማስጠንቀቂያ — ሰሚራ ፋሽን*",
        "━" * 30,
        f"📅 {now}",
        "━" * 30,
    ]
    for p in products:
        qty = p['stock_quantity']
        thr = p.get('low_stock_threshold', 0)
        name = p.get('name_am') or p.get('name', 'ምርት')
        if qty == 0:
            lines.append(f"🔴 *{name}* — ዕቃ አልቋል!")
        else:
            lines.append(f"🟡 *{name}* — {qty} ቀርቷል (ዝቅተኛ: {thr})")
    lines += [
        "━" * 30,
        "🔗 /admin/products ⟶ ዕቃ ይሙሉ",
    ]

    message = "\n".join(lines)
    phone_fmt = owner_phone if owner_phone.startswith('+') else f"+{owner_phone}"
    t = threading.Thread(
        target=_send_callmebot, args=(phone_fmt, message, api_key), daemon=True
    )
    t.start()


# ==================== BACKWARD COMPATIBILITY ====================

# Keep function versions for backward compatibility
def send_order_message(customer_name, customer_phone, items, total, order_number=None):
    """Backward compatibility function"""
    return WhatsAppService.send_order_message(customer_name, customer_phone, items, total, order_number)


def send_contact_message(name, email, phone, message_text):
    """Backward compatibility function"""
    return WhatsAppService.send_contact_message(name, email, phone, message_text)


def send_invoice_message(order_number, customer_name, customer_phone, items, subtotal, shipping, total, discount=0):
    """Backward compatibility function for invoice"""
    return WhatsAppService.send_invoice(order_number, customer_name, customer_phone, items, subtotal, shipping, total, discount)


def send_status_update_message(order_number, customer_phone, status, notes=''):
    """Backward compatibility function for status update"""
    return WhatsAppService.send_status_update(order_number, customer_phone, status, notes)