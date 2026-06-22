"""
Cart Routes for ኢትዮሳዳት ፈርኒቸር ወድ ሰሚራ

This module contains all cart-related routes including:
- View cart
- Add to cart
- Remove from cart
- Update quantities
- Checkout process
- Apply discounts
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from middleware.auth import user_login_required
from database.db import get_db
from routes.shared import calc_cart_totals, FREE_SHIPPING_THRESHOLD, SHIPPING_COST, USER_DISCOUNT_RATE
import json
from services.notification_service import notify_user, notify_admin
from services.whatsapp_service import send_owner_order_notification

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
            WHERE ci.user_id = %s
        """, (session['user_id'],))
        
        rows = cursor.fetchall()
        for row in rows:
            discounted_price = round(row['price'] * 0.9, 2)
            # Subtotal uses ORIGINAL price — calc_cart_totals applies the 10% once
            orig_subtotal = row['price'] * row['quantity']
            subtotal += orig_subtotal

            cart_items.append({
                'id': row['id'],
                'product_id': row['product_id'],
                'name': row['name'],
                'name_am': row['name_am'],
                'name_ar': row['name_ar'],
                'price': row['price'],
                'discounted_price': discounted_price,
                'quantity': row['quantity'],
                'thumbnail': row['thumbnail'],
                'stock_quantity': row['stock_quantity'],
                'subtotal': round(discounted_price * row['quantity'], 2)
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
                FROM products WHERE id IN ({placeholders})
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
                        'discounted_price': p['price'],
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
            cursor.execute("UPDATE cart_items SET quantity = %s WHERE id = %s",
                           (existing['quantity'] + quantity, existing['id']))
        else:
            cursor.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                           (session['user_id'], product_id, quantity))
        db.commit()
    else:
        cart = session.get('cart', {})
        cart_key = str(product_id)
        cart[cart_key] = cart.get(cart_key, 0) + quantity
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
        return remove_from_cart(product_id)
    
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
@user_login_required
def checkout():
    """Checkout page"""
    # Get cart items
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT ci.*, p.name, p.name_am, p.name_ar, p.price, p.thumbnail
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.user_id = %s
    """, (session['user_id'],))
    
    raw_items = cursor.fetchall()

    if not raw_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('customer.index'))

    # Build enriched cart items with discounted_price for template display
    cart_items = []
    subtotal = 0
    for item in raw_items:
        orig_price = item['price']
        discounted_price = round(orig_price * 0.9, 2)
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

    # calc_cart_totals applies the 10% discount exactly once on original subtotal
    totals = calc_cart_totals(subtotal, is_logged_in=True)

    # Get user info for pre-filling
    cursor.execute("SELECT full_name, email, phone, address, city FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()

    return render_template('customer/checkout.html',
                         cart_items=cart_items,
                         **totals,
                         user=user)


# ==================== PLACE ORDER ====================

@cart_bp.route('/place-order', methods=['POST'])
@user_login_required
def place_order():
    """Place order from cart"""
    db = get_db()
    cursor = db.cursor()
    
    # Get cart items
    cursor.execute("""
        SELECT ci.*, p.price, p.name, p.stock_quantity
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.user_id = %s
    """, (session['user_id'],))
    
    cart_items = cursor.fetchall()
    
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    # Check stock availability
    for item in cart_items:
        if item['quantity'] > item['stock_quantity']:
            flash(f'Sorry, {item["name"]} has only {item["stock_quantity"]} items in stock!', 'danger')
            return redirect(url_for('cart.view_cart'))
    
    # Calculate totals
    subtotal = 0
    for item in cart_items:
        subtotal += item['price'] * item['quantity']

    totals = calc_cart_totals(subtotal, is_logged_in=True)
    subtotal_after_discount = totals['subtotal_after_discount']
    shipping_cost = totals['shipping_cost']
    total = totals['total']
    discount = totals['discount']

    coupon_info = session.pop('applied_coupon', None)
    if coupon_info:
        if coupon_info.get('discount_type') == 'percentage':
            extra_disc = round(subtotal_after_discount * float(coupon_info['discount_value']) / 100, 2)
        else:
            extra_disc = min(float(coupon_info['discount_value']), subtotal_after_discount)
        discount = round(discount + extra_disc, 2)
        total = round(max(0, total - extra_disc), 2)

    # Generate order number
    from datetime import datetime
    import random
    import string
    order_number = f"{datetime.now().strftime('%Y%m%d')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
    
    # Get form data
    shipping_address = request.form.get('shipping_address', '')
    shipping_city = request.form.get('shipping_city', '')
    shipping_phone = request.form.get('shipping_phone', session.get('user_phone', ''))
    notes = request.form.get('notes', '')
    payment_method = request.form.get('payment_method', 'cash')
    
    # Create order
    cursor.execute("""
        INSERT INTO orders (
            order_number, user_id, status, payment_status, payment_method,
            subtotal, discount, shipping_fee, total,
            shipping_address, shipping_city, shipping_phone, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (
        order_number, session['user_id'], 'pending', 'pending', payment_method,
        subtotal, discount, shipping_cost, total,
        shipping_address, shipping_city, shipping_phone, notes
    ))
    row = cursor.fetchone()
    order_id = row[0] if row else None
    
    # Create order items and update stock
    for item in cart_items:
        discounted_price = item['price'] * 0.9
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
            VALUES (%s, %s, %s, %s)
        """, (order_id, item['product_id'], item['quantity'], discounted_price))
        
        # Update product stock
        cursor.execute("""
            UPDATE products SET 
                stock_quantity = stock_quantity - %s,
                sales_count = sales_count + %s
            WHERE id = %s
        """, (item['quantity'], item['quantity'], item['product_id']))
    
    # Clear cart
    cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (session['user_id'],))
    
    db.commit()
    
    flash(f'Order placed successfully! Your order number is: {order_number}', 'success')

    try:
        notify_user(
            session['user_id'],
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
            ref_user_id=session.get('user_id')
        )
    except Exception:
        pass

    # WhatsApp owner notification (background thread — never blocks order)
    try:
        customer_name = session.get('user_name', 'Customer')
        wa_items = [
            {'name': item['name'], 'name_am': item.get('name', ''),
             'quantity': item['quantity'], 'price': item['price']}
            for item in cart_items
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
        total = result['total'] or 0
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
                total += p['price'] * quantity
    
    # Apply 10% discount for logged in users
    if session.get('user_id'):
        total = total * 0.9
    
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