"""
Model Tests for Ethiosadat Furniture

This module contains tests for all database models including:
- Product model (CRUD operations)
- Ad model (CRUD operations)
- Order model (CRUD operations)
"""

import pytest
import json
from database.db import get_db
from database.models import Product, Ad, Order


# ==================== PRODUCT MODEL TESTS ====================

def test_product_creation(app):
    """Test creating a product"""
    with app.app_context():
        # Create test product with all fields
        product_data = {
            'name_am': 'የሙከራ ምርት',
            'name_en': 'Test Product',
            'description_am': 'ይህ የሙከራ ምርት መግለጫ ነው',
            'description_en': 'This is a test product description',
            'price': 5000,
            'old_price': 7000,
            'image': 'test.jpg',
            'category': 'ሶፋ',
            'stock': 10,
            'is_featured': 1
        }
        
        product_id = Product.create(product_data)
        assert product_id is not None
        assert isinstance(product_id, int)
        
        # Retrieve and verify
        product = Product.get_by_id(product_id)
        assert product is not None
        assert product['name_am'] == 'የሙከራ ምርት'
        assert product['name_en'] == 'Test Product'
        assert product['price'] == 5000
        assert product['old_price'] == 7000
        assert product['category'] == 'ሶፋ'
        assert product['stock'] == 10
        assert product['is_featured'] == 1


def test_product_creation_minimal_fields(app):
    """Test creating a product with only required fields"""
    with app.app_context():
        product_data = {
            'name_am': 'Minimal Product',
            'name_en': 'Minimal Product',
            'price': 1000,
            'category': 'ሌላ'
        }
        
        product_id = Product.create(product_data)
        assert product_id is not None
        
        product = Product.get_by_id(product_id)
        assert product is not None
        assert product['name_am'] == 'Minimal Product'
        assert product['price'] == 1000


def test_product_get_all(app):
    """Test getting all products"""
    with app.app_context():
        products = Product.get_all()
        assert isinstance(products, list)
        # Should return at least the products created in other tests
        assert len(products) >= 0


def test_product_get_by_id_not_found(app):
    """Test getting a product with non-existent ID"""
    with app.app_context():
        product = Product.get_by_id(99999)
        assert product is None


def test_product_get_by_category(app):
    """Test getting products by category"""
    with app.app_context():
        # Create a product in a specific category
        product_data = {
            'name_am': 'Category Test',
            'name_en': 'Category Test',
            'price': 2000,
            'category': 'አልጋ'
        }
        product_id = Product.create(product_data)
        
        # Get products by category
        products = Product.get_by_category('አልጋ')
        assert isinstance(products, list)
        assert len(products) > 0
        
        # Verify our product is in the list
        found = any(p['id'] == product_id for p in products)
        assert found is True


def test_product_search(app):
    """Test searching products by name"""
    with app.app_context():
        # Create a product with unique name
        unique_name = 'UniqueSearchTestProduct_' + str(pytest.gen)
        product_data = {
            'name_am': unique_name,
            'name_en': unique_name,
            'price': 1500,
            'category': 'ሌላ'
        }
        Product.create(product_data)
        
        # Search for the product
        results = Product.search(unique_name[:10])
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Verify the search term appears in results
        found = any(unique_name in str(p['name_am']) or unique_name in str(p['name_en']) for p in results)
        assert found is True


def test_product_update(app):
    """Test updating a product"""
    with app.app_context():
        # Create product
        product_data = {
            'name_am': 'Original Name',
            'name_en': 'Original Name',
            'price': 1000,
            'category': 'ሶፋ'
        }
        product_id = Product.create(product_data)
        
        # Update product
        update_data = {
            'name_am': 'Updated Name',
            'name_en': 'Updated Name',
            'price': 2000,
            'old_price': 3000,
            'category': 'አልጋ'
        }
        result = Product.update(product_id, update_data)
        assert result is True
        
        # Verify update
        product = Product.get_by_id(product_id)
        assert product['name_am'] == 'Updated Name'
        assert product['price'] == 2000
        assert product['old_price'] == 3000
        assert product['category'] == 'አልጋ'


