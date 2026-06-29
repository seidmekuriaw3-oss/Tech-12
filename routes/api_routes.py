"""
API Routes for SEMIRA FASHION

This module contains all API endpoints for AJAX requests including:
- Product search and filtering
- Cart operations (add, remove, update)
- User authentication (login, register)
- Order placement
- Contact form submission
- Branch information
"""

from flask import Blueprint, request, jsonify, session, current_app
from database.db import get_db
from database.models import Product, Order
from middleware.auth import is_admin
from routes.shared import FREE_SHIPPING_THRESHOLD, SHIPPING_COST, calc_cart_totals, USER_DISCOUNT_RATE
from extensions import limiter
import json
import re

api_bp = Blueprint('api', __name__)


# ==================== PRODUCT API ====================

@api_bp.route('/products/search')
def api_search_products():
    """Search products by query"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'success': True, 'products': [], 'count': 0})
    
    db = get_db()
    cursor = db.cursor()
    
    search_term = f'%{query}%'
    cursor.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE (p.name ILIKE %s OR p.name_am ILIKE %s OR p.name_ar ILIKE %s)
        AND p.is_active = 1
        ORDER BY p.id DESC
        LIMIT 50
    """, (search_term, search_term, search_term))
    
    products = cursor.fetchall()
    
    # Convert to list of dicts
    product_list = []
    for p in products:
        product_list.append({
            'id': p['id'],
            'name': p['name'],
            'name_am': p['name_am'],
            'name_ar': p['name_ar'],
            'price': p['price'],
            'compare_price': p['compare_price'],
            'thumbnail': p['thumbnail'],
            'stock_quantity': p['stock_quantity'],
            'category_name': p['category_name']
        })
    
    return jsonify({
        'success': True,
        'products': product_list,
        'count': len(product_list),
        'query': query
    })


@api_bp.route('/products/filter')
@api_bp.route('/search-products')
def api_filter_products():
    """Filter products by category, price range, etc."""
    category_id = request.args.get('category_id', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort_by', 'newest')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    db = get_db()
    cursor = db.cursor()
    
    # Build query (include avg rating and review count via subquery)
    query = """
        SELECT p.*, c.name as category_name,
            COALESCE(r.avg_rating, 0) as rating,
            COALESCE(r.review_count, 0) as reviews
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN (
            SELECT product_id,
                   ROUND(AVG(rating)::numeric, 1) as avg_rating,
                   COUNT(*) as review_count
            FROM reviews
            WHERE is_approved = 1
            GROUP BY product_id
        ) r ON r.product_id = p.id
        WHERE p.is_active = 1
    """
    params = []
    
    if category_id:
        query += " AND p.category_id = %s"
        params.append(category_id)
    
    if min_price is not None:
        query += " AND p.price >= %s"
        params.append(min_price)
    
    if max_price is not None:
        query += " AND p.price <= %s"
        params.append(max_price)
    
    # Add sorting
    if sort_by == 'price_asc':
        query += " ORDER BY p.price ASC"
    elif sort_by == 'price_desc':
        query += " ORDER BY p.price DESC"
    elif sort_by == 'name_asc':
        query += " ORDER BY p.name ASC"
    elif sort_by == 'oldest':
        query += " ORDER BY p.id ASC"
    else:  # newest
        query += " ORDER BY p.id DESC"
    
    query += " LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    products = cursor.fetchall()
    
    # Get total count
    count_query = """
        SELECT COUNT(*) as total
        FROM products p
        WHERE p.is_active = 1
    """
    count_params = []
    
    if category_id:
        count_query += " AND p.category_id = %s"
        count_params.append(category_id)
    
    if min_price is not None:
        count_query += " AND p.price >= %s"
        count_params.append(min_price)
    
    if max_price is not None:
        count_query += " AND p.price <= %s"
        count_params.append(max_price)
    
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()['total']
    
    # Convert products to list
    product_list = []
    for p in products:
        # Get discount percentage if compare_price exists
        discount = None
        if p['compare_price'] and p['compare_price'] > p['price']:
            discount = int(((p['compare_price'] - p['price']) / p['compare_price']) * 100)
        
        product_list.append({
            'id': p['id'],
            'name': p['name'],
            'name_am': p['name_am'],
            'name_ar': p['name_ar'],
            'price': p['price'],
            'compare_price': p['compare_price'],
            'discount': discount,
            'thumbnail': p['thumbnail'],
            'stock_quantity': p['stock_quantity'],
            'category_id': p['category_id'],
            'category_name': p['category_name'],
            'is_featured': bool(p['is_featured']),
            'is_new': bool(p['is_new']),
            'rating': float(p['rating']) if p['rating'] else 0,
            'reviews': int(p['reviews']) if p['reviews'] else 0
        })
    
    return jsonify({
        'success': True,
        'products': product_list,
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': offset + limit < total
    })


@api_bp.route('/products/<int:pid>')
def api_get_product(pid):
    """Get single product details"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT p.*, c.name as category_name, c.name_am as category_name_am
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = %s AND p.is_active = 1
    """, (pid,))
    
    product = cursor.fetchone()
    
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    
    # Get discount percentage
    discount = None
    if product['compare_price'] and product['compare_price'] > product['price']:
        discount = int(((product['compare_price'] - product['price']) / product['compare_price']) * 100)
    
    # Parse images if stored as JSON
    images = []
    if product['images']:
        try:
            images = json.loads(product['images'])
        except (json.JSONDecodeError, ValueError):
            images = [product['thumbnail']] if product['thumbnail'] else []
    
    return jsonify({
        'success': True,
        'product': {
            'id': product['id'],
            'name': product['name'],
            'name_am': product['name_am'],
            'name_ar': product['name_ar'],
            'description': product['description'],
            'description_am': product['description_am'],
            'description_ar': product['description_ar'],
            'price': product['price'],
            'compare_price': product['compare_price'],
            'discount': discount,
            'thumbnail': product['thumbnail'],
            'images': images,
            'stock_quantity': product['stock_quantity'],
            'category_id': product['category_id'],
            'category_name': product['category_name'],
            'material': product['material'],
            'color': product['color'],
            'sku': product['sku'],
            'is_featured': bool(product['is_featured']),
            'is_new': bool(product['is_new'])
        }
    })


