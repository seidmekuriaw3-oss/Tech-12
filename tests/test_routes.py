"""
Route Tests for Ethiosadat Furniture

This module contains tests for all route endpoints including:
- Customer routes (home, about, contact, cart, etc.)
- Authentication routes (login, logout)
- Admin routes (dashboard, products, orders, etc.)
- Error handlers (404, 500)
- Language switching
"""

import pytest

from database.db import get_db


# ==================== CUSTOMER ROUTES TESTS ====================

def test_index_route(client):
    """Test GET / - home page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Ethiosadat' in response.data or b'Furniture' in response.data


def test_home_page_renders_translated_ads(client, app):
    """The home page should render translated ad titles/descriptions when present."""
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO advertisements (
                title, title_am, description, description_am, image, link, sort_order, is_active,
                start_date, end_date, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW() + INTERVAL '7 days', NOW())
            """,
            ('', 'ለበጋ ቅናሽ', '', 'እስከ 30% ቅናሽ በምርቶች', '', '/products', 1, 1),
        )
        db.commit()

    response = client.get('/')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'ለበጋ ቅናሽ' in html
    assert 'እስከ 30% ቅናሽ በምርቶች' in html


def test_about_route(client):
    """Test GET /about - about page loads successfully"""
    response = client.get('/about')
    assert response.status_code == 200
    assert b'About' in response.data or 'ስለ'.encode('utf-8') in response.data


def test_contact_route(client):
    """Test GET /contact - contact page loads successfully"""
    response = client.get('/contact')
    assert response.status_code == 200
    assert b'Contact' in response.data or 'አግኙን'.encode('utf-8') in response.data


def test_contact_route_post(client):
    """Test POST /contact - submits contact form"""
    response = client.post('/contact', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'phone': '0912345678',
        'message': 'This is a test message'
    }, follow_redirects=True)
    # Should redirect to WhatsApp or show success message
    assert response.status_code == 200


def test_cart_route(client):
    """Test GET /cart - cart page loads successfully"""
    response = client.get('/cart')
    assert response.status_code == 200
    assert b'Cart' in response.data or 'ጋሪ'.encode('utf-8') in response.data


def test_category_route(client):
    """Test GET /category/<category> - category page loads"""
    response = client.get('/category/all')
    assert response.status_code == 200
    
    response = client.get('/category/ሶፋ')
    assert response.status_code == 200
    
    response = client.get('/category/አልጋ')
    assert response.status_code == 200


def test_category_route_invalid(client):
    """Test GET /category/invalid - returns 404 for invalid category"""
    response = client.get('/category/invalid-category-name')
    # Should redirect or show 404
    assert response.status_code in [302, 404]


def test_product_detail_route(client):
    """Test GET /product/<id> - product detail page"""
    # Try with non-existent product (should redirect or 404)
    response = client.get('/product/99999')
    assert response.status_code in [302, 404]


def test_search_route(client):
    """Test GET /search?q=query - search results page"""
    response = client.get('/search?q=sofa')
    assert response.status_code == 200
    
    response = client.get('/search?q=')
    assert response.status_code == 302  # Redirect to home


# ==================== AUTHENTICATION ROUTES TESTS ====================

