import os
import logging
from flask import session

logger = logging.getLogger(__name__)


def _get_discount_rate():
    """Return the configured member discount rate (avoids circular import)."""
    try:
        from routes.shared import USER_DISCOUNT_RATE
        return USER_DISCOUNT_RATE
    except Exception:
        return 0.10


class CartService:
    """Service class for shopping cart operations"""
    
    @staticmethod
    def get_cart():
        """
        Get the current cart from session.
        
        Returns:
            dict: Cart as {product_id_str: quantity}
        """
        return session.get('cart', {})
    
    @staticmethod
    def get_count():
        """
        Get total number of items in cart (sum of quantities).
        
        Returns:
            int: Total item count
        """
        try:
            cart = session.get('cart', {})
            if isinstance(cart, dict):
                return sum(cart.values())
            elif isinstance(cart, list):
                return sum(item.get('quantity', 1) for item in cart)
            return 0
        except Exception:
            return 0
    
    @staticmethod
    def get_subtotal():
        """
        Calculate cart subtotal (items total without shipping).
        
        Returns:
            float: Subtotal amount
        """
        try:
            cart = session.get('cart', {})
            if isinstance(cart, dict):
                # Cart is stored as dict {product_id: quantity}
                from database.db import get_db
                if cart:
                    db = get_db()
                    cursor = db.cursor()
                    placeholders = ','.join(['%s'] * len(cart))
                    cursor.execute(f"""
                        SELECT id, price FROM products WHERE id IN ({placeholders})
                    """, list(cart.keys()))
                    products = cursor.fetchall()
                    subtotal = 0
                    for p in products:
                        quantity = cart.get(str(p['id']), 0)
                        subtotal += float(p['price'] or 0) * quantity
                    return subtotal
            elif isinstance(cart, list):
                # Cart is stored as list of items
                subtotal = 0
                for item in cart:
                    subtotal += float(item.get('price', 0)) * item.get('quantity', 1)
                return subtotal
            return 0
        except Exception as e:
            logger.error(f"Error calculating subtotal: {e}")
            return 0
    
    @staticmethod
    def get_shipping_cost():
        """
        Calculate shipping cost based on subtotal.
        Free shipping if subtotal >= threshold (default 5000 ETB).
        
        Returns:
            float: Shipping cost
        """
        try:
            subtotal = CartService.get_subtotal()
            threshold = float(os.environ.get('FREE_SHIPPING_THRESHOLD', '5000'))
            shipping_cost = float(os.environ.get('SHIPPING_COST', '200'))
            return 0 if subtotal >= threshold else shipping_cost
        except Exception:
            return 200
    
    @staticmethod
    def get_discount():
        """
        Calculate discount for logged in users (10%).
        
        Returns:
            float: Discount amount
        """
        from flask import session
        try:
            subtotal = CartService.get_subtotal()
            if session.get('user_id'):
                return subtotal * 0.1
            return 0
        except Exception:
            return 0
    
    @staticmethod
    def get_total():
        """
        Calculate cart total including discount and shipping.
        
        Returns:
            float: Total amount (subtotal - discount + shipping)
        """
        subtotal = CartService.get_subtotal()
        discount = CartService.get_discount()
        shipping = CartService.get_shipping_cost()
        return subtotal - discount + shipping
    
    @staticmethod
    def get_items():
        """
        Get cart items with calculated totals for each item.
        
        Returns:
            list: Cart items with 'total' field added
        """
        try:
            cart = session.get('cart', {})
            items = []
            
            if isinstance(cart, dict) and cart:
                from database.db import get_db
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
                        items.append({
                            'product_id': p['id'],
                            'name': p['name'],
                            'name_am': p['name_am'],
                            'name_ar': p['name_ar'],
                            'price': float(p['price'] or 0),
                            'discounted_price': round(float(p['price'] or 0) * (1 - _get_discount_rate()), 2) if session.get('user_id') else float(p['price'] or 0),
                            'quantity': quantity,
                            'thumbnail': p['thumbnail'],
                            'stock_quantity': p['stock_quantity'],
                            'subtotal': float(p['price'] or 0) * quantity
                        })
            elif isinstance(cart, list):
                for item in cart:
                    items.append({
                        'id': item.get('id'),
                        'name': item.get('name'),
                        'price': float(item.get('price', 0)),
                        'quantity': item.get('quantity', 1),
                        'image': item.get('image', ''),
                        'total': float(item.get('price', 0)) * item.get('quantity', 1)
                    })
            
            return items
        except Exception as e:
            logger.error(f"Error getting cart items: {e}")
            return []
    
    @staticmethod
    def add_item(product_id, quantity=1):
        """
        Add a product to the cart.
        
        Args:
            product_id (int): Product identifier
            quantity (int): Quantity to add (default: 1)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check stock availability
            from database.db import get_db
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT id, stock_quantity FROM products WHERE id = %s AND is_active = 1", (product_id,))
            product = cursor.fetchone()
            
            if not product:
                return False
            
            cart = session.get('cart', {})
            product_id_str = str(product_id)
            
            current_quantity = cart.get(product_id_str, 0)
            new_quantity = current_quantity + quantity
            
            if product['stock_quantity'] < new_quantity:
                return False
            
            cart[product_id_str] = new_quantity
            session['cart'] = cart
            session.modified = True
            return True
            
        except Exception as e:
            logger.error(f"Error adding item to cart: {e}")
            return False
    
    @staticmethod
    def remove_item(product_id):
        """
        Remove a product from the cart.
        
        Args:
            product_id (int): Product identifier to remove
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cart = session.get('cart', {})
            product_id_str = str(product_id)
            
            if product_id_str in cart:
                del cart[product_id_str]
                session['cart'] = cart
                session.modified = True
            
            return True
        except Exception as e:
            logger.error(f"Error removing item from cart: {e}")
            return False
    
    @staticmethod
    def update_quantity(product_id, quantity):
        """
        Update quantity of a cart item.
        
        Args:
            product_id (int): Product identifier
            quantity (int): New quantity (if < 1, removes item)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if quantity < 1:
                return CartService.remove_item(product_id)
            
            # Check stock availability
            from database.db import get_db
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT stock_quantity FROM products WHERE id = %s AND is_active = 1", (product_id,))
            product = cursor.fetchone()
            
            if product and product['stock_quantity'] < quantity:
                return False
            
            cart = session.get('cart', {})
            cart[str(product_id)] = quantity
            session['cart'] = cart
            session.modified = True
            return True
        except Exception as e:
            logger.error(f"Error updating cart quantity: {e}")
            return False
    
    @staticmethod
    def clear():
        """Clear all items from the cart."""
        try:
            session.pop('cart', None)
            session.modified = True
            return True
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            return False
    
    @staticmethod
    def item_exists(product_id):
        """
        Check if a product exists in the cart.
        
        Args:
            product_id (int): Product identifier
        
        Returns:
            bool: True if exists, False otherwise
        """
        try:
            cart = session.get('cart', {})
            return str(product_id) in cart
        except Exception:
            return False
    
    @staticmethod
    def get_item_quantity(product_id):
        """
        Get quantity of a specific item in cart.
        
        Args:
            product_id (int): Product identifier
        
        Returns:
            int: Quantity (0 if not found)
        """
        try:
            cart = session.get('cart', {})
            return cart.get(str(product_id), 0)
        except Exception:
            return 0
    
    @staticmethod
    def get_item_subtotal(product_id):
        """
        Get subtotal price for a specific item in cart.
        
        Args:
            product_id (int): Product identifier
        
        Returns:
            float: Item subtotal (price * quantity)
        """
        try:
            from database.db import get_db
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            
            if product:
                quantity = CartService.get_item_quantity(product_id)
                return product['price'] * quantity
            return 0
        except Exception:
            return 0
    
    @staticmethod
    def is_empty():
        """
        Check if cart is empty.
        
        Returns:
            bool: True if empty, False otherwise
        """
        try:
            cart = session.get('cart', {})
            return len(cart) == 0
        except Exception:
            return True
    
    @staticmethod
    def sync_with_database(user_id):
        """
        Sync session cart with database cart after login.
        
        Args:
            user_id (int): User ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from database.db import get_db
            db = get_db()
            cursor = db.cursor()
            
            # Get session cart
            session_cart = session.get('cart', {})
            
            # Get database cart
            cursor.execute("SELECT product_id, quantity FROM cart_items WHERE user_id = %s", (user_id,))
            db_cart = {str(row['product_id']): row['quantity'] for row in cursor.fetchall()}
            
            # Merge carts (session cart takes priority)
            for product_id, quantity in session_cart.items():
                if product_id in db_cart:
                    new_quantity = db_cart[product_id] + quantity
                    cursor.execute("""
                        UPDATE cart_items SET quantity = %s
                        WHERE user_id = %s AND product_id = %s
                    """, (new_quantity, user_id, product_id))
                else:
                    cursor.execute("""
                        INSERT INTO cart_items (user_id, product_id, quantity)
                        VALUES (%s, %s, %s)
                    """, (user_id, product_id, quantity))
            
            db.commit()
            
            # Clear session cart
            session.pop('cart', None)
            session.modified = True
            
            return True
        except Exception as e:
            logger.error(f"Error syncing cart with database: {e}")
            return False
    
    @staticmethod
    def to_dict():
        """
        Get cart summary as a dictionary.
        
        Returns:
            dict: Cart summary with items, count, subtotal, shipping, total
        """
        return {
            'items': CartService.get_items(),
            'count': CartService.get_count(),
            'subtotal': CartService.get_subtotal(),
            'discount': CartService.get_discount(),
            'shipping': CartService.get_shipping_cost(),
            'total': CartService.get_total(),
            'is_empty': CartService.is_empty()
        }