# ==================== CART API ====================

@api_bp.route('/cart/add', methods=['GET', 'POST'])
def api_cart_add():
    """Add product to cart"""
    if request.method == 'GET':
        product_id = request.args.get('product_id')
        quantity = request.args.get('quantity', 1)
    else:
        data = request.get_json(silent=True) or {}
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid product ID or quantity'}), 400

    if not product_id:
        return jsonify({'success': False, 'error': 'Product ID required'}), 400

    # Check product exists and has enough stock
    db_check = get_db()
    cur_check = db_check.cursor()
    cur_check.execute("SELECT id, stock_quantity, is_active FROM products WHERE id = %s", (product_id,))
    prod_check = cur_check.fetchone()
    if not prod_check or not prod_check['is_active']:
        return jsonify({'success': False, 'error': 'Product not available'}), 404

    # For logged-in users, account for what's already in cart
    existing_qty = 0
    if session.get('user_id'):
        cur_check.execute("SELECT quantity FROM cart_items WHERE user_id = %s AND product_id = %s",
                          (session['user_id'], product_id))
        ex = cur_check.fetchone()
        if ex:
            existing_qty = ex['quantity']
    else:
        existing_qty = session.get('cart', {}).get(str(product_id), 0)

    if existing_qty + quantity > prod_check['stock_quantity']:
        avail = prod_check['stock_quantity'] - existing_qty
        if avail <= 0:
            return jsonify({'success': False, 'error': 'No more stock available'}), 400
        return jsonify({'success': False, 'error': f'Only {avail} more item(s) available'}), 400

    # Check if user is logged in
    if session.get('user_id'):
        # Save to database
        db = get_db()
        cursor = db.cursor()
        
        # Check if product already in cart
        cursor.execute("""
            SELECT id, quantity FROM cart_items 
            WHERE user_id = %s AND product_id = %s
        """, (session['user_id'], product_id))
        
        existing = cursor.fetchone()
        
        if existing:
            new_quantity = existing['quantity'] + quantity
            cursor.execute("""
                UPDATE cart_items SET quantity = %s WHERE id = %s
            """, (new_quantity, existing['id']))
        else:
            cursor.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (session['user_id'], product_id, quantity))
        
        db.commit()
    else:
        # Save to session cart
        cart = session.get('cart', {})
        cart_key = str(product_id)
        
        if cart_key in cart:
            cart[cart_key] += quantity
        else:
            cart[cart_key] = quantity
        
        session['cart'] = cart
        session.modified = True
    
    # Compute cart count to return
    try:
        if session.get('user_id'):
            db2 = get_db()
            cur2 = db2.cursor()
            cur2.execute("SELECT COALESCE(SUM(quantity),0) as c FROM cart_items WHERE user_id=%s", (session['user_id'],))
            row2 = cur2.fetchone()
            cart_count = int(row2['c']) if row2 else 0
        else:
            cart_count = sum(int(v) for v in session.get('cart', {}).values())
    except Exception:
        cart_count = 0

    return jsonify({'success': True, 'message': 'Product added to cart', 'cart_count': cart_count})


def _get_cart_totals_data(product_id_removed=None):
    """
    Helper: compute and return cart totals dict for JSON responses.
    If product_id_removed is set, that item is excluded (used after a remove).
    """
    from routes.shared import calc_cart_totals
    is_logged_in = bool(session.get('user_id'))
    subtotal = 0.0
    cart_count = 0

    try:
        db = get_db()
        cursor = db.cursor()

        if is_logged_in:
            cursor.execute("""
                SELECT SUM(p.price * ci.quantity) as s, SUM(ci.quantity) as c
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.id
                WHERE ci.user_id = %s
            """, (session['user_id'],))
            row = cursor.fetchone()
            subtotal = float(row['s'] or 0)
            cart_count = int(row['c'] or 0)
        else:
            cart = session.get('cart', {})
            if cart:
                placeholders = ','.join(['%s'] * len(cart))
                cursor.execute(
                    f"SELECT id, price FROM products WHERE id IN ({placeholders})",
                    list(cart.keys())
                )
                for p in cursor.fetchall():
                    qty = cart.get(str(p['id']), 0)
                    subtotal += float(p['price']) * qty
                    cart_count += qty
    except Exception:
        pass

    totals = calc_cart_totals(subtotal, is_logged_in=is_logged_in)
    totals['count'] = cart_count
    return totals