def test_login_route_get(client):
    """Test GET /login - login page loads"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data or 'ግባ'.encode('utf-8') in response.data


def test_login_route_post_invalid(client):
    """Test POST /login - invalid password shows error"""
    response = client.post('/login', data={'password': 'wrongpassword'}, follow_redirects=True)
    assert response.status_code == 200
    # Should show error message
    assert b'Invalid' in response.data or 'ስህተት'.encode('utf-8') in response.data


def test_login_route_post_valid(client, auth):
    """Test POST /login - valid password redirects to admin"""
    response = auth.login(password='test1234')
    # Follow redirects
    assert response.status_code == 200


def test_logout_route(client, auth):
    """Test GET /logout - logs out admin"""
    auth.login()
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200


# ==================== ADMIN ROUTES TESTS ====================

def test_admin_route_requires_login(client):
    """Test GET /admin - redirects to login when not authenticated"""
    response = client.get('/admin')
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.location


def test_admin_route_with_login(client, auth):
    """Test GET /admin - accessible after login"""
    auth.login()
    response = client.get('/admin')
    assert response.status_code == 200
    assert b'Dashboard' in response.data or 'ዳሽቦርድ'.encode('utf-8') in response.data


def test_admin_products_route(client, auth):
    """Test GET /admin/products - products list page"""
    auth.login()
    response = client.get('/admin/products')
    assert response.status_code == 200


def test_admin_ads_route(client, auth):
    """Test GET /admin/ads - ads management page"""
    auth.login()
    response = client.get('/admin/ads')
    assert response.status_code == 200


def test_admin_orders_route(client, auth):
    """Test GET /admin/orders - orders list page"""
    auth.login()
    response = client.get('/admin/orders')
    assert response.status_code == 200


def test_admin_reports_route(client, auth):
    """Test GET /admin/reports - reports page"""
    auth.login()
    response = client.get('/admin/reports')
    assert response.status_code == 200


def test_admin_settings_route(client, auth):
    """Test GET /admin/settings - settings page"""
    auth.login()
    response = client.get('/admin/settings')
    assert response.status_code == 200


# ==================== ADD TO CART TESTS ====================

def test_add_to_cart(client):
    """Test POST /cart/add - adds item to cart"""
    response = client.post('/cart/add', data={
        'product_id': '1',
        'product_name': 'Test Product',
        'product_price': '1000',
        'quantity': '1'
    }, follow_redirects=True)
    assert response.status_code == 200


def test_add_to_cart_ajax(client):
    """Test POST /cart/add with AJAX header - returns JSON"""
    response = client.post('/cart/add', 
        data={
            'product_id': '1',
            'product_name': 'Test Product',
            'product_price': '1000',
            'quantity': '1'
        },
        headers={'X-Requested-With': 'XMLHttpRequest'}
    )
    assert response.status_code == 200
    assert response.is_json


def test_update_cart(client):
    """Test POST /cart/update - updates cart item quantity"""
    # First add an item
    client.post('/cart/add', data={
        'product_id': '1',
        'product_name': 'Test',
        'product_price': '1000',
        'quantity': '1'
    })
    
    # Then update it
    response = client.post('/cart/update', data={
        'product_id': '1',
        'quantity': '3'
    }, follow_redirects=True)
    assert response.status_code == 200


def test_remove_from_cart(client):
    """Test GET /cart/remove/<id> - removes item from cart"""
    response = client.get('/cart/remove/1', follow_redirects=True)
    assert response.status_code == 200


def test_clear_cart(client):
    """Test GET /cart/clear - clears all cart items"""
    response = client.get('/cart/clear', follow_redirects=True)
    assert response.status_code == 200


def test_checkout_route_get(client):
    """Test GET /checkout - checkout page loads"""
    response = client.get('/checkout')
    assert response.status_code == 200


def test_checkout_route_post(client):
    """Test POST /checkout - submits order"""
    response = client.post('/checkout', data={
        'customer_name': 'Test Customer',
        'customer_phone': '0912345678',
        'customer_address': 'ወሎ ደሴ ኩታበር',
        'customer_email': 'test@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200


# ==================== LANGUAGE SWITCH TESTS ====================

def test_language_switch_to_english(client):
    """Test GET /set_lang/en - switches language to English"""
    response = client.get('/set_lang/en', follow_redirects=True)
    assert response.status_code == 200
    # Check that language changed (session should have lang='en')


def test_language_switch_to_amharic(client):
    """Test GET /set_lang/am - switches language to Amharic"""
    response = client.get('/set_lang/am', follow_redirects=True)
    assert response.status_code == 200


def test_language_switch_invalid(client):
    """Test GET /set_lang/invalid - handles invalid language"""
    response = client.get('/set_lang/invalid', follow_redirects=True)
    assert response.status_code == 200  # Should fall back to default


# ==================== STATIC FILES TESTS ====================

def test_static_css(client):
    """Test static CSS files are accessible"""
    response = client.get('/static/css/style.css')
    assert response.status_code == 200
    assert response.content_type == 'text/css'


def test_static_js(client):
    """Test static JS files are accessible"""
    response = client.get('/static/js/main.js')
    assert response.status_code == 200
    assert response.content_type == 'application/javascript'


def test_favicon(client):
    """Test favicon route"""
    response = client.get('/favicon.ico')
    # Favicon may return 200 or 204 if not found
    assert response.status_code in [200, 204]


# ==================== ERROR HANDLER TESTS ====================

def test_404_handler(client):
    """Test 404 page for non-existent route"""
    response = client.get('/nonexistent-page-12345')
    assert response.status_code == 404
    # Should show custom 404 page
    assert b'404' in response.data or b'Page Not Found' in response.data or 'አልተገኘም'.encode('utf-8') in response.data


def test_405_handler(client):
    """Test 405 for wrong HTTP method"""
    # POST to GET-only endpoint
    response = client.post('/about')
    assert response.status_code == 405


# ==================== HEALTH CHECK TESTS ====================

def test_health_check(client):
    """Test GET /health - health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.is_json


# ==================== ROBOTS.TXT AND SITEMAP TESTS ====================

def test_robots_txt(client):
    """Test GET /robots.txt - robots file"""
    response = client.get('/robots.txt')
    assert response.status_code == 200
    assert 'User-agent' in response.text


def test_sitemap_xml(client):
    """Test GET /sitemap.xml - sitemap file"""
    response = client.get('/sitemap.xml')
    assert response.status_code == 200
    assert 'xml' in response.content_type