def test_product_delete(app):
    """Test deleting a product"""
    with app.app_context():
        # Create product
        product_data = {
            'name_am': 'To Delete',
            'name_en': 'To Delete',
            'price': 1000,
            'category': 'ሌላ'
        }
        product_id = Product.create(product_data)
        
        # Verify product exists
        product = Product.get_by_id(product_id)
        assert product is not None
        
        # Delete product
        result = Product.delete(product_id)
        assert result is True
        
        # Verify deletion
        product = Product.get_by_id(product_id)
        assert product is None


def test_product_update_stock(app):
    """Test updating product stock quantity"""
    with app.app_context():
        product_data = {
            'name_am': 'Stock Test',
            'name_en': 'Stock Test',
            'price': 1000,
            'stock': 10,
            'category': 'ሌላ'
        }
        product_id = Product.create(product_data)
        
        result = Product.update_stock(product_id, -3)
        assert result is True
        
        product = Product.get_by_id(product_id)
        assert product['stock'] == 7


def test_product_get_featured(app):
    """Test getting featured products"""
    with app.app_context():
        featured_products = Product.get_featured()
        assert isinstance(featured_products, list)


def test_product_get_low_stock(app):
    """Test getting low stock products"""
    with app.app_context():
        low_stock = Product.get_low_stock(threshold=5)
        assert isinstance(low_stock, list)


# ==================== AD MODEL TESTS ====================

def test_ad_creation(app):
    """Test creating an advertisement"""
    with app.app_context():
        ad_id = Ad.create('Test advertisement message with emoji 🎉')
        assert ad_id is not None
        
        ads = Ad.get_all()
        assert len(ads) > 0
        assert ads[0]['text'] == 'Test advertisement message with emoji 🎉'


def test_ad_creation_with_media(app):
    """Test creating an advertisement with media"""
    with app.app_context():
        ad_id = Ad.create('Video advertisement', media='test_video.mp4')
        assert ad_id is not None
        
        ad = Ad.get_by_id(ad_id)
        assert ad is not None
        assert ad['media'] == 'test_video.mp4'


def test_ad_get_all(app):
    """Test getting all advertisements"""
    with app.app_context():
        Ad.create('First ad')
        Ad.create('Second ad')
        
        ads = Ad.get_all()
        assert isinstance(ads, list)
        assert len(ads) >= 2


def test_ad_get_active(app):
    """Test getting only active advertisements"""
    with app.app_context():
        ads = Ad.get_active()
        assert isinstance(ads, list)
        # Active ads should only show is_active = 1


def test_ad_get_by_id(app):
    """Test getting advertisement by ID"""
    with app.app_context():
        ad_id = Ad.create('Test ad for ID lookup')
        
        ad = Ad.get_by_id(ad_id)
        assert ad is not None
        assert ad['id'] == ad_id
        assert ad['text'] == 'Test ad for ID lookup'


def test_ad_update(app):
    """Test updating an advertisement"""
    with app.app_context():
        ad_id = Ad.create('Original text')
        
        update_data = {
            'title': 'Updated Title',
            'text': 'Updated text',
            'media': 'new_video.mp4',
            'sort_order': 5
        }
        result = Ad.update(ad_id, update_data)
        assert result is True
        
        ad = Ad.get_by_id(ad_id)
        assert ad['text'] == 'Updated text'
        assert ad['media'] == 'new_video.mp4'


def test_ad_toggle_active(app):
    """Test toggling advertisement active status"""
    with app.app_context():
        ad_id = Ad.create('Toggle test ad')
        
        # Toggle to inactive
        result = Ad.toggle_active(ad_id)
        assert result is True
        
        ad = Ad.get_by_id(ad_id)
        assert ad['is_active'] == 0
        
        # Toggle back to active
        Ad.toggle_active(ad_id)
        ad = Ad.get_by_id(ad_id)
        assert ad['is_active'] == 1


