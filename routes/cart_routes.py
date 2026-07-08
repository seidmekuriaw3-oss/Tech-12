"""
Cart Routes for SEMIRA FASHION

This module contains all cart-related routes including:
- View cart
- Add to cart
- Remove from cart
- Update quantities
- Checkout process
- Apply discounts
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from middleware.auth import user_login_required
from database.db import get_db
from routes.shared import calc_cart_totals, FREE_SHIPPING_THRESHOLD, SHIPPING_COST, USER_DISCOUNT_RATE
import json
from services.notification_service import notify_user, notify_admin
from services.whatsapp_service import send_owner_order_notification, send_low_stock_alert

cart_bp = Blueprint('cart', __name__)


# ==================== CART VIEW ====================

@cart_bp.route('/')
def view_cart():
    """View shopping cart page"""
    cart_items = []
    subtotal = 0
    
    if session.get('user_id'):
        # Get cart from database
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT ci.*, p.name, p.name_am, p.name_ar, p.price, p.compare_price, p.thumbnail, p.stock_quantity
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = %s AND p.is_active = 1
        """, (session['user_id'],))
        
        rows = cursor.fetchall()
        for row in rows:
            price = float(row['price'])
            discounted_price = round(price * (1 - USER_DISCOUNT_RATE), 2)
            # Subtotal uses ORIGINAL price — calc_cart_totals applies the 10% once
            subtotal += price * row['quantity']

            cart_items.append({
                'id': row['id'],
                'product_id': row['product_id'],
                'name': row['name'],
                'name_am': row['name_am'],
                'name_ar': row['name_ar'],
                'price': price,
                'discounted_price': discounted_price,
                'quantity': row['quantity'],
                'thumbnail': row['thumbnail'],
                'stock_quantity': row['stock_quantity'],
                'subtotal': round(price * row['quantity'], 2)  # Show original price in cart
            })
    else:
        # Get cart from session
        cart = session.get('cart', {})
        if cart:
            db = get_db()
            cursor = db.cursor()
            placeholders = ','.join(['%s'] * len(cart))
            cursor.execute(f"""
                SELECT id, name, name_am, name_ar, price, compare_price, thumbnail, stock_quantity
                FROM products WHERE id IN ({placeholders}) AND is_active = 1
            """, list(cart.keys()))
            
            products = cursor.fetchall()
            for p in products:
                quantity = cart.get(str(p['id']), 0)
                if quantity > 0:
                    price = float(p['price'])
                    item_subtotal = price * quantity
                    subtotal += item_subtotal
                    cart_items.append({
                        'product_id': p['id'],
                        'name': p['name'],
                        'name_am': p['name_am'],
                        'name_ar': p['name_ar'],
                        'price': price,
                        'discounted_price': price,
                        'quantity': quantity,
                        'thumbnail': p['thumbnail'],
                        'stock_quantity': p['stock_quantity'],
                        'subtotal': round(item_subtotal, 2)
                    })
    
    totals = calc_cart_totals(subtotal, is_logged_in=bool(session.get('user_id')))

    # Get site settings
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    whatsapp_number = settings.get('whatsapp_number', '251987957957')

    return render_template('customer/cart.html',
                         cart_items=cart_items,
                         **totals,
                         whatsapp_number=whatsapp_number,
                         is_logged_in=bool(session.get('user_id')))


# ==================== ADD TO CART ====================