@api_bp.route('/cart/remove', methods=['GET', 'POST'])
def api_cart_remove():
    """Remove product from cart"""
    try:
        if request.method == 'GET':
            product_id = request.args.get('product_id')
        else:
            data = request.get_json(silent=True) or {}
            product_id = data.get('product_id')
        try:
            product_id = int(product_id) if product_id else None
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid product ID'}), 400

        if not product_id:
            return jsonify({'success': False, 'error': 'Product ID required'}), 400

        if session.get('user_id'):
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                DELETE FROM cart_items WHERE user_id = %s AND product_id = %s
            """, (session['user_id'], product_id))
            db.commit()
        else:
            cart = session.get('cart', {})
            cart_key = str(product_id)
            if cart_key in cart:
                del cart[cart_key]
            session['cart'] = cart
            session.modified = True

        totals = _get_cart_totals_data()
        totals['success'] = True
        totals['message'] = 'Product removed from cart'
        return jsonify(totals)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/cart/update', methods=['GET', 'POST'])
def api_cart_update():
    """Update product quantity in cart"""
    try:
        if request.method == 'GET':
            product_id = request.args.get('product_id')
            quantity = request.args.get('quantity', 1)
        else:
            data = request.get_json(silent=True) or {}
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
        try:
            product_id = int(product_id) if product_id else None
            quantity = int(quantity)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid product ID or quantity'}), 400

        if not product_id:
            return jsonify({'success': False, 'error': 'Product ID required'}), 400

        if quantity <= 0:
            return api_cart_remove()

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT price, stock_quantity FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404

        if quantity > product['stock_quantity']:
            return jsonify({'success': False, 'error': f'Only {product["stock_quantity"]} items available'}), 400

        item_price = float(product['price'])

        if session.get('user_id'):
            cursor.execute("""
                UPDATE cart_items SET quantity = %s
                WHERE user_id = %s AND product_id = %s
            """, (quantity, session['user_id'], product_id))
            db.commit()
        else:
            cart = session.get('cart', {})
            cart[str(product_id)] = quantity
            session['cart'] = cart
            session.modified = True

        totals = _get_cart_totals_data()
        is_logged_in = bool(session.get('user_id'))
        discounted_price = item_price * (1 - USER_DISCOUNT_RATE) if is_logged_in else item_price
        item_total = round(discounted_price * quantity, 2)

        totals['success'] = True
        totals['message'] = 'Cart updated'
        totals['item_total'] = item_total
        return jsonify(totals)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/cart')
def api_get_cart():
    """Get current cart contents"""
    cart_items = []
    subtotal = 0
    
    if session.get('user_id'):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT ci.*, p.name, p.name_am, p.name_ar, p.price, p.compare_price, p.thumbnail
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = %s AND p.is_active = 1
        """, (session['user_id'],))
        
        rows = cursor.fetchall()
        for row in rows:
            item_subtotal = row['price'] * row['quantity']
            subtotal += item_subtotal
            cart_items.append({
                'id': row['id'],
                'product_id': row['product_id'],
                'name': row['name'],
                'name_am': row['name_am'],
                'name_ar': row['name_ar'],
                'price': row['price'],
                'quantity': row['quantity'],
                'thumbnail': row['thumbnail'],
                'subtotal': item_subtotal
            })
    else:
        cart = session.get('cart', {})
        if cart:
            db = get_db()
            cursor = db.cursor()
            placeholders = ','.join(['%s'] * len(cart))
            cursor.execute(f"""
                SELECT id, name, name_am, name_ar, price, compare_price, thumbnail
                FROM products WHERE id IN ({placeholders}) AND is_active = 1
            """, list(cart.keys()))
            
            products = cursor.fetchall()
            for p in products:
                quantity = cart.get(str(p['id']), 0)
                if quantity > 0:
                    item_subtotal = p['price'] * quantity
                    subtotal += item_subtotal
                    cart_items.append({
                        'product_id': p['id'],
                        'name': p['name'],
                        'name_am': p['name_am'],
                        'name_ar': p['name_ar'],
                        'price': p['price'],
                        'quantity': quantity,
                        'thumbnail': p['thumbnail'],
                        'subtotal': item_subtotal
                    })
    
    # Apply 10% discount for logged in users (once, on original subtotal)
    is_logged_in = bool(session.get('user_id'))
    totals = calc_cart_totals(subtotal, is_logged_in=is_logged_in)

    return jsonify({
        'success': True,
        'items': cart_items,
        'item_count': len(cart_items),
        'subtotal': totals['subtotal'],
        'discount': totals['discount'],
        'subtotal_after_discount': totals['subtotal_after_discount'],
        'shipping_cost': totals['shipping_cost'],
        'total': totals['total'],
        'free_shipping': totals['free_shipping'],
        'free_shipping_threshold': totals['free_shipping_threshold'],
    })


@api_bp.route('/cart/count')
def api_cart_count():
    """Get cart item count"""
    count = 0
    
    if session.get('user_id'):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT SUM(quantity) as total FROM cart_items WHERE user_id = %s", (session['user_id'],))
        result = cursor.fetchone()
        count = result['total'] or 0
    else:
        cart = session.get('cart', {})
        count = sum(cart.values())
    
    return jsonify({'success': True, 'count': count})


# ==================== USER AUTH API ====================