def test_ad_delete(app):
    """Test deleting an advertisement"""
    with app.app_context():
        ad_id = Ad.create('Ad to delete')
        
        # Verify exists
        ad = Ad.get_by_id(ad_id)
        assert ad is not None
        
        # Delete
        result = Ad.delete(ad_id)
        assert result is True
        
        # Verify deleted
        ad = Ad.get_by_id(ad_id)
        assert ad is None


# ==================== ORDER MODEL TESTS ====================

def test_order_creation(app):
    """Test creating an order"""
    with app.app_context():
        items = [{'name': 'Product 1', 'price': 1000, 'quantity': 2, 'total': 2000}]
        
        order_data = {
            'order_number': 'ORD-TEST-001',
            'customer_name': 'Test Customer',
            'customer_phone': '0912345678',
            'customer_address': 'ወሎ ደሴ ኩታበር',
            'customer_email': 'test@example.com',
            'items': items,
            'subtotal': 2000,
            'shipping_cost': 200,
            'total': 2200,
            'notes': 'Test order notes'
        }
        
        result = Order.create(order_data)
        assert result is True


def test_order_get_all(app):
    """Test getting all orders"""
    with app.app_context():
        orders = Order.get_all()
        assert isinstance(orders, list)


def test_order_get_by_id(app):
    """Test getting an order by ID"""
    with app.app_context():
        # Create order first
        items = [{'name': 'Test', 'price': 500, 'quantity': 1, 'total': 500}]
        order_data = {
            'order_number': 'ORD-TEST-002',
            'customer_name': 'ID Test',
            'customer_phone': '0912345678',
            'items': items,
            'subtotal': 500,
            'shipping_cost': 0,
            'total': 500
        }
        Order.create(order_data)
        
        orders = Order.get_all()
        if len(orders) > 0:
            order_id = orders[0]['id']
            order = Order.get_by_id(order_id)
            assert order is not None
            assert order['id'] == order_id


def test_order_get_by_order_number(app):
    """Test getting an order by order number"""
    with app.app_context():
        order_number = 'ORD-UNIQUE-12345'
        items = [{'name': 'Unique Order', 'price': 1000, 'quantity': 1, 'total': 1000}]
        order_data = {
            'order_number': order_number,
            'customer_name': 'Number Test',
            'customer_phone': '0912345678',
            'items': items,
            'subtotal': 1000,
            'shipping_cost': 0,
            'total': 1000
        }
        Order.create(order_data)
        
        order = Order.get_by_order_number(order_number)
        assert order is not None
        assert order['order_number'] == order_number


def test_order_update_status(app):
    """Test updating order status"""
    with app.app_context():
        items = [{'name': 'Status Test', 'price': 500, 'quantity': 1, 'total': 500}]
        order_data = {
            'order_number': 'ORD-STATUS-001',
            'customer_name': 'Status Test',
            'customer_phone': '0912345678',
            'items': items,
            'subtotal': 500,
            'shipping_cost': 0,
            'total': 500,
            'status': 'pending'
        }
        Order.create(order_data)
        
        orders = Order.get_all()
        if len(orders) > 0:
            order_id = orders[0]['id']
            result = Order.update_status(order_id, 'confirmed')
            assert result is True
            
            order = Order.get_by_id(order_id)
            assert order['status'] == 'confirmed'


def test_order_get_by_status(app):
    """Test getting orders by status"""
    with app.app_context():
        pending_orders = Order.get_by_status('pending')
        assert isinstance(pending_orders, list)
        
        confirmed_orders = Order.get_by_status('confirmed')
        assert isinstance(confirmed_orders, list)


def test_order_delete(app):
    """Test deleting an order"""
    with app.app_context():
        items = [{'name': 'Delete Test', 'price': 100, 'quantity': 1, 'total': 100}]
        order_data = {
            'order_number': 'ORD-DELETE-001',
            'customer_name': 'Delete Test',
            'customer_phone': '0912345678',
            'items': items,
            'subtotal': 100,
            'shipping_cost': 0,
            'total': 100
        }
        Order.create(order_data)
        
        orders = Order.get_all()
        if len(orders) > 0:
            order_id = orders[0]['id']
            result = Order.delete(order_id)
            assert result is True
            
            order = Order.get_by_id(order_id)
            assert order is None