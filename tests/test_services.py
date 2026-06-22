"""
Service Tests for Ethiosadat Furniture

This module contains tests for all service layer classes including:
- CartService (cart operations)
- ProductService (product operations)
- OrderService (order operations)
- AdService (advertisement operations)
- WhatsAppService (messaging operations)
"""

import pytest
from services.cart_service import CartService
from services.product_service import ProductService
from services.order_service import OrderService
from services.ad_service import AdService
from services.whatsapp_service import WhatsAppService


# ==================== CART SERVICE TESTS ====================

def test_cart_service_get_cart(app):
    """Test CartService.get_cart() - returns list"""
    with app.app_context():
        CartService.clear()
        cart = CartService.get_cart()
        assert isinstance(cart, list)
        assert len(cart) == 0


def test_cart_service_add_item(app):
    """Test CartService.add_item() - adds item to cart"""
    with app.app_context():
        CartService.clear()
        CartService.add_item('test_id_1', 'Test Product 1', 1000, 2)
        
        cart = CartService.get_cart()
        assert len(cart) == 1
        assert cart[0]['id'] == 'test_id_1'
        assert cart[0]['name'] == 'Test Product 1'
        assert cart[0]['price'] == 1000
        assert cart[0]['quantity'] == 2


def test_cart_service_add_existing_item(app):
    """Test CartService.add_item() - adds quantity to existing item"""
    with app.app_context():
        CartService.clear()
        CartService.add_item('test_id_2', 'Test Product 2', 500, 1)
        CartService.add_item('test_id_2', 'Test Product 2', 500, 3)
        
        cart = CartService.get_cart()
        assert len(cart) == 1
        assert cart[0]['quantity'] == 4


def test_cart_service_get_count(app):
    """Test CartService.get_count() - returns total item count"""
    with app.app_context():
        CartService.clear()
        assert CartService.get_count() == 0
        
        CartService.add_item('test_id_3', 'Test Product 3', 1000, 2)
        CartService.add_item('test_id_4', 'Test Product 4', 2000, 3)
        
        assert CartService.get_count() == 5


def test_cart_service_get_subtotal(app):
    """Test CartService.get_subtotal() - calculates subtotal correctly"""
    with app.app_context():
        CartService.clear()
        CartService.add_item('test_id_5', 'Product 5', 1000, 2)
        CartService.add_item('test_id_6', 'Product 6', 500, 3)
        
        subtotal = CartService.get_subtotal()
        assert subtotal == (1000 * 2) + (500 * 3)  # 2000 + 1500 = 3500


def test_cart_service_get_total(app):
    """Test CartService.get_total() - includes shipping"""
    with app.app_context():
        CartService.clear()
        # Add items to exceed free shipping threshold
        CartService.add_item('test_id_7', 'Product 7', 3000, 2)  # 6000 subtotal
        
        total = CartService.get_total()
        assert total > 0


def test_cart_service_update_quantity(app):
    """Test CartService.update_quantity() - updates item quantity"""
    with app.app_context():
        CartService.clear()
        CartService.add_item('test_id_8', 'Product 8', 1000, 1)
        
        CartService.update_quantity('test_id_8', 5)
        cart = CartService.get_cart()
        assert cart[0]['quantity'] == 5


def test_cart_service_update_quantity_remove_when_zero(app):
    """Test CartService.update_quantity() - removes item when quantity < 1"""
    with app.app_context():
        CartService.clear()
        CartService.add_item('test_id_9', 'Product 9', 1000, 1)
        
        CartService.update_quantity('test_id_9', 0)
        cart = CartService.get_cart()
        assert len(cart) == 0


def test_cart_service_remove_item(app):
    """Test CartService.remove_item() - removes specific item"""
    with app.app_context():
        CartService.clear()
        CartService.add_item('test_id_10', 'Product 10', 1000, 1)
        CartService.add_item('test_id_11', 'Product 11', 2000, 1)
        
        CartService.remove_item('test_id_10')
        cart = CartService.get_cart()
        assert len(cart) == 1
        assert cart[0]['id'] == 'test_id_11'


def test_cart_service_item_exists(app):
    """Test CartService.item_exists() - checks if item in cart"""
    with app.app_context():
        CartService.clear()
        CartService.add_item('test_id_12', 'Product 12', 1000, 1)
        
        assert CartService.item_exists('test_id_12') is True
        assert CartService.item_exists('nonexistent') is False


def test_cart_service_get_item_quantity(app):
    """Test CartService.get_item_quantity() - returns quantity of specific item"""
    with app.app_context():
        CartService.clear()
        CartService.add_item('test_id_13', 'Product 13', 1000, 3)
        
        assert CartService.get_item_quantity('test_id_13') == 3
        assert CartService.get_item_quantity('nonexistent') == 0


def test_cart_service_is_empty(app):
    """Test CartService.is_empty() - checks if cart is empty"""
    with app.app_context():
        CartService.clear()
        assert CartService.is_empty() is True
        
        CartService.add_item('test_id_14', 'Product 14', 1000, 1)
        assert CartService.is_empty() is False


def test_cart_service_clear(app):
    """Test CartService.clear() - removes all items"""
    with app.app_context():
        CartService.add_item('test_id_15', 'Product 15', 1000, 1)
        CartService.add_item('test_id_16', 'Product 16', 2000, 1)
        
        CartService.clear()
        cart = CartService.get_cart()
        assert len(cart) == 0


# ==================== PRODUCT SERVICE TESTS ====================

def test_product_service_get_all(app):
    """Test ProductService.get_all() - returns list of products"""
    with app.app_context():
        products = ProductService.get_all()
        assert isinstance(products, list)