@api_bp.route('/auth/register', methods=['POST'])
@limiter.limit("5 per minute; 20 per hour")
def api_register():
    """Register new user"""
    data = request.get_json(silent=True) or {}
    
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    
    # Validation
    if not full_name or not email or not password:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({'success': False, 'error': 'Invalid email address'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        return jsonify({'success': False, 'error': 'Email already registered'}), 400
    
    # Create user
    from werkzeug.security import generate_password_hash
    import random as _random
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    base_username = email.split('@')[0].lower()
    username = base_username
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        username = base_username + str(_random.randint(100, 9999))

    cursor.execute("""
        INSERT INTO users (username, full_name, email, phone, password_hash, is_admin, is_active)
        VALUES (%s, %s, %s, %s, %s, 0, 1) RETURNING id
    """, (username, full_name, email, phone, password_hash))
    row = cursor.fetchone()
    db.commit()
    user_id = row[0] if row else None
    
    # Auto login after registration
    session['user_id'] = user_id
    session['user_name'] = full_name
    session['user_email'] = email
    session['user_phone'] = phone
    
    return jsonify({
        'success': True,
        'message': 'Registration successful!',
        'user': {
            'id': user_id,
            'name': full_name,
            'email': email
        }
    })


@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute; 50 per hour")
def api_login():
    """Login user"""
    data = request.get_json(silent=True) or {}
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s AND is_active = 1", (email,))
    user = cursor.fetchone()
    
    if not user:
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
    
    from werkzeug.security import check_password_hash
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
    
    # Set session
    session['user_id'] = user['id']
    session['user_name'] = user['full_name']
    session['user_email'] = user['email']
    session['user_phone'] = user['phone']
    
    # Merge guest cart with user cart
    guest_cart = session.get('cart', {})
    if guest_cart:
        for product_id, quantity in guest_cart.items():
            cursor.execute("SELECT id, quantity FROM cart_items WHERE user_id = %s AND product_id = %s", 
                          (user['id'], product_id))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("UPDATE cart_items SET quantity = quantity + %s WHERE id = %s",
                             (quantity, existing['id']))
            else:
                cursor.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                             (user['id'], product_id, quantity))
        db.commit()
        session.pop('cart', None)
    
    return jsonify({
        'success': True,
        'message': 'Login successful!',
        'user': {
            'id': user['id'],
            'name': user['full_name'],
            'email': user['email']
        }
    })


@api_bp.route('/auth/logout', methods=['POST'])
def api_logout():
    """Logout user"""
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('user_phone', None)
    
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@api_bp.route('/auth/check')
def api_check_auth():
    """Check if user is authenticated"""
    if session.get('user_id'):
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'name': session.get('user_name'),
                'email': session.get('user_email')
            }
        })
    else:
        return jsonify({
            'success': True,
            'authenticated': False,
            'user': None
        })


# ==================== ORDER API ====================

@api_bp.route('/order/place', methods=['POST'])
@limiter.limit("10 per minute; 30 per hour")
def api_place_order():
    """Place a new order"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Please login to place order'}), 401
    
    data = request.get_json(silent=True) or {}
    
    # Get cart items
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT ci.*, p.price, p.name, p.stock_quantity
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.user_id = %s
        FOR UPDATE OF p
    """, (session['user_id'],))
    
    cart_items = cursor.fetchall()
    
    if not cart_items:
        return jsonify({'success': False, 'error': 'Cart is empty'}), 400

    # Stock check before processing
    for _ci in cart_items:
        if _ci['quantity'] > _ci['stock_quantity']:
            db.rollback()
            return jsonify({'success': False,
                            'error': f"Insufficient stock for {_ci['name']}"}), 400

    # Calculate totals — discount applied once via calc_cart_totals
    subtotal = 0
    items_list = []
    for item in cart_items:
        orig_price = item['price']
        subtotal += orig_price * item['quantity']
        items_list.append({
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'price': round(orig_price * (1 - USER_DISCOUNT_RATE), 2)
        })

    totals = calc_cart_totals(subtotal, is_logged_in=True)
    discount = totals['discount']
    shipping_cost = totals['shipping_cost']
    total = totals['total']
    
    # Generate order number
    from datetime import datetime
    import random
    import string
    order_number = f"{datetime.now().strftime('%Y%m%d')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
    
    # Create order
    cursor.execute("""
        INSERT INTO orders (
            order_number, user_id, status, payment_status,
            subtotal, discount, shipping_fee, total,
            shipping_address, shipping_city, shipping_phone, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (
        order_number, session['user_id'], 'pending', 'pending',
        subtotal, discount, shipping_cost, total,
        data.get('shipping_address', ''),
        data.get('shipping_city', ''),
        data.get('shipping_phone', session.get('user_phone', '')),
        data.get('notes', '')
    ))
    row = cursor.fetchone()
    order_id = row[0] if row else None
    
    # Create order items
    for item in items_list:
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
            VALUES (%s, %s, %s, %s)
        """, (order_id, item['product_id'], item['quantity'], item['price']))
        
        # Atomic stock decrement — guards against race conditions
        cursor.execute("""
            UPDATE products SET stock_quantity = stock_quantity - %s, sales_count = sales_count + %s
            WHERE id = %s AND stock_quantity >= %s
        """, (item['quantity'], item['quantity'], item['product_id'], item['quantity']))
        if cursor.rowcount == 0:
            db.rollback()
            return jsonify({'success': False,
                            'error': f"Insufficient stock for product #{item['product_id']}"}), 400
    
    # Low-stock check — query updated stock levels within this transaction
    try:
        ordered_pids = [it['product_id'] for it in items_list]
        if ordered_pids:
            from services.whatsapp_service import send_low_stock_alert as _stock_alert
            _ph = ','.join(['%s'] * len(ordered_pids))
            cursor.execute(
                f"""SELECT id, name_am, name, stock_quantity, low_stock_threshold
                    FROM products WHERE id IN ({_ph})
                    AND stock_quantity <= low_stock_threshold""",
                ordered_pids
            )
            _low = [dict(r) for r in cursor.fetchall()]
            if _low:
                _stock_alert(_low)
    except Exception as _e:
        current_app.logger.error(f"Low-stock check error (api): {_e}")

    # Clear cart
    cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (session['user_id'],))

    db.commit()
    
    return jsonify({
        'success': True,
        'message': 'Order placed successfully!',
        'order_id': order_id,
        'order_number': order_number,
        'total': total
    })


# ==================== CONTACT API ====================

