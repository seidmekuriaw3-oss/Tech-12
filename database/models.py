import json
from database.db import get_db


class Product:
    """Product model for database operations"""
    
    @staticmethod
    def get_all():
        """Get all products ordered by newest first"""
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM products WHERE is_active = 1 ORDER BY id DESC"
            ).fetchall()
        except Exception as e:
            print(f"Error getting all products: {e}")
            return []
    
    @staticmethod
    def get_all_admin():
        """Get all products including inactive for admin"""
        try:
            db = get_db()
            return db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        except Exception as e:
            print(f"Error getting all admin products: {e}")
            return []
    
    @staticmethod
    def get_by_id(pid):
        """Get a single product by ID"""
        try:
            db = get_db()
            return db.execute("SELECT * FROM products WHERE id = %s", (pid,)).fetchone()
        except Exception as e:
            print(f"Error getting product by ID {pid}: {e}")
            return None
    
    @staticmethod
    def get_by_category(category_id):
        """Get all products in a specific category"""
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM products WHERE category_id = %s AND is_active = 1 ORDER BY id DESC", 
                (category_id,)
            ).fetchall()
        except Exception as e:
            print(f"Error getting products by category {category_id}: {e}")
            return []
    
    @staticmethod
    def get_featured(limit=8):
        """Get featured products"""
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM products WHERE is_featured = 1 AND is_active = 1 ORDER BY id DESC LIMIT %s",
                (limit,)
            ).fetchall()
        except Exception as e:
            print(f"Error getting featured products: {e}")
            return []
    
    @staticmethod
    def get_new(limit=8):
        """Get new products"""
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM products WHERE is_new = 1 AND is_active = 1 ORDER BY id DESC LIMIT %s",
                (limit,)
            ).fetchall()
        except Exception as e:
            print(f"Error getting new products: {e}")
            return []
    
    @staticmethod
    def search(query):
        """Search products by name (Amharic, English, or Arabic)"""
        try:
            db = get_db()
            search = f'%{query}%'
            return db.execute(
                """SELECT * FROM products 
                   WHERE (name LIKE %s OR name_am LIKE %s OR name_ar LIKE %s) 
                   AND is_active = 1
                   ORDER BY id DESC""",
                (search, search, search)
            ).fetchall()
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    @staticmethod
    def create(data):
        """
        Create a new product
        
        Args:
            data (dict): Product data with keys:
                - name, name_am, name_ar, name_en (required)
                - price (required)
                - category_id (required)
                - description, description_am, description_ar, description_en
                - image, images, thumbnail, stock_quantity
                - is_featured, is_new, material, color, weight, dimensions
                - meta_title, meta_description
        """
        try:
            db = get_db()
            
            # Handle images as JSON string
            images_json = None
            if data.get('images'):
                if isinstance(data['images'], list):
                    images_json = json.dumps(data['images'])
                else:
                    images_json = data['images']
            
            cursor = db.execute(
                """INSERT INTO products (
                    name, name_am, name_ar, name_en,
                    description, description_am, description_ar, description_en,
                    price, compare_price, cost, sku, barcode,
                    stock_quantity, low_stock_threshold,
                    images, thumbnail,
                    is_active, is_featured, is_new,
                    weight, dimensions, material, color,
                    category_id, views, sales_count,
                    meta_title, meta_description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id""",
                (
                    data.get('name', data.get('name_en', '')),
                    data.get('name_am', ''),
                    data.get('name_ar', ''),
                    data.get('name_en', ''),
                    data.get('description', data.get('description_en', '')),
                    data.get('description_am', ''),
                    data.get('description_ar', ''),
                    data.get('description_en', ''),
                    data['price'],
                    data.get('compare_price', data.get('old_price')),
                    data.get('cost'),
                    data.get('sku'),
                    data.get('barcode'),
                    data.get('stock_quantity', data.get('stock', 0)),
                    data.get('low_stock_threshold', 5),
                    images_json,
                    data.get('thumbnail', data.get('image', '')),
                    1,  # is_active
                    data.get('is_featured', 0),
                    data.get('is_new', 0),
                    data.get('weight'),
                    data.get('dimensions'),
                    data.get('material'),
                    data.get('color'),
                    data['category_id'],
                    0,  # views
                    0,  # sales_count
                    data.get('meta_title', ''),
                    data.get('meta_description', '')
                )
            )
            row = cursor.fetchone()
            db.commit()
            return row['id'] if row else None
        except Exception as e:
            print(f"Error creating product: {e}")
            db.rollback()
            return None

    @staticmethod
    def update(pid, data):
        """
        Update an existing product
        
        Args:
            pid (int): Product ID
            data (dict): Updated product data
        """
        try:
            db = get_db()
            
            # Handle images as JSON string
            images_json = None
            if data.get('images'):
                if isinstance(data['images'], list):
                    images_json = json.dumps(data['images'])
                else:
                    images_json = data['images']
            
            db.execute(
                """UPDATE products SET 
                    name=%s, name_am=%s, name_ar=%s, name_en=%s,
                    description=%s, description_am=%s, description_ar=%s, description_en=%s,
                    price=%s, compare_price=%s, cost=%s, sku=%s, barcode=%s,
                    stock_quantity=%s, low_stock_threshold=%s,
                    images=%s, thumbnail=%s,
                    is_featured=%s, is_new=%s,
                    weight=%s, dimensions=%s, material=%s, color=%s,
                    category_id=%s,
                    meta_title=%s, meta_description=%s,
                    updated_at=CURRENT_TIMESTAMP
                   WHERE id=%s""",
                (
                    data.get('name', data.get('name_en', '')),
                    data.get('name_am', ''),
                    data.get('name_ar', ''),
                    data.get('name_en', ''),
                    data.get('description', data.get('description_en', '')),
                    data.get('description_am', ''),
                    data.get('description_ar', ''),
                    data.get('description_en', ''),
                    data.get('price'),
                    data.get('compare_price', data.get('old_price')),
                    data.get('cost'),
                    data.get('sku'),
                    data.get('barcode'),
                    data.get('stock_quantity', data.get('stock', 0)),
                    data.get('low_stock_threshold', 5),
                    images_json,
                    data.get('thumbnail', data.get('image', '')),
                    data.get('is_featured', 0),
                    data.get('is_new', 0),
                    data.get('weight'),
                    data.get('dimensions'),
                    data.get('material'),
                    data.get('color'),
                    data.get('category_id'),
                    data.get('meta_title', ''),
                    data.get('meta_description', ''),
                    pid
                )
            )
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating product {pid}: {e}")
            db.rollback()
            return False

    @staticmethod
    def delete(pid):
        """Soft delete a product (set is_active to 0)"""
        try:
            db = get_db()
            db.execute("UPDATE products SET is_active = 0 WHERE id = %s", (pid,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error deleting product {pid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def hard_delete(pid):
        """Permanently delete a product"""
        try:
            db = get_db()
            db.execute("DELETE FROM products WHERE id = %s", (pid,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error hard deleting product {pid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def update_stock(pid, quantity):
        """Update product stock quantity"""
        try:
            db = get_db()
            db.execute(
                "UPDATE products SET stock_quantity = stock_quantity - %s WHERE id = %s AND stock_quantity >= %s",
                (quantity, pid, quantity)
            )
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating stock for product {pid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_low_stock(threshold=5):
        """Get products with low stock"""
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM products WHERE stock_quantity <= %s AND stock_quantity > 0 AND is_active = 1 ORDER BY stock_quantity ASC",
                (threshold,)
            ).fetchall()
        except Exception as e:
            print(f"Error getting low stock products: {e}")
            return []
    
    @staticmethod
    def get_out_of_stock():
        """Get products that are out of stock"""
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM products WHERE stock_quantity = 0 AND is_active = 1 ORDER BY id DESC"
            ).fetchall()
        except Exception as e:
            print(f"Error getting out of stock products: {e}")
            return []


class Ad:
    """Advertisement model for database operations"""
    
    @staticmethod
    def get_all():
        """Get all active advertisements ordered by sort_order"""
        try:
            db = get_db()
            return db.execute(
                """SELECT * FROM advertisements 
                   WHERE is_active = 1 
                   AND (end_date IS NULL OR end_date > NOW())
                   AND (start_date IS NULL OR start_date <= NOW())
                   ORDER BY sort_order ASC, id DESC"""
            ).fetchall()
        except Exception as e:
            print(f"Error getting all ads: {e}")
            return []
    
    @staticmethod
    def get_all_admin():
        """Get all advertisements (including inactive) for admin panel"""
        try:
            db = get_db()
            return db.execute("SELECT * FROM advertisements ORDER BY id DESC").fetchall()
        except Exception as e:
            print(f"Error getting all admin ads: {e}")
            return []
    
    @staticmethod
    def get_by_id(aid):
        """Get a single advertisement by ID"""
        try:
            db = get_db()
            return db.execute("SELECT * FROM advertisements WHERE id = %s", (aid,)).fetchone()
        except Exception as e:
            print(f"Error getting ad by ID {aid}: {e}")
            return None
    
    @staticmethod
    def create(data):
        """Create a new advertisement"""
        try:
            db = get_db()
            cursor = db.execute(
                """INSERT INTO advertisements (
                    title, title_am, title_ar, description, description_am, description_ar,
                    image, link, sort_order, is_active, start_date, end_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id""",
                (
                    data.get('title', ''),
                    data.get('title_am', ''),
                    data.get('title_ar', ''),
                    data.get('description', data.get('text', '')),
                    data.get('description_am', ''),
                    data.get('description_ar', ''),
                    data.get('image', data.get('media', '')),
                    data.get('link', ''),
                    data.get('sort_order', 0),
                    1,
                    data.get('start_date'),
                    data.get('end_date')
                )
            )
            row = cursor.fetchone()
            db.commit()
            return row['id'] if row else None
        except Exception as e:
            print(f"Error creating ad: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def update(aid, data):
        """Update an existing advertisement"""
        try:
            db = get_db()
            db.execute(
                """UPDATE advertisements SET 
                    title=%s, title_am=%s, title_ar=%s, 
                    description=%s, description_am=%s, description_ar=%s,
                    image=%s, link=%s, sort_order=%s
                   WHERE id=%s""",
                (
                    data.get('title', ''),
                    data.get('title_am', ''),
                    data.get('title_ar', ''),
                    data.get('description', data.get('text', '')),
                    data.get('description_am', ''),
                    data.get('description_ar', ''),
                    data.get('image', data.get('media', '')),
                    data.get('link', ''),
                    data.get('sort_order', 0),
                    aid
                )
            )
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating ad {aid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def delete(aid):
        """Delete an advertisement by ID"""
        try:
            db = get_db()
            db.execute("DELETE FROM advertisements WHERE id = %s", (aid,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error deleting ad {aid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def toggle_active(aid):
        """Toggle advertisement active status"""
        try:
            db = get_db()
            db.execute(
                "UPDATE advertisements SET is_active = 1 - is_active WHERE id = %s",
                (aid,)
            )
            db.commit()
            return True
        except Exception as e:
            print(f"Error toggling ad {aid}: {e}")
            db.rollback()
            return False


class Order:
    """Order model for database operations"""
    
    @staticmethod
    def generate_order_number():
        """Generate a unique order number"""
        import random
        import string
        from datetime import datetime
        prefix = datetime.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f'{prefix}-{random_str}'
    
    @staticmethod
    def create(order_data):
        """
        Create a new order with items
        
        Args:
            order_data (dict): Order data with keys:
                - user_id (required)
                - items (list of dicts with product_id, quantity, price)
                - subtotal, shipping_fee, total
                - shipping_address, shipping_city, shipping_phone
                - payment_method, notes
        """
        try:
            db = get_db()
            
            # Generate order number if not provided
            order_number = order_data.get('order_number', Order.generate_order_number())
            
            # Create order
            cursor = db.execute(
                """INSERT INTO orders (
                    order_number, user_id, status, payment_status, payment_method,
                    subtotal, discount, shipping_fee, total,
                    shipping_address, shipping_city, shipping_phone, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id""",
                (
                    order_number,
                    order_data['user_id'],
                    order_data.get('status', 'pending'),
                    order_data.get('payment_status', 'pending'),
                    order_data.get('payment_method'),
                    order_data['subtotal'],
                    order_data.get('discount', 0),
                    order_data['shipping_fee'],
                    order_data['total'],
                    order_data['shipping_address'],
                    order_data.get('shipping_city'),
                    order_data.get('shipping_phone'),
                    order_data.get('notes')
                )
            )
            
            row = cursor.fetchone()
            order_id = row['id'] if row else None
            
            # Create order items
            for item in order_data['items']:
                db.execute(
                    """INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
                       VALUES (%s, %s, %s, %s)""",
                    (order_id, item['product_id'], item['quantity'], item['price'])
                )
                
                # Update product stock
                db.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - %s, sales_count = sales_count + %s WHERE id = %s",
                    (item['quantity'], item['quantity'], item['product_id'])
                )
            
            # Clear user's cart
            db.execute("DELETE FROM cart_items WHERE user_id = %s", (order_data['user_id'],))
            
            db.commit()
            return order_id
        except Exception as e:
            print(f"Error creating order: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_all():
        """Get all orders ordered by newest first"""
        try:
            db = get_db()
            return db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        except Exception as e:
            print(f"Error getting all orders: {e}")
            return []
    
    @staticmethod
    def get_by_id(oid):
        """Get a single order by ID"""
        try:
            db = get_db()
            return db.execute("SELECT * FROM orders WHERE id = %s", (oid,)).fetchone()
        except Exception as e:
            print(f"Error getting order by ID {oid}: {e}")
            return None
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get all orders for a specific user"""
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM orders WHERE user_id = %s ORDER BY id DESC",
                (user_id,)
            ).fetchall()
        except Exception as e:
            print(f"Error getting orders for user {user_id}: {e}")
            return []
    
    @staticmethod
    def get_by_order_number(order_number):
        """Get an order by its order number"""
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM orders WHERE order_number = %s", 
                (order_number,)
            ).fetchone()
        except Exception as e:
            print(f"Error getting order by number {order_number}: {e}")
            return None
    
    @staticmethod
    def get_items(order_id):
        """Get all items for an order"""
        try:
            db = get_db()
            return db.execute(
                """SELECT oi.*, p.name, p.name_am, p.name_ar, p.thumbnail 
                   FROM order_items oi
                   JOIN products p ON oi.product_id = p.id
                   WHERE oi.order_id = %s""",
                (order_id,)
            ).fetchall()
        except Exception as e:
            print(f"Error getting items for order {order_id}: {e}")
            return []
    
    @staticmethod
    def update_status(oid, status):
        """Update order status"""
        try:
            db = get_db()
            db.execute(
                "UPDATE orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (status, oid)
            )
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating order {oid} status: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def update_payment_status(oid, payment_status):
        """Update order payment status"""
        try:
            db = get_db()
            db.execute(
                "UPDATE orders SET payment_status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (payment_status, oid)
            )
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating order {oid} payment status: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_by_status(status):
        """Get all orders with a specific status"""
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM orders WHERE status = %s ORDER BY id DESC",
                (status,)
            ).fetchall()
        except Exception as e:
            print(f"Error getting orders by status {status}: {e}")
            return []
    
    @staticmethod
    def get_pending():
        """Get all pending orders"""
        return Order.get_by_status('pending')
    
    @staticmethod
    def get_stats():
        """Get order statistics"""
        try:
            db = get_db()
            
            # Total orders count
            cursor = db.execute("SELECT COUNT(*) FROM orders")
            total_orders = cursor.fetchone()[0] or 0
            
            # Total revenue
            cursor = db.execute("SELECT SUM(total) FROM orders WHERE status != 'cancelled'")
            total_revenue = cursor.fetchone()[0] or 0
            
            # Pending orders
            cursor = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
            pending_orders = cursor.fetchone()[0] or 0
            
            # Completed orders
            cursor = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'delivered'")
            completed_orders = cursor.fetchone()[0] or 0
            
            return {
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'pending_orders': pending_orders,
                'completed_orders': completed_orders
            }
        except Exception as e:
            print(f"Error getting order stats: {e}")
            return {
                'total_orders': 0,
                'total_revenue': 0,
                'pending_orders': 0,
                'completed_orders': 0
            }
    
    @staticmethod
    def delete(oid):
        """Delete an order by ID"""
        try:
            db = get_db()
            db.execute("DELETE FROM order_items WHERE order_id = %s", (oid,))
            db.execute("DELETE FROM orders WHERE id = %s", (oid,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error deleting order {oid}: {e}")
            db.rollback()
            return False


class User:
    """User model for database operations"""

    @staticmethod
    def get_by_id(uid):
        try:
            db = get_db()
            return db.execute("SELECT * FROM users WHERE id = %s", (uid,)).fetchone()
        except Exception as e:
            print(f"Error getting user by ID {uid}: {e}")
            return None

    @staticmethod
    def get_by_username(username):
        try:
            db = get_db()
            return db.execute("SELECT * FROM users WHERE username = %s", (username,)).fetchone()
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None

    @staticmethod
    def get_by_email(email):
        try:
            db = get_db()
            return db.execute("SELECT * FROM users WHERE email = %s", (email,)).fetchone()
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    @staticmethod
    def get_all():
        try:
            db = get_db()
            return db.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    @staticmethod
    def create(data):
        try:
            db = get_db()
            cursor = db.execute(
                """INSERT INTO users (username, email, password_hash, full_name, phone, address, city, is_admin, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (
                    data.get('username'),
                    data.get('email'),
                    data.get('password_hash'),
                    data.get('full_name', ''),
                    data.get('phone', ''),
                    data.get('address', ''),
                    data.get('city', ''),
                    data.get('is_admin', 0),
                    data.get('is_active', 1),
                )
            )
            db.commit()
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"Error creating user: {e}")
            db.rollback()
            return None

    @staticmethod
    def update(uid, data):
        try:
            db = get_db()
            db.execute(
                """UPDATE users SET full_name=%s, phone=%s, address=%s, city=%s, updated_at=CURRENT_TIMESTAMP
                   WHERE id=%s""",
                (data.get('full_name'), data.get('phone'), data.get('address'), data.get('city'), uid)
            )
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating user {uid}: {e}")
            db.rollback()
            return False

    @staticmethod
    def update_last_login(uid):
        try:
            db = get_db()
            db.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=%s", (uid,))
            db.commit()
        except Exception as e:
            print(f"Error updating last login for user {uid}: {e}")

    @staticmethod
    def delete(uid):
        try:
            db = get_db()
            db.execute("DELETE FROM users WHERE id=%s", (uid,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error deleting user {uid}: {e}")
            db.rollback()
            return False


class Category:
    """Category model for database operations"""

    @staticmethod
    def get_all():
        try:
            db = get_db()
            return db.execute("SELECT * FROM categories WHERE is_active=1 ORDER BY sort_order ASC").fetchall()
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []

    @staticmethod
    def get_all_admin():
        try:
            db = get_db()
            return db.execute("SELECT * FROM categories ORDER BY sort_order ASC").fetchall()
        except Exception as e:
            print(f"Error getting admin categories: {e}")
            return []

    @staticmethod
    def get_by_id(cid):
        try:
            db = get_db()
            return db.execute("SELECT * FROM categories WHERE id=%s", (cid,)).fetchone()
        except Exception as e:
            print(f"Error getting category {cid}: {e}")
            return None

    @staticmethod
    def create(data):
        try:
            db = get_db()
            cursor = db.execute(
                "INSERT INTO categories (name, name_am, name_ar, description, icon, image, sort_order, is_active) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                (data.get('name'), data.get('name_am'), data.get('name_ar'), data.get('description'),
                 data.get('icon'), data.get('image'), data.get('sort_order', 0), data.get('is_active', 1))
            )
            db.commit()
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"Error creating category: {e}")
            db.rollback()
            return None

    @staticmethod
    def update(cid, data):
        try:
            db = get_db()
            db.execute(
                "UPDATE categories SET name=%s, name_am=%s, name_ar=%s, description=%s, icon=%s, image=%s, sort_order=%s, is_active=%s WHERE id=%s",
                (data.get('name'), data.get('name_am'), data.get('name_ar'), data.get('description'),
                 data.get('icon'), data.get('image'), data.get('sort_order', 0), data.get('is_active', 1), cid)
            )
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating category {cid}: {e}")
            db.rollback()
            return False

    @staticmethod
    def delete(cid):
        try:
            db = get_db()
            db.execute("DELETE FROM categories WHERE id=%s", (cid,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error deleting category {cid}: {e}")
            db.rollback()
            return False


class CartItem:
    """Cart item model for database operations"""

    @staticmethod
    def get_by_user(user_id):
        try:
            db = get_db()
            return db.execute(
                """SELECT ci.*, p.name, p.name_am, p.thumbnail, p.price, p.compare_price, p.stock_quantity
                   FROM cart_items ci JOIN products p ON ci.product_id = p.id
                   WHERE ci.user_id=%s""",
                (user_id,)
            ).fetchall()
        except Exception as e:
            print(f"Error getting cart for user {user_id}: {e}")
            return []

    @staticmethod
    def add(user_id, product_id, quantity=1):
        try:
            db = get_db()
            existing = db.execute(
                "SELECT id, quantity FROM cart_items WHERE user_id=%s AND product_id=%s",
                (user_id, product_id)
            ).fetchone()
            if existing:
                db.execute(
                    "UPDATE cart_items SET quantity=quantity+%s WHERE id=%s",
                    (quantity, existing['id'])
                )
            else:
                db.execute(
                    "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s,%s,%s)",
                    (user_id, product_id, quantity)
                )
            db.commit()
            return True
        except Exception as e:
            print(f"Error adding to cart: {e}")
            db.rollback()
            return False

    @staticmethod
    def update_quantity(item_id, quantity):
        try:
            db = get_db()
            db.execute("UPDATE cart_items SET quantity=%s WHERE id=%s", (quantity, item_id))
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating cart item {item_id}: {e}")
            db.rollback()
            return False

    @staticmethod
    def remove(item_id):
        try:
            db = get_db()
            db.execute("DELETE FROM cart_items WHERE id=%s", (item_id,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error removing cart item {item_id}: {e}")
            db.rollback()
            return False

    @staticmethod
    def clear(user_id):
        try:
            db = get_db()
            db.execute("DELETE FROM cart_items WHERE user_id=%s", (user_id,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error clearing cart for user {user_id}: {e}")
            db.rollback()
            return False

    @staticmethod
    def count(user_id):
        try:
            db = get_db()
            result = db.execute(
                "SELECT SUM(quantity) FROM cart_items WHERE user_id=%s", (user_id,)
            ).fetchone()
            return result[0] or 0
        except Exception as e:
            print(f"Error counting cart items: {e}")
            return 0


class OrderItem:
    """Order item model for database operations"""

    @staticmethod
    def get_by_order(order_id):
        try:
            db = get_db()
            return db.execute(
                """SELECT oi.*, p.name, p.name_am, p.thumbnail
                   FROM order_items oi JOIN products p ON oi.product_id = p.id
                   WHERE oi.order_id=%s""",
                (order_id,)
            ).fetchall()
        except Exception as e:
            print(f"Error getting items for order {order_id}: {e}")
            return []


Advertisement = Ad


class Branch:
    """Branch model for database operations"""

    @staticmethod
    def get_all():
        try:
            db = get_db()
            return db.execute("SELECT * FROM branches WHERE is_active=1 ORDER BY sort_order ASC").fetchall()
        except Exception as e:
            print(f"Error getting branches: {e}")
            return []

    @staticmethod
    def get_by_id(bid):
        try:
            db = get_db()
            return db.execute("SELECT * FROM branches WHERE id=%s", (bid,)).fetchone()
        except Exception as e:
            print(f"Error getting branch {bid}: {e}")
            return None

    @staticmethod
    def create(data):
        try:
            db = get_db()
            cursor = db.execute(
                """INSERT INTO branches (name, name_am, name_ar, address, address_am, address_ar,
                   phone, email, latitude, longitude, working_hours, image, sort_order, is_active)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id""",
                (data.get('name'), data.get('name_am'), data.get('name_ar'),
                 data.get('address'), data.get('address_am'), data.get('address_ar'),
                 data.get('phone'), data.get('email'),
                 data.get('latitude', 0), data.get('longitude', 0),
                 data.get('working_hours'), data.get('image'),
                 data.get('sort_order', 0), data.get('is_active', 1))
            )
            row = cursor.fetchone()
            db.commit()
            return row['id'] if row else None
        except Exception as e:
            print(f"Error creating branch: {e}")
            db.rollback()
            return None

    @staticmethod
    def update(bid, data):
        try:
            db = get_db()
            db.execute(
                """UPDATE branches SET name=%s, name_am=%s, name_ar=%s, address=%s, address_am=%s, address_ar=%s,
                   phone=%s, email=%s, latitude=%s, longitude=%s, working_hours=%s, image=%s, sort_order=%s, is_active=%s
                   WHERE id=%s""",
                (data.get('name'), data.get('name_am'), data.get('name_ar'),
                 data.get('address'), data.get('address_am'), data.get('address_ar'),
                 data.get('phone'), data.get('email'),
                 data.get('latitude', 0), data.get('longitude', 0),
                 data.get('working_hours'), data.get('image'),
                 data.get('sort_order', 0), data.get('is_active', 1), bid)
            )
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating branch {bid}: {e}")
            db.rollback()
            return False

    @staticmethod
    def delete(bid):
        try:
            db = get_db()
            db.execute("DELETE FROM branches WHERE id=%s", (bid,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error deleting branch {bid}: {e}")
            db.rollback()
            return False


class Notification:
    """Notification model for database operations"""

    @staticmethod
    def get_all():
        try:
            db = get_db()
            return db.execute("SELECT * FROM notifications ORDER BY id DESC").fetchall()
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []

    @staticmethod
    def get_by_id(nid):
        try:
            db = get_db()
            return db.execute("SELECT * FROM notifications WHERE id=%s", (nid,)).fetchone()
        except Exception as e:
            print(f"Error getting notification {nid}: {e}")
            return None

    @staticmethod
    def create(data):
        try:
            db = get_db()
            cursor = db.execute(
                """INSERT INTO notifications (title, title_am, title_ar, body, body_am, body_ar,
                   image, link, target_audience, created_by)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id""",
                (data.get('title'), data.get('title_am'), data.get('title_ar'),
                 data.get('body'), data.get('body_am'), data.get('body_ar'),
                 data.get('image'), data.get('link'),
                 data.get('target_audience', 'all'), data.get('created_by'))
            )
            row = cursor.fetchone()
            db.commit()
            return row['id'] if row else None
        except Exception as e:
            print(f"Error creating notification: {e}")
            db.rollback()
            return None

    @staticmethod
    def delete(nid):
        try:
            db = get_db()
            db.execute("DELETE FROM notifications WHERE id=%s", (nid,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error deleting notification {nid}: {e}")
            db.rollback()
            return False