def test_product_service_get_by_id(app):
    """Test ProductService.get_by_id() - returns product or None"""
    with app.app_context():
        # Test with non-existent ID
        product = ProductService.get_by_id(99999)
        assert product is None


def test_product_service_get_by_category(app):
    """Test ProductService.get_by_category() - returns filtered products"""
    with app.app_context():
        products = ProductService.get_by_category('ሶፋ')
        assert isinstance(products, list)


def test_product_service_search(app):
    """Test ProductService.search() - returns matching products"""
    with app.app_context():
        results = ProductService.search('test')
        assert isinstance(results, list)


def test_product_service_get_featured(app):
    """Test ProductService.get_featured() - returns featured products"""
    with app.app_context():
        featured = ProductService.get_featured(limit=4)
        assert isinstance(featured, list)


def test_product_service_get_categories(app):
    """Test ProductService.get_categories() - returns category list"""
    with app.app_context():
        categories = ProductService.get_categories()
        assert isinstance(categories, list)


def test_product_service_get_count(app):
    """Test ProductService.get_count() - returns product count"""
    with app.app_context():
        count = ProductService.get_count()
        assert isinstance(count, int)
        assert count >= 0


# ==================== ORDER SERVICE TESTS ====================

def test_order_service_get_all(app):
    """Test OrderService.get_all() - returns list of orders"""
    with app.app_context():
        orders = OrderService.get_all()
        assert isinstance(orders, list)


def test_order_service_get_by_id(app):
    """Test OrderService.get_by_id() - returns order or None"""
    with app.app_context():
        order = OrderService.get_by_id(99999)
        assert order is None


def test_order_service_get_stats(app):
    """Test OrderService.get_stats() - returns statistics dictionary"""
    with app.app_context():
        stats = OrderService.get_stats()
        assert isinstance(stats, dict)
        assert 'total_orders' in stats
        assert 'total_revenue' in stats
        assert 'pending_orders' in stats


# ==================== AD SERVICE TESTS ====================

def test_ad_service_get_all(app):
    """Test AdService.get_all() - returns list of ads"""
    with app.app_context():
        ads = AdService.get_all()
        assert isinstance(ads, list)


def test_ad_service_get_active(app):
    """Test AdService.get_active() - returns only active ads"""
    with app.app_context():
        active_ads = AdService.get_active()
        assert isinstance(active_ads, list)


def test_ad_service_create_and_delete(app):
    """Test AdService.create() and delete()"""
    with app.app_context():
        # Create ad
        ad_id = AdService.create('Test advertisement for service test')
        assert ad_id is not None
        
        # Verify created
        ad = AdService.get_by_id(ad_id)
        assert ad is not None
        assert ad['text'] == 'Test advertisement for service test'
        
        # Delete ad
        result = AdService.delete(ad_id)
        assert result is True
        
        # Verify deleted
        ad = AdService.get_by_id(ad_id)
        assert ad is None


def test_ad_service_toggle_active(app):
    """Test AdService.toggle_active() - activates/deactivates ad"""
    with app.app_context():
        ad_id = AdService.create('Toggle test ad')
        
        # Toggle to inactive
        AdService.toggle_active(ad_id)
        ad = AdService.get_by_id(ad_id)
        assert ad['is_active'] == 0
        
        # Toggle back to active
        AdService.toggle_active(ad_id)
        ad = AdService.get_by_id(ad_id)
        assert ad['is_active'] == 1
        
        # Cleanup
        AdService.delete(ad_id)


def test_ad_service_get_count(app):
    """Test AdService.get_count() - returns ad count"""
    with app.app_context():
        count = AdService.get_count()
        assert isinstance(count, int)
        assert count >= 0


# ==================== WHATSAPP SERVICE TESTS ====================

def test_whatsapp_service_send_order_message():
    """Test WhatsAppService.send_order_message() - returns URL"""
    items = [
        {'name': 'Test Product 1', 'price': 1000, 'quantity': 2, 'total': 2000}
    ]
    url = WhatsAppService.send_order_message('Test Customer', '0912345678', items, 2000)
    assert isinstance(url, str)
    assert 'https://wa.me/' in url
    assert 'text=' in url


def test_whatsapp_service_send_contact_message():
    """Test WhatsAppService.send_contact_message() - returns URL"""
    url = WhatsAppService.send_contact_message('Test User', 'test@example.com', '0912345678', 'Hello, this is a test message')
    assert isinstance(url, str)
    assert 'https://wa.me/' in url


def test_whatsapp_service_format_phone_number():
    """Test WhatsAppService.format_phone_number() - formats Ethiopian numbers"""
    # Test with 09 prefix
    formatted = WhatsAppService.format_phone_number('0912345678')
    assert formatted == '251912345678'
    
    # Test with 07 prefix
    formatted = WhatsAppService.format_phone_number('0712345678')
    assert formatted == '251712345678'
    
    # Test with country code
    formatted = WhatsAppService.format_phone_number('251912345678')
    assert formatted == '251912345678'


def test_whatsapp_service_validate_phone_number():
    """Test WhatsAppService.validate_phone_number() - validates Ethiopian numbers"""
    assert WhatsAppService.validate_phone_number('0912345678') is True
    assert WhatsAppService.validate_phone_number('0712345678') is True
    assert WhatsAppService.validate_phone_number('251912345678') is True
    assert WhatsAppService.validate_phone_number('123456') is False
    assert WhatsAppService.validate_phone_number('') is False


def test_whatsapp_service_get_whatsapp_link():
    """Test WhatsAppService.get_whatsapp_link() - generates WhatsApp link"""
    link = WhatsAppService.get_whatsapp_link('0912345678', 'Hello')
    assert 'https://wa.me/' in link
    assert 'text=Hello' in link