@cart_bp.route('/go/add/<int:product_id>', methods=['GET'])
def go_add_to_cart(product_id):
    """GET-friendly fallback: add to cart then redirect to cart page"""
    quantity = int(request.args.get('qty', 1))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, stock_quantity FROM products WHERE id = %s AND is_active = 1", (product_id,))
    product = cursor.fetchone()
    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('customer.index'))
    if session.get('user_id'):
        cursor.execute("SELECT id, quantity FROM cart_items WHERE user_id = %s AND product_id = %s",
                       (session['user_id'], product_id))
        existing = cursor.fetchone()
        if existing:
            new_qty = existing['quantity'] + quantity
            if new_qty > product['stock_quantity']:
                flash(f'Sorry, only {product["stock_quantity"]} items available in stock!', 'warning')
                return redirect(url_for('cart.view_cart'))
            cursor.execute("UPDATE cart_items SET quantity = %s WHERE id = %s",
                           (new_qty, existing['id']))
        else:
            if quantity > product['stock_quantity']:
                flash(f'Sorry, only {product["stock_quantity"]} items available in stock!', 'warning')
                return redirect(url_for('cart.view_cart'))
            cursor.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                           (session['user_id'], product_id, quantity))
        db.commit()
    else:
        cart = session.get('cart', {})
        cart_key = str(product_id)
        new_qty = cart.get(cart_key, 0) + quantity
        if new_qty > product['stock_quantity']:
            flash(f'Sorry, only {product["stock_quantity"]} items available in stock!', 'warning')
            return redirect(url_for('cart.view_cart'))
        cart[cart_key] = new_qty
        session['cart'] = cart
        session.modified = True
    flash('Product added to cart!', 'success')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    quantity = int(request.form.get('quantity', 1))
    
    # Check if product exists and has stock
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, stock_quantity FROM products WHERE id = %s AND is_active = 1", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        flash('Product not found!', 'danger')
        return redirect(request.referrer or url_for('customer.index'))
    
    if product['stock_quantity'] < quantity:
        flash(f'Sorry, only {product["stock_quantity"]} items available in stock!', 'warning')
        return redirect(request.referrer or url_for('customer.index'))
    
    if session.get('user_id'):
        # Add to database cart
        cursor.execute("""
            SELECT id, quantity FROM cart_items 
            WHERE user_id = %s AND product_id = %s
        """, (session['user_id'], product_id))
        
        existing = cursor.fetchone()
        
        if existing:
            new_quantity = existing['quantity'] + quantity
            if product['stock_quantity'] >= new_quantity:
                cursor.execute("""
                    UPDATE cart_items SET quantity = %s WHERE id = %s
                """, (new_quantity, existing['id']))
                flash('Cart updated successfully!', 'success')
            else:
                flash(f'Sorry, only {product["stock_quantity"]} items available in stock!', 'warning')
        else:
            cursor.execute("""
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (session['user_id'], product_id, quantity))
            flash('Product added to cart!', 'success')
        
        db.commit()
    else:
        # Add to session cart
        cart = session.get('cart', {})
        cart_key = str(product_id)
        
        current_quantity = cart.get(cart_key, 0)
        new_quantity = current_quantity + quantity
        
        if product['stock_quantity'] >= new_quantity:
            cart[cart_key] = new_quantity
            session['cart'] = cart
            session.modified = True
            flash('Product added to cart!', 'success')
        else:
            flash(f'Sorry, only {product["stock_quantity"]} items available in stock!', 'warning')
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'Product added to cart',
            'cart_count': get_cart_count()
        })
    
    return redirect(url_for('cart.view_cart'))


# ====================== REMOVE FROM CART ====================

@cart_bp.route('/remove/<int:product_id>')
def remove_from_cart(product_id):
    """Remove product from cart"""
    if session.get('user_id'):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            DELETE FROM cart_items 
            WHERE user_id = %s AND product_id = %s
        """, (session['user_id'], product_id))
        db.commit()
    else:
        cart = session.get('cart', {})
        cart_key = str(product_id)
        if cart_key in cart:
            del cart[cart_key]
        session['cart'] = cart
        session.modified = True
    
    flash('Product removed from cart!', 'success')
    return redirect(url_for('cart.view_cart'))


# ==================== UPDATE CART ====================