@api_bp.route('/contact', methods=['POST'])
@limiter.limit("10 per hour")
def api_contact():
    """Submit contact form"""
    data = request.get_json(silent=True) or {}

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    message = data.get('message', '').strip()

    if not name or not email or not message:
        return jsonify({'success': False, 'error': 'Name, email, and message are required'}), 400

    db = get_db()
    cursor = db.cursor()
    # Use the canonical contact_messages table (no DDL on every request)
    cursor.execute("""
        INSERT INTO contact_messages (name, email, phone, message)
        VALUES (%s, %s, %s, %s)
    """, (name, email, phone, message))
    db.commit()

    return jsonify({
        'success': True,
        'message': 'Message sent successfully! We will contact you soon.'
    })


# ==================== BRANCHES API ====================

@api_bp.route('/branches')
def api_get_branches():
    """Get all branches"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT * FROM branches 
        WHERE is_active = 1 
        ORDER BY sort_order ASC
    """)
    
    branches = cursor.fetchall()
    
    branch_list = []
    for b in branches:
        branch_list.append({
            'id': b['id'],
            'name': b['name'],
            'name_am': b['name_am'],
            'name_ar': b['name_ar'],
            'address': b['address'],
            'address_am': b['address_am'],
            'address_ar': b['address_ar'],
            'phone': b['phone'],
            'email': b['email'],
            'latitude': b['latitude'],
            'longitude': b['longitude'],
            'working_hours': b['working_hours'],
            'image': b['image'],
            'maps_url': f"https://www.google.com/maps/dir/%sapi=1&destination={b['latitude']},{b['longitude']}"
        })
    
    return jsonify({
        'success': True,
        'branches': branch_list,
        'count': len(branch_list)
    })


# ==================== SETTINGS API ====================

