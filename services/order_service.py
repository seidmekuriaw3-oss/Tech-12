"""Order service — PostgreSQL only, all placeholders use %s."""
import json
from database.db import get_db
from utils.helpers import generate_order_number
from datetime import datetime
import logging
logger = logging.getLogger(__name__)


class OrderService:
    """Service class for order management."""

    @staticmethod
    def create_order(user_id, shipping_address, shipping_city, shipping_phone,
                     items, subtotal, discount, shipping_fee, total,
                     notes='', payment_method='cash'):
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
                order_number, user_id, 'pending', 'pending', payment_method,
                subtotal, discount, shipping_fee, total,
                shipping_address, shipping_city, shipping_phone, notes
            ))

            row = cursor.fetchone()
            order_id = row[0] if row else None

            for item in items:
                db.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, item['product_id'], item['quantity'], item['price']))

                db.execute("""
                    UPDATE products SET
                        stock_quantity = stock_quantity - %s,
                        sales_count = sales_count + %s
                    WHERE id = %s
                """, (item['quantity'], item['quantity'], item['product_id']))

            db.commit()
            return order_id

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            db.rollback()
            return None

    @staticmethod
    def get_all():
        try:
            db = get_db()
            return db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        except Exception as e:
            logger.error(f"Error getting all orders: {e}")
            return []

    @staticmethod
    def get_by_id(oid):
        try:
            db = get_db()
            return db.execute("SELECT * FROM orders WHERE id = %s", (oid,)).fetchone()
        except Exception as e:
            logger.error(f"Error getting order by ID {oid}: {e}")
            return None

    @staticmethod
    def get_by_user_id(user_id):
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM orders WHERE user_id = %s ORDER BY id DESC",
                (user_id,)
            ).fetchall()
        except Exception as e:
            logger.error(f"Error getting orders for user {user_id}: {e}")
            return []

    @staticmethod
    def get_by_order_number(order_number):
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM orders WHERE order_number = %s",
                (order_number,)
            ).fetchone()
        except Exception as e:
            logger.error(f"Error getting order by number {order_number}: {e}")
            return None

    @staticmethod
    def update_status(oid, status):
        valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
        if status not in valid_statuses:
            logger.warning(f"Invalid status: {status}")
            return False
        try:
            db = get_db()
            db.execute(
                "UPDATE orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
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
        valid_statuses = ['pending', 'paid', 'failed', 'refunded']
        if payment_status not in valid_statuses:
            logger.warning(f"Invalid payment status: {payment_status}")
            return False
        try:
            db = get_db()
            db.execute(
                "UPDATE orders SET payment_status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
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
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM orders WHERE status = %s ORDER BY id DESC",
                (status,)
            ).fetchall()
        except Exception as e:
            logger.error(f"Error getting orders by status {status}: {e}")
            return []

    @staticmethod
    def get_pending():
        return OrderService.get_by_status('pending')

    @staticmethod
    def get_confirmed():
        return OrderService.get_by_status('confirmed')

    @staticmethod
    def get_processing():
        return OrderService.get_by_status('processing')

    @staticmethod
    def get_shipped():
        return OrderService.get_by_status('shipped')

    @staticmethod
    def get_delivered():
        return OrderService.get_by_status('delivered')

    @staticmethod
    def get_cancelled():
        return OrderService.get_by_status('cancelled')

    @staticmethod
    def delete_order(oid):
        try:
            db = get_db()
            db.execute("DELETE FROM order_items WHERE order_id = %s", (oid,))
            db.execute("DELETE FROM orders WHERE id = %s", (oid,))
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting order {oid}: {e}")
            db.rollback()
            return False

    @staticmethod
    def get_order_items(order_id):
        try:
            db = get_db()
            return db.execute("""
                SELECT oi.*, p.name, p.name_am, p.name_ar, p.thumbnail
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """, (order_id,)).fetchall()
        except Exception as e:
            logger.error(f"Error getting order items for order {order_id}: {e}")
            return []

    @staticmethod
    def get_stats():
        try:
            db = get_db()
            total_orders   = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] or 0
            total_revenue  = db.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status = 'delivered'").fetchone()[0]
            pending_orders = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'").fetchone()[0] or 0
            processing_orders = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'processing'").fetchone()[0] or 0
            completed_orders  = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'delivered'").fetchone()[0] or 0
            cancelled_orders  = db.execute("SELECT COUNT(*) FROM orders WHERE status = 'cancelled'").fetchone()[0] or 0
            today_orders      = db.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURRENT_DATE").fetchone()[0] or 0
            return {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'pending_orders': pending_orders,
                'processing_orders': processing_orders,
                'completed_orders': completed_orders,
                'cancelled_orders': cancelled_orders,
                'today_orders': today_orders,
            }
        except Exception as e:
            logger.error(f"Error getting order stats: {e}")
            return {k: 0 for k in ('total_orders','total_revenue','pending_orders',
                                   'processing_orders','completed_orders','cancelled_orders','today_orders')}

    @staticmethod
    def get_recent(limit=10):
        try:
            db = get_db()
            return db.execute(
                "SELECT * FROM orders ORDER BY id DESC LIMIT %s", (limit,)
            ).fetchall()
        except Exception as e:
            logger.error(f"Error getting recent orders: {e}")
            return []

    @staticmethod
    def search(query):
        """Search orders by number, address, or phone — uses ILIKE for PostgreSQL."""
        try:
            db = get_db()
            search = f'%{query}%'
            return db.execute("""
                SELECT * FROM orders
                WHERE order_number ILIKE %s
                   OR shipping_address ILIKE %s
                   OR shipping_phone ILIKE %s
                ORDER BY id DESC
            """, (search, search, search)).fetchall()
        except Exception as e:
            logger.error(f"Error searching orders: {e}")
            return []

    @staticmethod
    def get_daily_sales(days=7):
        try:
            db = get_db()
            return db.execute("""
                SELECT DATE(created_at) as date,
                       COUNT(*) as order_count,
                       COALESCE(SUM(total), 0) as revenue
                FROM orders
                WHERE created_at >= NOW() - INTERVAL '%s days'
                AND status = 'delivered'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (days,)).fetchall()
        except Exception as e:
            logger.error(f"Error getting daily sales: {e}")
            return []