@cart_bp.route('/update', methods=['POST'])
def update_cart():
    """Update cart quantities"""
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 0))
    
    if not product_id:
        flash('Invalid request!', 'danger')
        return redirect(url_for('cart.view_cart'))
    
    # Check stock
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT stock_quantity FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    if product and quantity > product['stock_quantity']:
        flash(f'Sorry, only {product["stock_quantity"]} items available in stock!', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    if quantity <= 0:
        return remove_from_cart(int(product_id))
    
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
    
    flash('Cart updated!', 'success')
    return redirect(url_for('cart.view_cart'))


# ==================== CLEAR CART ====================

@cart_bp.route('/clear', methods=['GET', 'POST'])
def clear_cart():
    """Clear entire cart"""
    if session.get('user_id'):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (session['user_id'],))
        db.commit()
    else:
        session.pop('cart', None)
    
    flash('Cart cleared!', 'success')
    return redirect(url_for('cart.view_cart'))


# ==================== CHECKOUT ====================

@cart_bp.route('/checkout')
def checkout():
    """Checkout page — supports both logged-in users and guests"""
    user_id = session.get('user_id')
    db = get_db()
    cursor = db.cursor()

    cart_items = []
    subtotal = 0

    if user_id:
        # Logged-in: fetch from DB cart_items
        cursor.execute("""
            SELECT ci.*, p.name, p.name_am, p.name_ar, p.price, p.thumbnail
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = %s AND p.is_active = 1
        """, (user_id,))
        raw_items = cursor.fetchall()

        if not raw_items:
            flash('Your cart is empty!', 'warning')
            return redirect(url_for('customer.index'))

        for item in raw_items:
            orig_price = float(item['price'])
            discounted_price = round(orig_price * (1 - USER_DISCOUNT_RATE), 2)
            subtotal += orig_price * item['quantity']
            cart_items.append({
                'id': item['id'] if 'id' in item.keys() else None,
                'product_id': item['product_id'],
                'name': item['name'],
                'name_am': item['name_am'],
                'name_ar': item['name_ar'],
                'price': orig_price,
                'discounted_price': discounted_price,
                'quantity': item['quantity'],
                'thumbnail': item['thumbnail'],
                'subtotal': round(discounted_price * item['quantity'], 2),
            })
    else:
        # Guest: fetch from session cart
        session_cart = session.get('cart', {})
        if not session_cart:
            flash('Your cart is empty!', 'warning')
            return redirect(url_for('customer.index'))

        product_ids = [int(pid) for pid in session_cart.keys()]
        placeholders = ','.join(['%s'] * len(product_ids))
        cursor.execute(f"SELECT id, name, name_am, name_ar, price, thumbnail FROM products WHERE id IN ({placeholders}) AND is_active = 1", product_ids)
        products_map = {str(p['id']): p for p in cursor.fetchall()}

        for pid_str, qty in session_cart.items():
            p = products_map.get(pid_str)
            if not p:
                continue
            orig_price = float(p['price'])
            subtotal += orig_price * qty
            cart_items.append({
                'id': None,
                'product_id': p['id'],
                'name': p['name'],
                'name_am': p['name_am'],
                'name_ar': p['name_ar'],
                'price': orig_price,
                'discounted_price': orig_price,
                'quantity': qty,
                'thumbnail': p['thumbnail'],
                'subtotal': round(orig_price * qty, 2),
            })

        if not cart_items:
            flash('Your cart is empty!', 'warning')
            return redirect(url_for('customer.index'))

    is_logged_in = bool(user_id)
    totals = calc_cart_totals(subtotal, is_logged_in=is_logged_in)

    user = None
    if user_id:
        cursor.execute("SELECT full_name, email, phone, address, city FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

    return render_template('customer/checkout.html',
                           cart_items=cart_items,
                           **totals,
                           user=user,
                           is_guest=not is_logged_in)


# ==================== PLACE ORDER ====================

@cart_bp.route('/place-order', methods=['POST'])
def place_order():
    """Place order from cart — supports both logged-in users and guests"""
    user_id = session.get('user_id')
    db = get_db()
    cursor = db.cursor()

    # Get form data
    shipping_address = request.form.get('shipping_address', '').strip()
    shipping_city    = request.form.get('shipping_city', '').strip()
    shipping_phone   = request.form.get('shipping_phone', '').strip()
    notes            = request.form.get('notes', '').strip()
    payment_method   = request.form.get('payment_method', 'cash').lower().strip()
    customer_name    = request.form.get('customer_name', '').strip()
    customer_email   = request.form.get('customer_email', '').strip() or None

    # Validate payment method (whitelist allowed methods)
    ALLOWED_PAYMENT_METHODS = ['cash', 'card', 'telebirr', 'bank']
    if payment_method not in ALLOWED_PAYMENT_METHODS:
        flash(f'Invalid payment method. Allowed: {", ".join(ALLOWED_PAYMENT_METHODS)}', 'danger')
        return redirect(url_for('cart.checkout'))

    # Validate required fields for all users
    if not shipping_address or len(shipping_address) < 5:
        flash('እባክዎ ትክክለኛ አድራሻዎን ያስገቡ። (ቢያንስ 5 ፊደሎች)', 'danger')
        return redirect(url_for('cart.checkout'))
    if not shipping_phone:
        flash('ስልክ ቁጥር ያስፈልጋል።', 'danger')
        return redirect(url_for('cart.checkout'))
    
    # Validate phone number format - Ethiopian numbers only
    import re
    phone_pattern = r'^(09|07|2519|2517)\d{8}$'
    phone_normalized = shipping_phone.replace(' ', '').replace('-', '')
    if not re.match(phone_pattern, phone_normalized):
        flash('ትክክለኛ የኢትዮጵያ ስልክ ቁጥር ያስገቡ (09xxxxxxxx, 07xxxxxxxx, 2519xxxxxxxx)', 'danger')
        return redirect(url_for('cart.checkout'))
    
    if not user_id and not customer_name:
        flash('ሙሉ ስም ያስፈልጋል።', 'danger')
        return redirect(url_for('cart.checkout'))
    
    # Validate customer name length
    if customer_name and (len(customer_name) < 2 or len(customer_name) > 100):
        flash('ስም 2 ወደ 100 ፊደሎች መሆን አለበት።', 'danger')
        return redirect(url_for('cart.checkout'))
    
    # Validate email if provided
    if customer_email:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, customer_email):
            flash('ትክክለኛ ኢሜይል ያስገቡ።', 'danger')
            return redirect(url_for('cart.checkout'))
    
    # Validate city if provided
    if shipping_city and len(shipping_city) > 50:
        flash('ከተማ 50 ፊደሎች ያነስ መሆን አለበት።', 'danger')
        return redirect(url_for('cart.checkout'))
    
    # Validate notes if provided
    if notes and len(notes) > 500:
        flash('ማስታወሻ 500 ፊደሎች ያነስ መሆን አለበት።', 'danger')
        return redirect(url_for('cart.checkout'))

    cart_items_raw = []

    if user_id:
        cursor.execute("""
            SELECT ci.product_id, ci.quantity, p.price, p.name, p.name_am, p.stock_quantity
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = %s AND p.is_active = 1
            FOR UPDATE OF p
        """, (user_id,))
        cart_items_raw = cursor.fetchall()
    else:
        session_cart = session.get('cart', {})
        if session_cart:
            product_ids = [int(pid) for pid in session_cart.keys()]
            placeholders = ','.join(['%s'] * len(product_ids))
            cursor.execute(
                f"SELECT id, name, name_am, price, stock_quantity FROM products WHERE id IN ({placeholders}) AND is_active = 1 FOR UPDATE",
                product_ids
            )
            products_map = {p['id']: p for p in cursor.fetchall()}
            for pid_str, qty in session_cart.items():
                p = products_map.get(int(pid_str))
                if p:
                    cart_items_raw.append({
                        'product_id': p['id'], 'quantity': qty,
                        'price': p['price'], 'name': p['name'],
                        'name_am': p['name_am'], 'stock_quantity': p['stock_quantity']
                    })

    if not cart_items_raw:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart.view_cart'))

    # Duplicate order prevention: check if identical order was just created
    # This prevents double-submit when user clicks button twice or reloads page
    try:
        if user_id:
            # For logged-in users, check for recent orders with same items
            cursor.execute("""
                SELECT id FROM orders 
                WHERE user_id = %s 
                AND created_at > NOW() - INTERVAL '30 seconds'
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
        else:
            # For guests, check for recent orders with same phone/address
            cursor.execute("""
                SELECT id FROM orders 
                WHERE user_id IS NULL
                AND shipping_phone = %s 
                AND shipping_address = %s
                AND created_at > NOW() - INTERVAL '30 seconds'
                ORDER BY created_at DESC LIMIT 1
            """, (shipping_phone, shipping_address))
        
        recent_order = cursor.fetchone()
        if recent_order:
            # Likely a double-submit - redirect to confirmation for existing order
            if user_id:
                flash('ይህ ትዕዛዝ ቀድሞ ተላልፏል።', 'warning')
            else:
                # For guests, generate token for the recent order
                cursor.execute("""
                    SELECT order_number FROM orders WHERE id = %s
                """, (recent_order['id'],))
                dup_order_info = cursor.fetchone()
                if dup_order_info:
                    import hmac, hashlib
                    dup_token = hmac.new(
                        current_app.config['SECRET_KEY'].encode(),
                        f"{recent_order['id']}-{dup_order_info['order_number']}-{shipping_phone}".encode(),
                        hashlib.sha256
                    ).hexdigest()
                    session['guest_order_token'] = dup_token
            return redirect(url_for('customer.order_confirmation', order_id=recent_order['id']))
    except Exception as e:
        current_app.logger.error(f"Duplicate order check failed: {e}")
    
# Stock check
    for item in cart_items_raw:
        qty = item['quantity'] if isinstance(item, dict) else item['quantity']
        stock = item['stock_quantity'] if isinstance(item, dict) else item['stock_quantity']
        name = item['name'] if isinstance(item, dict) else item['name']
        if qty > stock:
            flash(f'Sorry, {name} has only {stock} items in stock!', 'danger')
            return redirect(url_for('cart.view_cart'))

    # Calculate totals
    subtotal = sum(
        float(item['price']) * int(item['quantity'])
        for item in cart_items_raw
    )
    is_logged_in = bool(user_id)
    totals = calc_cart_totals(subtotal, is_logged_in=is_logged_in)
    subtotal_after_discount = totals['subtotal_after_discount']
    shipping_cost = totals['shipping_cost']
    total = totals['total']
    discount = totals['discount']

    # Read coupon from session and consume it ATOMICALLY before creating order
    coupon_id  = None
    extra_disc = 0.0
    coupon_info = session.get('applied_coupon')
    if coupon_info:
        coupon_id   = coupon_info.get('coupon_id')
        disc_type   = coupon_info.get('discount_type')
        disc_value  = float(coupon_info.get('discount_value', 0))
        extra_disc  = 0.0
        if coupon_id and disc_type:
            # Atomic coupon consumption: check AND increment in one query
            # This prevents race condition where two orders use the same limited coupon
            cursor.execute("""
                UPDATE coupons 
                SET used_count = used_count + 1
                WHERE id = %s 
                  AND is_active = 1
                  AND (valid_to IS NULL OR valid_to >= NOW())
                  AND (usage_limit IS NULL OR used_count < usage_limit)
                RETURNING min_order, max_discount
            """, (coupon_id,))
            coupon_result = cursor.fetchone()
            if coupon_result:
                # Coupon was successfully consumed (used_count incremented)
                min_order = float(coupon_result['min_order'] or 0)
                if subtotal_after_discount >= min_order:
                    if disc_type == 'percentage':
                        extra_disc = subtotal_after_discount * disc_value / 100
                        if coupon_result['max_discount']:
                            extra_disc = min(extra_disc, float(coupon_result['max_discount']))
                    else:
                        extra_disc = min(disc_value, subtotal_after_discount)
                    extra_disc = round(extra_disc, 2)
                else:
                    # Min order not met — rollback the used_count increment to avoid leaking
                    cursor.execute("UPDATE coupons SET used_count = used_count - 1 WHERE id = %s", (coupon_id,))
                    coupon_id = None
                    extra_disc = 0.0
                    current_app.logger.warning(f"Coupon min_order not met; rolled back used_count")
            else:
                # Coupon could not be consumed - already used or limit exceeded or expired
                coupon_id = None
                extra_disc = 0.0
                current_app.logger.warning(f"Coupon {coupon_id} could not be consumed - limit may have been reached")
        if extra_disc > 0:
            discount = round(discount + extra_disc, 2)
            total = round(max(0, total - extra_disc), 2)

    # Generate order number
    from datetime import datetime
    import random, string
    order_number = f"{datetime.now().strftime('%Y%m%d')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

    if not customer_name and user_id:
        customer_name = session.get('user_name', 'Customer')
    if not shipping_phone and user_id:
        shipping_phone = session.get('user_phone', '')

    cursor.execute("""
        INSERT INTO orders (
            order_number, user_id, customer_name, customer_email, status, payment_status, payment_method,
            subtotal, discount, shipping_fee, total,
            shipping_address, shipping_city, shipping_phone, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (
        order_number, user_id, customer_name, customer_email, 'pending', 'pending', payment_method,
        subtotal, discount, shipping_cost, total,
        shipping_address, shipping_city, shipping_phone, notes
    ))
    row = cursor.fetchone()
    order_id = row[0] if row else None
    if not order_id:
        db.rollback()
        flash('ትዕዛዙን ማስቀመጥ አልተሳካም። እባክዎ እንደገና ይሞክሩ።', 'danger')
        return redirect(url_for('cart.checkout'))

    # Record initial pending status in history
    try:
        cursor.execute(
            "INSERT INTO order_status_history (order_id, status, note) VALUES (%s, 'pending', 'ትዕዛዝ ደርሷል')",
            (order_id,)
        )
    except Exception as _he:
        current_app.logger.warning(f"Could not record order history: {_he}")

    # Create order items and update stock atomically
    for item in cart_items_raw:
        price = item['price'] if isinstance(item, dict) else item['price']
        qty   = item['quantity'] if isinstance(item, dict) else item['quantity']
        pid   = item['product_id'] if isinstance(item, dict) else item['product_id']
        name  = item['name'] if isinstance(item, dict) else item['name']
        discounted_price = round(float(price) * (1 - USER_DISCOUNT_RATE if is_logged_in else 1.0), 2)
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
            VALUES (%s, %s, %s, %s)
        """, (order_id, pid, qty, discounted_price))
        # Atomic decrement — prevents race condition when two orders compete for the last item
        cursor.execute("""
            UPDATE products SET
                stock_quantity = stock_quantity - %s,
                sales_count = sales_count + %s
            WHERE id = %s AND stock_quantity >= %s
        """, (qty, qty, pid, qty))
        if cursor.rowcount == 0:
            db.rollback()
            flash(f'ይቅርታ! "{name}" ላይ በቂ ዕቃ አልተገኘም። ካርትዎን ያረጋግጡ።', 'danger')
            return redirect(url_for('cart.view_cart'))

    # Low-stock check — query updated stock levels within this transaction
    try:
        ordered_pids = list({
            (item['product_id'] if isinstance(item, dict) else item['product_id'])
            for item in cart_items_raw
        })
        if ordered_pids:
            _ph = ','.join(['%s'] * len(ordered_pids))
            cursor.execute(
                f"""SELECT id, name_am, name, stock_quantity, low_stock_threshold
                    FROM products WHERE id IN ({_ph})
                    AND stock_quantity <= low_stock_threshold""",
                ordered_pids
            )
            _low = [dict(r) for r in cursor.fetchall()]
            if _low:
                send_low_stock_alert(_low)
    except Exception as _e:
        current_app.logger.error(f"Low-stock check error: {_e}")

    # Clear cart
    if user_id:
        cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))
    else:
        session.pop('cart', None)

    db.commit()

    # Coupon was successfully consumed — remove it from session only after commit
    session.pop('applied_coupon', None)

    flash(f'✅ Order placed successfully! Your order number is: {order_number}', 'success')

    if user_id:
        try:
            notify_user(
                user_id,
                '✅ Order Placed Successfully',
                f'Your order #{order_number} has been received. We will confirm it shortly.',
                type='order',
                link=f'/orders/{order_id}'
            )
            notify_admin(
                '🛒 New Order Received',
                f'Order #{order_number} was placed. Total: {total:.0f} ETB.',
                type='new_order',
                link=f'/admin/orders/{order_id}',
                ref_order_id=order_id,
                ref_user_id=user_id
            )
        except Exception:
            pass
    else:
        try:
            notify_admin(
                '🛒 New Guest Order',
                f'Guest order #{order_number} from {customer_name}. Total: {total:.0f} ETB.',
                type='new_order',
                link=f'/admin/orders/{order_id}',
                ref_order_id=order_id
            )
        except Exception:
            pass

    try:
        wa_items = [
            {'name': item['name'] if isinstance(item, dict) else item['name'],
             'name_am': item.get('name_am', '') if isinstance(item, dict) else item.get('name_am', ''),
             'quantity': item['quantity'] if isinstance(item, dict) else item['quantity'],
             'price': item['price'] if isinstance(item, dict) else item['price']}
            for item in cart_items_raw
        ]
        send_owner_order_notification(
            order_number=order_number,
            customer_name=customer_name,
            customer_phone=shipping_phone,
            items=wa_items,
            total=total,
            notes=notes
        )
    except Exception:
        pass

    # Generate secure token for guest order access
    if not user_id:
        import hmac
        import hashlib
        guest_token = hmac.new(
            current_app.config['SECRET_KEY'].encode(),
            f"{order_id}-{order_number}-{shipping_phone}".encode(),
            hashlib.sha256
        ).hexdigest()
        session['guest_order_token'] = guest_token
    
    session['last_order_id'] = order_id
    return redirect(url_for('customer.order_confirmation', order_id=order_id))


# ==================== HELPER FUNCTIONS ====================

def get_cart_count():
    """Get total number of items in cart"""
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
    
    return count


def get_cart_total():
    """Get cart total amount"""
    total = 0
    
    if session.get('user_id'):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT SUM(p.price * ci.quantity) as total
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = %s
        """, (session['user_id'],))
        result = cursor.fetchone()
        total = float(result['total'] or 0)
    else:
        cart = session.get('cart', {})
        if cart:
            db = get_db()
            cursor = db.cursor()
            placeholders = ','.join(['%s'] * len(cart))
            cursor.execute(f"SELECT id, price FROM products WHERE id IN ({placeholders})", list(cart.keys()))
            products = cursor.fetchall()
            for p in products:
                quantity = cart.get(str(p['id']), 0)
                total += float(p['price']) * quantity
    
    # Apply member discount for logged-in users
    if session.get('user_id'):
        total = float(total) * (1 - USER_DISCOUNT_RATE)
    
    return round(total, 2)


# ==================== CONTEXT PROCESSOR ====================

def add_cart_context():
    """
    Add cart information to all templates.
    This function should be called from app context processor.
    """
    return {
        'cart_count': get_cart_count(),
        'cart_total': get_cart_total()
    }