@api_bp.route('/settings')
def api_get_settings():
    """Get public settings"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT key, value FROM settings")
    
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    
    return jsonify({
        'success': True,
        'settings': {
            'site_name': settings.get('site_name', 'SEMIRA FASHION'),
            'site_phone': settings.get('site_phone', '+251987957957'),
            'whatsapp_number': settings.get('whatsapp_number', '251987957957'),
            'free_shipping_threshold': float(settings.get('free_shipping_threshold', 5000)),
            'shipping_cost': float(settings.get('shipping_cost', 200)),
            'currency': settings.get('currency', 'ETB')
        }
    })


# ==================== CATEGORIES API ====================

@api_bp.route('/categories')
def api_categories():
    """Get all active categories with product counts."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT c.*, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON p.category_id = c.id AND p.is_active = 1
            WHERE c.is_active = 1
            GROUP BY c.id
            ORDER BY c.sort_order ASC
        """)
        categories = cursor.fetchall()
        return jsonify({
            'success': True,
            'categories': [dict(c) for c in categories] if categories else []
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== WISHLIST API ====================

@api_bp.route('/wishlist/ids', methods=['GET'])
def api_wishlist_ids():
    if not session.get('user_id'):
        return jsonify({'ids': []})
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT product_id FROM wishlist WHERE user_id = %s", (session['user_id'],))
        rows = cursor.fetchall()
        return jsonify({'ids': [str(r['product_id']) for r in rows]})
    except Exception:
        return jsonify({'ids': []})


@api_bp.route('/wishlist/add', methods=['POST'])
def api_wishlist_add():
    """Add product to wishlist."""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Please login first'}), 401
    try:
        data = request.get_json(silent=True) or {}
        product_id = data.get('product_id')
        if not product_id:
            return jsonify({'success': False, 'error': 'Product ID required'}), 400

        db = get_db()
        cursor = db.cursor()
        # Fetch current price so we can track price drops later
        cursor.execute("SELECT price FROM products WHERE id = %s AND is_active = 1", (product_id,))
        prod = cursor.fetchone()
        if not prod:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        cursor.execute("""
            INSERT INTO wishlist (user_id, product_id, price_at_add)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, product_id) DO NOTHING
        """, (session['user_id'], product_id, prod['price']))
        db.commit()
        return jsonify({'success': True, 'message': 'Added to wishlist'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/wishlist/remove', methods=['POST'])
def api_wishlist_remove():
    """Remove product from wishlist."""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Please login first'}), 401
    try:
        data = request.get_json(silent=True) or {}
        product_id = data.get('product_id')
        if not product_id:
            return jsonify({'success': False, 'error': 'Product ID required'}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM wishlist WHERE user_id = %s AND product_id = %s",
                       (session['user_id'], product_id))
        db.commit()
        return jsonify({'success': True, 'message': 'Removed from wishlist'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== COUPON API ====================

@api_bp.route('/apply-coupon', methods=['POST'])
def api_apply_coupon():
    """Apply discount coupon to cart."""
    try:
        data = request.get_json(silent=True) or {}
        code = data.get('code', '').strip().upper()
        if not code:
            return jsonify({'success': False, 'error': 'Coupon code required'}), 400

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT * FROM coupons
            WHERE code = %s AND is_active = 1
            AND (valid_from IS NULL OR valid_from <= CURRENT_TIMESTAMP)
            AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
            AND (usage_limit IS NULL OR used_count < usage_limit)
        """, (code,))
        coupon = cursor.fetchone()

        if not coupon:
            return jsonify({'success': False, 'error': 'Invalid or expired coupon code'}), 400

        # Get cart subtotal
        subtotal = 0
        if session.get('user_id'):
            cursor.execute("""
                SELECT SUM(p.price * ci.quantity) as total
                FROM cart_items ci JOIN products p ON ci.product_id = p.id
                WHERE ci.user_id = %s
            """, (session['user_id'],))
            result = cursor.fetchone()
            subtotal = result['total'] or 0 if result else 0

        if subtotal < (coupon['min_order'] or 0):
            return jsonify({'success': False,
                            'error': f"Minimum order of {coupon['min_order']} ETB required"}), 400

        if coupon['discount_type'] == 'percentage':
            discount = subtotal * (coupon['discount_value'] / 100)
            if coupon['max_discount']:
                discount = min(discount, coupon['max_discount'])
        else:
            discount = coupon['discount_value']

        session['applied_coupon'] = {
            'code': code,
            'discount': discount,
            'coupon_id': coupon['id'],
            # Keep raw fields so checkout can recalculate if needed
            'discount_type': coupon['discount_type'],
            'discount_value': float(coupon['discount_value']),
        }
        session.modified = True

        return jsonify({
            'success': True,
            'message': f'Coupon applied! You saved {discount:.2f} ETB',
            'discount': discount
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== REVIEWS API ====================

@api_bp.route('/product/<int:product_id>/reviews', methods=['GET', 'POST'])
def product_reviews(product_id):
    """Get or add product reviews."""
    if request.method == 'GET':
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT r.id, r.rating, r.comment, r.is_approved,
                       r.created_at, u.full_name as user_name,
                       CASE WHEN EXISTS(
                           SELECT 1 FROM order_items oi
                           JOIN orders o ON oi.order_id = o.id
                           WHERE oi.product_id = r.product_id
                             AND o.user_id = r.user_id
                             AND o.status = 'delivered'
                       ) THEN 1 ELSE 0 END as verified_purchase
                FROM reviews r JOIN users u ON r.user_id = u.id
                WHERE r.product_id = %s AND r.is_approved = 1
                ORDER BY r.created_at DESC LIMIT 30
            """, (product_id,))
            rows = cursor.fetchall()
            reviews_list = []
            for row in (rows or []):
                r = dict(row)
                if r.get('created_at') and not isinstance(r['created_at'], str):
                    r['created_at'] = r['created_at'].strftime('%b %d, %Y')
                reviews_list.append(r)

            avg_rating = (sum(r['rating'] for r in reviews_list) / len(reviews_list)
                          if reviews_list else 0)

            # Rating distribution
            dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for r in reviews_list:
                dist[int(r['rating'])] += 1

            # Current user's review status
            user_review = None
            has_purchased = False
            if session.get('user_id'):
                cursor.execute("SELECT rating, comment FROM reviews WHERE product_id=%s AND user_id=%s",
                               (product_id, session['user_id']))
                ur = cursor.fetchone()
                if ur:
                    user_review = dict(ur)
                # Check purchase
                cursor.execute("""
                    SELECT 1 FROM order_items oi
                    JOIN orders o ON oi.order_id = o.id
                    WHERE oi.product_id = %s AND o.user_id = %s AND o.status = 'delivered'
                    LIMIT 1
                """, (product_id, session['user_id']))
                has_purchased = cursor.fetchone() is not None

            return jsonify({
                'success': True,
                'reviews': reviews_list,
                'average_rating': round(avg_rating, 1),
                'total_reviews': len(reviews_list),
                'distribution': dist,
                'user_review': user_review,
                'has_purchased': has_purchased,
                'is_logged_in': bool(session.get('user_id'))
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # POST - add review
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Please login to leave a review'}), 401
    try:
        data = request.get_json(silent=True) or {}
        rating = int(data.get('rating', 0))
        comment = data.get('comment', '').strip()

        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'error': 'Rating must be between 1 and 5'}), 400
        if not comment:
            return jsonify({'success': False, 'error': 'Please write a review'}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM reviews WHERE product_id = %s AND user_id = %s",
                       (product_id, session['user_id']))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'You have already reviewed this product'}), 400

        cursor.execute("""
            INSERT INTO reviews (product_id, user_id, rating, comment, is_approved)
            VALUES (%s, %s, %s, %s, 0)
        """, (product_id, session['user_id'], rating, comment))
        db.commit()

        # Notify admin of new review
        try:
            from services.notification_service import notify_admin
            notify_admin(
                title='New Product Review',
                body=f'A customer left a {rating}⭐ review — awaiting approval.',
                type='info',
                link='/admin/reviews'
            )
        except Exception:
            pass

        return jsonify({'success': True, 'message': 'Review submitted! Awaiting approval.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== NEWSLETTER API ====================

@api_bp.route('/subscribe-newsletter', methods=['POST'])
@limiter.limit("5 per hour")
def subscribe_newsletter():
    """Subscribe to newsletter."""
    try:
        data = request.get_json(silent=True) or {}
        email = data.get('email', '').strip().lower()
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        if not re.match(r'^[^\s@]+@([^\s@.,]+\.)+[^\s@.,]{2,}$', email):
            return jsonify({'success': False, 'error': 'Invalid email address'}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO newsletter (email) VALUES (%s)
            ON CONFLICT (email) DO NOTHING
        """, (email,))
        db.commit()
        return jsonify({'success': True, 'message': 'Successfully subscribed to newsletter!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== TRANSLATION API ====================

@api_bp.route('/translate', methods=['POST'])
def api_translate():
    """Translate text to target language."""
    try:
        from utils.translation_cache import translate_text
        data = request.get_json(silent=True) or {}
        text = data.get('text', '').strip()
        target_lang = data.get('target_lang', 'en')
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        translated = translate_text(text, target_lang)
        return jsonify({'status': 'success', 'original': text,
                        'translated': translated, 'language': target_lang})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/translate-batch', methods=['POST'])
def api_translate_batch():
    """Translate multiple texts at once."""
    try:
        from utils.translation_cache import batch_translate
        data = request.get_json(silent=True) or {}
        texts = data.get('texts', [])
        target_lang = data.get('target_lang', 'en')
        if not texts or not isinstance(texts, list):
            return jsonify({'error': 'Texts array is required'}), 400
        translations = batch_translate(texts, target_lang)
        return jsonify({'status': 'success', 'translations': translations,
                        'language': target_lang, 'count': len(translations)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== PLATFORM API ====================

@api_bp.route('/platform')
def api_platform():
    """Get current platform information."""
    from middleware.platform import get_platform, is_android_app
    from flask import request as _req
    return jsonify({
        'success': True,
        'platform': get_platform(),
        'is_android_app': is_android_app(),
        'user_agent': _req.headers.get('User-Agent', '')
    })


# ==================== SUBMIT ORDER API ====================

@api_bp.route('/submit-order', methods=['POST'])
@limiter.limit("10 per minute; 30 per hour")
def api_submit_order():
    """Submit order via AJAX (quick-checkout modal) — supports guests and logged-in users."""
    user_id = session.get('user_id')
    try:
        data = request.get_json(silent=True) or {}
        customer_name    = (data.get('customer_name') or '').strip()
        customer_phone   = (data.get('customer_phone') or '').strip()
        shipping_address = (data.get('customer_address') or '').strip()
        customer_email   = (data.get('customer_email') or '').strip() or None
        notes            = (data.get('order_notes') or '').strip()

        if not customer_name or not customer_phone:
            return jsonify({'success': False, 'error': 'Name and phone number are required'}), 400
        if not shipping_address:
            return jsonify({'success': False, 'error': 'Delivery address is required'}), 400

        db = get_db()
        cursor = db.cursor()

        cart_items = []
        if user_id:
            cursor.execute("""
                SELECT ci.product_id, ci.quantity, p.price, p.name, p.name_am
                FROM cart_items ci JOIN products p ON ci.product_id = p.id
                WHERE ci.user_id = %s
            """, (user_id,))
            cart_items = cursor.fetchall()
        else:
            # Guest: load from session cart
            session_cart = session.get('cart', {})
            if session_cart:
                product_ids = [int(pid) for pid in session_cart.keys()]
                placeholders = ','.join(['%s'] * len(product_ids))
                cursor.execute(
                    f"SELECT id, name, name_am, price FROM products WHERE id IN ({placeholders}) AND is_active = TRUE",
                    product_ids
                )
                products_map = {p['id']: p for p in cursor.fetchall()}
                for pid_str, qty in session_cart.items():
                    p = products_map.get(int(pid_str))
                    if p:
                        cart_items.append({
                            'product_id': p['id'], 'quantity': qty,
                            'price': p['price'], 'name': p['name'],
                            'name_am': p['name_am'] or p['name'],
                        })

        if not cart_items:
            return jsonify({'success': False, 'error': 'Cart is empty'}), 400

        # Discount applies only to authenticated (session) users — not UA-based
        is_logged_in = bool(user_id)

        subtotal = 0
        items_list = []
        for item in cart_items:
            price = item['price'] or 0
            qty   = item['quantity'] or 1
            subtotal += price * qty
            items_list.append({
                'product_id': item['product_id'], 'quantity': qty,
                'price': round(price * (1 - USER_DISCOUNT_RATE), 2) if is_logged_in else price,
                'name': item['name'],
                'name_am': item['name_am'] or item['name'],
            })

        from routes.shared import calc_cart_totals as _cct
        _totals = _cct(subtotal, is_logged_in=is_logged_in)
        discount = _totals['discount']
        subtotal_after_discount = _totals['subtotal_after_discount']
        shipping_cost = _totals['shipping_cost']
        total = _totals['total']

        # Apply coupon if one is active in session (re-validate against current cart)
        coupon_info = session.pop('applied_coupon', None)
        if coupon_info:
            _coupon_id  = coupon_info.get('coupon_id')
            _disc_type  = coupon_info.get('discount_type')
            _disc_value = float(coupon_info.get('discount_value', 0))
            if _coupon_id and _disc_type:
                cursor.execute("""
                    SELECT min_order, max_discount, usage_limit, used_count, is_active
                    FROM coupons WHERE id = %s
                    AND (valid_to IS NULL OR valid_to >= NOW())
                """, (_coupon_id,))
                _fresh = cursor.fetchone()
                if (_fresh and _fresh['is_active'] and
                        (_fresh['usage_limit'] is None or _fresh['used_count'] < _fresh['usage_limit'])):
                    _min_order = float(_fresh['min_order'] or 0)
                    if subtotal_after_discount >= _min_order:
                        if _disc_type == 'percentage':
                            _extra = subtotal_after_discount * _disc_value / 100
                            if _fresh['max_discount']:
                                _extra = min(_extra, float(_fresh['max_discount']))
                        else:
                            _extra = min(_disc_value, subtotal_after_discount)
                        _extra = round(_extra, 2)
                        discount = round(discount + _extra, 2)
                        total = round(max(0, total - _extra), 2)

        import random, string
        from datetime import datetime as _dt
        order_number = f"{_dt.now().strftime('%Y%m%d')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

        cursor.execute("""
            INSERT INTO orders (
                order_number, user_id, customer_name, customer_email, status, payment_status,
                subtotal, discount, shipping_fee, total,
                shipping_address, shipping_phone, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (order_number, user_id, customer_name, customer_email, 'pending', 'pending',
              subtotal, discount, shipping_cost, total,
              shipping_address, customer_phone, notes))

        row = cursor.fetchone()
        order_id = row[0] if row else None

        for item in items_list:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['product_id'], item['quantity'], item['price']))
            # Atomic decrement — prevents race condition / negative stock
            cursor.execute("""
                UPDATE products SET stock_quantity = stock_quantity - %s,
                    sales_count = COALESCE(sales_count, 0) + %s
                WHERE id = %s AND stock_quantity >= %s
            """, (item['quantity'], item['quantity'], item['product_id'], item['quantity']))
            if cursor.rowcount == 0:
                db.rollback()
                return jsonify({'success': False,
                                'error': f"ይቅርታ! \"{item.get('name', 'ምርት')}\" ላይ በቂ ዕቃ አልተገኘም።"}), 400

        if user_id:
            cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))
        else:
            session.pop('cart', None)
        db.commit()

        # WhatsApp owner notification (background thread)
        try:
            from services.whatsapp_service import send_owner_order_notification
            wa_items = [{'name': i.get('name', ''), 'name_am': i.get('name_am', ''),
                         'quantity': i.get('quantity', 1), 'price': i.get('price', 0)} for i in items_list]
            send_owner_order_notification(
                order_number=order_number,
                customer_name=customer_name,
                customer_phone=customer_phone,
                items=wa_items,
                total=total,
                notes=notes
            )
        except Exception:
            pass

        return jsonify({
            'success': True,
            'message': 'Order placed successfully!',
            'order_id': order_id,
            'order_number': order_number,
            'total': total,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/profile', methods=['GET'])
def api_get_user_profile():
    """Return current logged-in user profile data as JSON."""
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, full_name, email, phone, city, address FROM users WHERE id = %s",
            (session['user_id'],)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        uid = session['user_id']
        cursor.execute("SELECT COUNT(*) as cnt FROM orders WHERE user_id = %s", (uid,))
        total_row = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) as cnt FROM orders WHERE user_id = %s AND status = 'delivered'", (uid,))
        delivered_row = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) as cnt FROM orders WHERE user_id = %s AND status NOT IN ('delivered','cancelled')", (uid,))
        pending_row = cursor.fetchone()

        return jsonify({
            'success': True,
            'user': {
                'full_name': row['full_name'] or '',
                'email':     row['email'] or '',
                'phone':     row['phone'] or '',
                'city':      row['city'] or '',
                'address':   row['address'] or '',
            },
            'order_stats': {
                'total':     total_row['cnt'] if total_row else 0,
                'delivered': delivered_row['cnt'] if delivered_row else 0,
                'pending':   pending_row['cnt'] if pending_row else 0,
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ORDER TRACKING API ====================

@api_bp.route('/track-order')
def api_track_order():
    """AJAX order tracking by order number."""
    order_number = request.args.get('order_number', '').strip()
    if not order_number:
        return jsonify({'success': False, 'error': 'Order number is required'}), 400
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT o.id, o.order_number, o.status, o.total,
                   o.payment_method, o.payment_status,
                   o.shipping_city, o.shipping_address,
                   o.tracking_number, o.created_at
            FROM orders o
            WHERE o.order_number = %s
        """, (order_number,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Order not found'}), 404

        order = dict(row)
        if order.get('created_at') and not isinstance(order['created_at'], str):
            order['created_at'] = order['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        elif order.get('created_at') is None:
            order['created_at'] = ''

        return jsonify({'success': True, 'order': order})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== NOTIFICATION API ====================

@api_bp.route('/notifications')
def api_get_notifications():
    """Return current user's notifications."""
    if not session.get('user_id'):
        return jsonify({'success': False, 'notifications': [], 'unread': 0})
    from services.notification_service import get_user_notifications, get_user_unread_count
    notifs = get_user_notifications(session['user_id'], limit=50)
    unread = get_user_unread_count(session['user_id'])
    return jsonify({'success': True, 'notifications': notifs, 'unread': unread})


@api_bp.route('/notifications/count')
def api_notification_count():
    """Return unread notification count for current user."""
    if not session.get('user_id'):
        return jsonify({'count': 0})
    from services.notification_service import get_user_unread_count
    return jsonify({'count': get_user_unread_count(session['user_id'])})


@api_bp.route('/notifications/mark-read', methods=['POST'])
def api_mark_notifications_read():
    """Mark one or all notifications as read."""
    if not session.get('user_id'):
        return jsonify({'success': False}), 401
    from services.notification_service import mark_user_notifications_read
    data = request.get_json(silent=True) or {}
    notif_id = data.get('id')
    mark_user_notifications_read(session['user_id'], notif_id)
    return jsonify({'success': True})


@api_bp.route('/admin/alerts')
def api_admin_alerts():
    """Return admin alerts (admin only)."""
    if not is_admin():
        return jsonify({'success': False}), 403
    from services.notification_service import get_admin_alerts, get_admin_unread_count
    alerts = get_admin_alerts(limit=60)
    unread = get_admin_unread_count()
    return jsonify({'success': True, 'notifications': alerts, 'unread_count': unread})


@api_bp.route('/admin/alerts/count')
def api_admin_alerts_count():
    """Return unread admin alert count."""
    if not is_admin():
        return jsonify({'count': 0})
    from services.notification_service import get_admin_unread_count
    return jsonify({'count': get_admin_unread_count()})


@api_bp.route('/admin/alerts/mark-read', methods=['POST'])
def api_admin_mark_alerts_read():
    if not is_admin():
        return jsonify({'success': False}), 403
    from services.notification_service import mark_admin_alerts_read
    data = request.get_json(silent=True) or {}
    mark_admin_alerts_read(data.get('id'))
    return jsonify({'success': True})
