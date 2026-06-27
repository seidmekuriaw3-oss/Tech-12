"""
Services Package for SEMIRA FASHION

This package contains all business logic services for:
- Product management
- Shopping cart operations
- Order processing
- Advertisement management
- WhatsApp integration
- Notification services
"""

# ==================== PRODUCT SERVICES ====================
from services.product_service import ProductService

# ==================== CART SERVICES ====================
from services.cart_service import CartService

# ==================== ORDER SERVICES ====================
from services.order_service import OrderService

# ==================== ADVERTISEMENT SERVICES ====================
from services.ad_service import AdService

# ==================== WHATSAPP SERVICES ====================
from services.whatsapp_service import (
    WhatsAppService,
    send_order_message,
    send_contact_message
)

# ==================== NOTIFICATION SERVICES ====================
from services.notification_service import (
    NotificationService,
    send_push_notification,
    send_email_notification
)

# ==================== USER SERVICES ====================
# from services.user_service import UserService

# ==================== SETTINGS SERVICES ====================
# from services.settings_service import SettingsService

# ==================== UTILITY FUNCTIONS ====================

def get_all_services():
    """
    Get all service classes for easy access.
    
    Returns:
        dict: Dictionary containing all service classes
    """
    return {
        'product': ProductService,
        'cart': CartService,
        'order': OrderService,
        'ad': AdService,
        'whatsapp': WhatsAppService,
        'notification': NotificationService
    }


def get_service(service_name):
    """
    Get a specific service by name.
    
    Args:
        service_name (str): Name of the service 
                           ('product', 'cart', 'order', 'ad', 'whatsapp', 'notification')
    
    Returns:
        class: The requested service class, or None if not found
    """
    services = get_all_services()
    return services.get(service_name.lower())


# ==================== WHATSAPP FUNCTIONS (Shorter aliases) ====================

def whatsapp_order(customer_name, customer_phone, items, total):
    """
    Shortcut function for sending order via WhatsApp.
    
    Args:
        customer_name (str): Customer's full name
        customer_phone (str): Customer's phone number
        items (list): List of ordered items
        total (float): Order total amount
    
    Returns:
        str: WhatsApp URL
    """
    return send_order_message(customer_name, customer_phone, items, total)


def whatsapp_contact(name, email, phone, message):
    """
    Shortcut function for sending contact message via WhatsApp.
    
    Args:
        name (str): Sender's name
        email (str): Sender's email
        phone (str): Sender's phone number
        message (str): Contact message
    
    Returns:
        str: WhatsApp URL
    """
    return send_contact_message(name, email, phone, message)


# ==================== NOTIFICATION UTILITIES ====================

def send_admin_notification(title, body, data=None):
    """
    Send notification to admin.
    
    Args:
        title (str): Notification title
        body (str): Notification body
        data (dict, optional): Additional data
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    return send_push_notification(title, body, data, target='admin')


def send_customer_notification(user_id, title, body, data=None):
    """
    Send notification to specific customer.
    
    Args:
        user_id (int): Customer user ID
        title (str): Notification title
        body (str): Notification body
        data (dict, optional): Additional data
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    return send_push_notification(title, body, data, target='user', user_id=user_id)


def send_broadcast_notification(title, body, data=None):
    """
    Send broadcast notification to all users.
    
    Args:
        title (str): Notification title
        body (str): Notification body
        data (dict, optional): Additional data
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    return send_push_notification(title, body, data, target='all')


# ==================== VERSION INFO ====================

__version__ = '1.0.0'
__all__ = [
    # Services
    'ProductService',
    'CartService', 
    'OrderService',
    'AdService',
    'WhatsAppService',
    'NotificationService',
    
    # WhatsApp functions
    'send_order_message',
    'send_contact_message',
    'whatsapp_order',
    'whatsapp_contact',
    
    # Notification functions
    'send_push_notification',
    'send_email_notification',
    'send_admin_notification',
    'send_customer_notification',
    'send_broadcast_notification',
    
    # Utility functions
    'get_all_services',
    'get_service'
]


# ==================== INITIALIZATION LOG ====================
import logging
logger = logging.getLogger(__name__)

logger.warning("✅ Services package initialized successfully")
logger.warning(f"   - ProductService: Available")
logger.warning(f"   - CartService: Available")
logger.warning(f"   - OrderService: Available")
logger.warning(f"   - AdService: Available")
logger.warning(f"   - WhatsAppService: Available")
logger.warning(f"   - NotificationService: Available")