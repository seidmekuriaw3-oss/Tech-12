import json
from database.db import get_db
from utils.helpers import generate_order_number
from datetime import datetime
import logging
logger = logging.getLogger(__name__)


class OrderService:
    """Service class for order management"""
    
    @staticmethod
    def create_order(user_id, shipping_address, shipping_city, shipping_phone, items, subtotal, discount, shipping_fee, total, notes='', payment_method='cash'):
        """
        Create a new order with items.
        
        Args:
            user_id (int): Customer user ID
            shipping_address (str): Delivery address
            shipping_city (str): City
            shipping_phone (str): Contact phone
            items (list): List of ordered items with product_id, quantity, price
            subtotal (float): Order subtotal
            discount (float): Discount amount (10% for logged in users)
            shipping_fee (float): Shipping cost
            total (float): Order total
            notes (str): Additional order notes
            payment_method (str): Payment method ('cash', 'bank', etc.)
        
        Returns:
            int or None: Order ID if successful, None otherwise
        """
        try:
            db = get_db()
            order_number = generate_order_number()
            
            cursor = db.execute("""
                INSERT INTO orders (
                    order_number, user_id, status, payment_status, payment_method,
                    subtotal, discount, shipping_fee, total,
                    shipping_address, shipping_city, shipping_phone, notes,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, (
                order_number, 
                user_id,
                'pending',
                'pending',
                payment_method,
                subtotal, 
                discount, 
                shipping_fee, 
                total, 
                shipping_address,
                shipping_city,
                shipping_phone,
                notes
            ))
            
            row = cursor.fetchone()
            order_id = row[0] if row else None
            
            # Create order items
            for item in items:
                db.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
                    VALUES (?, ?, ?, ?)
                """, (order_id, item['product_id'], item['quantity'], item['price']))
                
                # Update product stock and sales count
                db.execute("""
                    UPDATE products SET 
                        stock_quantity = stock_quantity - ?,
                        sales_count = sales_count + ?
                    WHERE id = ?
                """, (item['quantity'], item['quantity'], item['product_id']))
            
            db.commit()
            return order_id
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_all():
        """
        Get all orders ordered by newest first.
        
        Returns:
            list: List of all orders
        """
        try:
            db = get_db()
            return db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        except Exception as e:
            logger.error(f"Error getting all orders: {e}")
            return []
    
    @staticmethod
    def get_by_id(oid):
        """
        Get a single order by ID.
        
        Args:
            oid (int): Order ID
        
        Returns:
            dict or None: Order data if found, None otherwise
        """
        try:
            db = get_db()
            return db.execute("SELECT * FROM orders WHERE id = ?", (oid,)).fetchone()
        except Exception as e:
            logger.error(f"Error getting order by ID {oid}: {e}")
            return None
    
    @staticmethod
    def get_by_user_id(user_id):
        """
        Get all orders for a specific user.
        
        Args:
            user_id (int): User ID
        
        Returns:
            list: List of user orders
        """
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC",
                (user_id,)
            ).fetchall()
        except Exception as e:
            logger.error(f"Error getting orders for user {user_id}: {e}")
            return []
    
    @staticmethod
    def get_by_order_number(order_number):
        """
        Get an order by its order number.
        
        Args:
            order_number (str): Order number (e.g., ORD-20241225-ABCD)
        
        Returns:
            dict or None: Order data if found, None otherwise
        """
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM orders WHERE order_number = ?", 
                (order_number,)
            ).fetchone()
        except Exception as e:
            logger.error(f"Error getting order by number {order_number}: {e}")
            return None
    
    @staticmethod
    def update_status(oid, status):
        """
        Update order status.
        
        Args:
            oid (int): Order ID
            status (str): New status ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled')
        
        Returns:
            bool: True if successful, False otherwise
        """
        valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
        
        if status not in valid_statuses:
            logger.warning(f"Invalid status: {status}")
            return False
        
        try:
            db = get_db()
            db.execute(
                "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                (status, oid)
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating order {oid} status: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def update_payment_status(oid, payment_status):
        """
        Update order payment status.
        
        Args:
            oid (int): Order ID
            payment_status (str): Payment status ('pending', 'paid', 'failed', 'refunded')
        
        Returns:
            bool: True if successful, False otherwise
        """
        valid_statuses = ['pending', 'paid', 'failed', 'refunded']
        
        if payment_status not in valid_statuses:
            logger.warning(f"Invalid payment status: {payment_status}")
            return False
        
        try:
            db = get_db()
            db.execute(
                "UPDATE orders SET payment_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                (payment_status, oid)
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating order {oid} payment status: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_by_status(status):
        """
        Get all orders with a specific status.
        
        Args:
            status (str): Order status
        
        Returns:
            list: List of orders with the given status
        """
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM orders WHERE status = ? ORDER BY id DESC",
                (status,)
            ).fetchall()
        except Exception as e:
            logger.error(f"Error getting orders by status {status}: {e}")
            return []
    
    @staticmethod
    def get_pending():
        """Get all pending orders."""
        return OrderService.get_by_status('pending')
    
    @staticmethod
    def get_confirmed():
        """Get all confirmed orders."""
        return OrderService.get_by_status('confirmed')
    
    @staticmethod
    def get_processing():
        """Get all processing orders."""
        return OrderService.get_by_status('processing')
    
    @staticmethod
    def get_shipped():
        """Get all shipped orders."""
        return OrderService.get_by_status('shipped')
    
    @staticmethod
    def get_delivered():
        """Get all delivered orders."""
        return OrderService.get_by_status('delivered')
    
    @staticmethod
    def get_cancelled():
        """Get all cancelled orders."""
        return OrderService.get_by_status('cancelled')
    
    @staticmethod
    def delete_order(oid):
        """
        Delete an order by ID (cascade deletes order items).
        
        Args:
            oid (int): Order ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute("DELETE FROM order_items WHERE order_id = ?", (oid,))
            db.execute("DELETE FROM orders WHERE id = ?", (oid,))
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting order {oid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_order_items(order_id):
        """
        Get order items for a specific order.
        
        Args:
            order_id (int): Order ID
        
        Returns:
            list: List of order items with product details
        """
        try:
            db = get_db()
            return db.execute("""
                SELECT oi.*, p.name, p.name_am, p.name_ar, p.thumbnail
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (order_id,)).fetchall()
        except Exception as e:
            logger.error(f"Error getting order items for order {order_id}: {e}")
            return []
    
    @staticmethod
    def get_stats():
        """
        Get order statistics for reports.
        
        Returns:
            dict: Statistics including counts and total revenue
        """
        try:
            db = get_db()
            
            # Total orders
            cursor = db.execute("SELECT COUNT(*) FROM orders")
            total_orders = cursor.fetchone()[0] or 0
            
            # Total revenue (from delivered orders)
            cursor = db.execute(
                "SELECT SUM(total) FROM orders WHERE status = 'delivered'"
            )
            total_revenue = cursor.fetchone()[0] or 0
            
            # Pending orders
            cursor = db.execute(
                "SELECT COUNT(*) FROM orders WHERE status = 'pending'"
            )
            pending_orders = cursor.fetchone()[0] or 0
            
            # Processing orders
            cursor = db.execute(
                "SELECT COUNT(*) FROM orders WHERE status = 'processing'"
            )
            processing_orders = cursor.fetchone()[0] or 0
            
            # Completed (delivered) orders
            cursor = db.execute(
                "SELECT COUNT(*) FROM orders WHERE status = 'delivered'"
            )
            completed_orders = cursor.fetchone()[0] or 0
            
            # Cancelled orders
            cursor = db.execute(
                "SELECT COUNT(*) FROM orders WHERE status = 'cancelled'"
            )
            cancelled_orders = cursor.fetchone()[0] or 0
            
            # Today's orders
            cursor = db.execute(
                "SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURRENT_DATE"
            )
            today_orders = cursor.fetchone()[0] or 0
            
            return {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'pending_orders': pending_orders,
                'processing_orders': processing_orders,
                'completed_orders': completed_orders,
                'cancelled_orders': cancelled_orders,
                'today_orders': today_orders
            }
        except Exception as e:
            logger.error(f"Error getting order stats: {e}")
            return {
                'total_orders': 0,
                'total_revenue': 0,
                'pending_orders': 0,
                'processing_orders': 0,
                'completed_orders': 0,
                'cancelled_orders': 0,
                'today_orders': 0
            }
    
    @staticmethod
    def get_recent(limit=10):
        """
        Get recent orders.
        
        Args:
            limit (int): Maximum number of orders to return
        
        Returns:
            list: Recent orders
        """
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM orders ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
        except Exception as e:
            logger.error(f"Error getting recent orders: {e}")
            return []
    
    @staticmethod
    def search(query):
        """
        Search orders by order number, customer name, phone, or address.
        
        Args:
            query (str): Search query
        
        Returns:
            list: Matching orders
        """
        try:
            db = get_db()
            search = f'%{query}%'
            return db.execute("""
                SELECT * FROM orders 
                WHERE order_number LIKE ? 
                OR shipping_address LIKE ?
                OR shipping_phone LIKE ?
                ORDER BY id DESC
            """, (search, search, search)).fetchall()
        except Exception as e:
            logger.error(f"Error searching orders: {e}")
            return []
    
    @staticmethod
    def get_daily_sales(days=7):
        """
        Get daily sales for the last N days.
        
        Args:
            days (int): Number of days to look back
        
        Returns:
            list: Daily sales data
        """
        try:
            db = get_db()
            return db.execute("""
                SELECT DATE(created_at) as date, 
                       COUNT(*) as order_count, 
                       SUM(total) as revenue
                FROM orders 
                WHERE created_at >= NOW() - INTERVAL '%s days'
                AND status = 'delivered'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (days,)).fetchall()
        except Exception as e:
            logger.error(f"Error getting daily sales: {e}")
            return []