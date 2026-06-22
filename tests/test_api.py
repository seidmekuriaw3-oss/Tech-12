"""
API Tests for Ethiosadat Furniture

This module contains tests for all API endpoints including:
- Products API
- Cart API
- Search API
- Categories API
"""

import pytest
import json


# ==================== PRODUCTS API TESTS ====================

def test_api_products(client):
    """Test GET /api/products - returns all products"""
    response = client.get('/api/products')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'success' in data
    assert data['success'] is True
    assert 'products' in data
    assert isinstance(data['products'], list)
    assert 'count' in data


def test_api_products_with_category(client):
    """Test GET /api/products?category=ሶፋ - filters by category"""
    response = client.get('/api/products?category=ሶፋ')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'products' in data


def test_api_products_with_limit(client):
    """Test GET /api/products?limit=5 - limits results"""
    response = client.get('/api/products?limit=5')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['products']) <= 5


def test_api_product_detail(client, sample_product_db):
    """Test GET /api/product/<id> - returns single product"""
    response = client.get(f'/api/product/{sample_product_db}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'product' in data
    assert data['product']['id'] == sample_product_db


def test_api_product_detail_not_found(client):
    """Test GET /api/product/99999 - returns 404 for non-existent product"""
    response = client.get('/api/product/99999')
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'error' in data


# ==================== CART API TESTS ====================

def test_api_cart_count_empty(client):
    """Test GET /api/cart/count - returns zero for empty cart"""
    response = client.get('/api/cart/count')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'cart_count' in data
    assert isinstance(data['cart_count'], int)


def test_api_cart_count_populated(populated_cart):
    """Test GET /api/cart/count - returns correct count for populated cart"""
    response = populated_cart.get('/api/cart/count')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['cart_count'] == 2


def test_api_cart_get(client):
    """Test GET /api/cart - returns cart contents"""
    response = client.get('/api/cart')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'cart' in data
    assert 'subtotal' in data
    assert 'shipping' in data
    assert 'total' in data
    assert 'count' in data


def test_api_add_to_cart(client):
    """Test POST /api/cart/add - adds item to cart"""
    response = client.post('/api/cart/add', 
        json={
            'product_id': '999',
            'product_name': 'Test Product',
            'product_price': 1000,
            'quantity': 1
        },
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data.get('success') is True
    assert 'message' in data
    assert 'cart_count' in data


def test_api_add_to_cart_invalid_data(client):
    """Test POST /api/cart/add - returns error for invalid data"""
    response = client.post('/api/cart/add', 
        json={},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data.get('success') is False
    assert 'error' in data


def test_api_add_to_cart_missing_product_id(client):
    """Test POST /api/cart/add - returns error when product_id missing"""
    response = client.post('/api/cart/add', 
        json={
            'product_name': 'Test Product',
            'product_price': 1000,
            'quantity': 1
        },
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data.get('success') is False


def test_api_update_cart(client, populated_cart):
    """Test POST /api/cart/update - updates cart item quantity"""
    response = populated_cart.post('/api/cart/update',
        json={
            'product_id': '1',
            'quantity': 5
        },
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data.get('success') is True
    assert 'subtotal' in data
    assert 'total' in data


def test_api_remove_from_cart(client, populated_cart):
    """Test POST /api/cart/remove - removes item from cart"""
    response = populated_cart.post('/api/cart/remove',
        json={'product_id': '1'},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data.get('success') is True
    assert 'subtotal' in data
    assert 'total' in data


def test_api_remove_from_cart_not_found(client):
    """Test POST /api/cart/remove - returns error for non-existent item"""
    response = client.post('/api/cart/remove',
        json={'product_id': '99999'},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert data.get('success') is False


# ==================== SEARCH API TESTS ====================

def test_api_search(client):
    """Test GET /api/search?q=test - returns search results"""
    response = client.get('/api/search?q=test')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'products' in data
    assert 'count' in data
    assert 'query' in data


def test_api_search_empty_query(client):
    """Test GET /api/search?q= - returns empty results for empty query"""
    response = client.get('/api/search?q=')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['products'] == []
    assert data['count'] == 0


def test_api_search_no_results(client):
    """Test GET /api/search?q=nonexistent - returns empty for no matches"""
    response = client.get('/api/search?q=xyzabcdefghijk')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['count'] == 0


# ==================== CATEGORIES API TESTS ====================

def test_api_categories(client):
    """Test GET /api/categories - returns all categories"""
    response = client.get('/api/categories')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'categories' in data
    assert isinstance(data['categories'], list)


# ==================== ERROR HANDLING TESTS ====================

def test_api_404(client):
    """Test non-existent API endpoint returns 404"""
    response = client.get('/api/nonexistent')
    assert response.status_code == 404


def test_api_method_not_allowed(client):
    """Test wrong HTTP method returns 405"""
    response = client.get('/api/cart/add')  # POST only
    assert response.status_code == 405