from database.db import get_db
import logging
logger = logging.getLogger(__name__)


class ProductService:
    """Service class for product management — PostgreSQL only (%s placeholders)"""

    @staticmethod
    def get_all():
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 
                ORDER BY p.id DESC
            """).fetchall()
        except Exception as e:
            logger.error(f"Error getting all products: {e}")
            return []

    @staticmethod
    def get_all_admin():
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.id DESC
            """).fetchall()
        except Exception as e:
            logger.error(f"Error getting all admin products: {e}")
            return []

    @staticmethod
    def get_by_id(pid):
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name, c.name_am as category_name_am
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id = %s
            """, (pid,)).fetchone()
        except Exception as e:
            logger.error(f"Error getting product by ID {pid}: {e}")
            return None

    @staticmethod
    def get_by_category(category_id):
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.category_id = %s AND p.is_active = 1 
                ORDER BY p.id DESC
            """, (category_id,)).fetchall()
        except Exception as e:
            logger.error(f"Error getting products by category {category_id}: {e}")
            return []

    @staticmethod
    def get_featured(limit=8):
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_featured = 1 AND p.is_active = 1 
                ORDER BY p.id DESC LIMIT %s
            """, (limit,)).fetchall()
        except Exception as e:
            logger.error(f"Error getting featured products: {e}")
            return []

    @staticmethod
    def get_new(limit=8):
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_new = 1 AND p.is_active = 1 
                ORDER BY p.id DESC LIMIT %s
            """, (limit,)).fetchall()
        except Exception as e:
            logger.error(f"Error getting new products: {e}")
            return []

    @staticmethod
    def get_by_ids(ids):
        if not ids:
            return []
        try:
            placeholders = ','.join(['%s'] * len(ids))
            db = get_db()
            return db.execute(f"""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id IN ({placeholders}) AND p.is_active = 1 
                ORDER BY p.id DESC
            """, ids).fetchall()
        except Exception as e:
            logger.error(f"Error getting products by IDs: {e}")
            return []

    @staticmethod
    def search(query):
        """Search products — uses ILIKE for case-insensitive PostgreSQL search."""
        try:
            db = get_db()
            search = f'%{query}%'
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE (p.name ILIKE %s OR p.name_am ILIKE %s OR p.name_ar ILIKE %s
                       OR p.description ILIKE %s OR p.description_am ILIKE %s)
                AND p.is_active = 1 
                ORDER BY p.id DESC
            """, (search, search, search, search, search)).fetchall()
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []

    @staticmethod
    def create(data):
        try:
            db = get_db()
            cursor = db.execute("""
                INSERT INTO products (
                    name, name_am, name_ar,
                    description, description_am, description_ar,
                    price, compare_price, cost,
                    sku, barcode,
                    stock_quantity, low_stock_threshold,
                    images, thumbnail,
                    is_featured, is_new, is_active,
                    material, color, weight, dimensions,
                    category_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data.get('name', data.get('name_en', '')),
                data.get('name_am', ''),
                data.get('name_ar', ''),
                data.get('description', data.get('description_en', '')),
                data.get('description_am', ''),
                data.get('description_ar', ''),
                data.get('price', 0),
                data.get('compare_price', data.get('old_price')),
                data.get('cost'),
                data.get('sku'),
                data.get('barcode'),
                data.get('stock_quantity', data.get('stock', 0)),
                data.get('low_stock_threshold', 5),
                data.get('images'),
                data.get('thumbnail', data.get('image', '')),
                data.get('is_featured', 0),
                data.get('is_new', 0),
                data.get('material'),
                data.get('color'),
                data.get('weight'),
                data.get('dimensions'),
                data.get('category_id')
            ))
            db.commit()
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            db.rollback()
            return None

    @staticmethod
    def update(pid, data):
        try:
            db = get_db()
            db.execute("""
                UPDATE products SET 
                    name=%s, name_am=%s, name_ar=%s,
                    description=%s, description_am=%s, description_ar=%s,
                    price=%s, compare_price=%s, cost=%s,
                    sku=%s, barcode=%s,
                    stock_quantity=%s, low_stock_threshold=%s,
                    images=%s, thumbnail=%s,
                    is_featured=%s, is_new=%s,
                    material=%s, color=%s, weight=%s, dimensions=%s,
                    category_id=%s, updated_at=CURRENT_TIMESTAMP
                WHERE id=%s
            """, (
                data.get('name', data.get('name_en', '')),
                data.get('name_am', ''),
                data.get('name_ar', ''),
                data.get('description', data.get('description_en', '')),
                data.get('description_am', ''),
                data.get('description_ar', ''),
                data.get('price'),
                data.get('compare_price', data.get('old_price')),
                data.get('cost'),
                data.get('sku'),
                data.get('barcode'),
                data.get('stock_quantity', data.get('stock', 0)),
                data.get('low_stock_threshold', 5),
                data.get('images'),
                data.get('thumbnail', data.get('image', '')),
                data.get('is_featured', 0),
                data.get('is_new', 0),
                data.get('material'),
                data.get('color'),
                data.get('weight'),
                data.get('dimensions'),
                data.get('category_id'),
                pid
            ))
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating product {pid}: {e}")
            db.rollback()
            return False

    @staticmethod
    def delete(pid):
        """Soft delete — marks is_active = 0."""
        try:
            db = get_db()
            db.execute("UPDATE products SET is_active = 0 WHERE id = %s", (pid,))
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting product {pid}: {e}")
            db.rollback()
            return False

    @staticmethod
    def hard_delete(pid):
        """Permanently remove a product row."""
        try:
            db = get_db()
            db.execute("DELETE FROM products WHERE id = %s", (pid,))
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error hard deleting product {pid}: {e}")
            db.rollback()
            return False

    @staticmethod
    def update_stock(pid, quantity):
        """Subtract quantity from stock (atomic — only succeeds if enough stock exists)."""
        try:
            db = get_db()
            db.execute(
                "UPDATE products SET stock_quantity = stock_quantity - %s WHERE id = %s AND stock_quantity >= %s",
                (quantity, pid, quantity)
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating stock for product {pid}: {e}")
            db.rollback()
            return False

    @staticmethod
    def restore_stock(pid, quantity):
        """Add quantity back to stock."""
        try:
            db = get_db()
            db.execute(
                "UPDATE products SET stock_quantity = stock_quantity + %s WHERE id = %s",
                (quantity, pid)
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error restoring stock for product {pid}: {e}")
            db.rollback()
            return False

    @staticmethod
    def get_low_stock(threshold=5):
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.stock_quantity <= %s AND p.stock_quantity > 0 AND p.is_active = 1 
                ORDER BY p.stock_quantity ASC
            """, (threshold,)).fetchall()
        except Exception as e:
            logger.error(f"Error getting low stock products: {e}")
            return []

    @staticmethod
    def get_out_of_stock():
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.stock_quantity = 0 AND p.is_active = 1 
                ORDER BY p.id DESC
            """).fetchall()
        except Exception as e:
            logger.error(f"Error getting out of stock products: {e}")
            return []

    @staticmethod
    def get_by_price_range(min_price, max_price):
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.price BETWEEN %s AND %s AND p.is_active = 1 
                ORDER BY p.price ASC
            """, (min_price, max_price)).fetchall()
        except Exception as e:
            logger.error(f"Error getting products by price range: {e}")
            return []

    @staticmethod
    def get_categories():
        try:
            db = get_db()
            return db.execute("""
                SELECT c.*, COUNT(p.id) as product_count
                FROM categories c
                LEFT JOIN products p ON p.category_id = c.id AND p.is_active = 1
                WHERE c.is_active = 1
                GROUP BY c.id
                ORDER BY c.sort_order ASC
            """).fetchall()
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []

    @staticmethod
    def get_count():
        try:
            db = get_db()
            result = db.execute("SELECT COUNT(*) FROM products WHERE is_active = 1").fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting product count: {e}")
            return 0

    @staticmethod
    def get_popular(limit=8):
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 
                ORDER BY p.sales_count DESC, p.id DESC 
                LIMIT %s
            """, (limit,)).fetchall()
        except Exception as e:
            logger.error(f"Error getting popular products: {e}")
            return []

    @staticmethod
    def increment_view(pid):
        try:
            db = get_db()
            db.execute("UPDATE products SET views = views + 1 WHERE id = %s", (pid,))
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error incrementing view for product {pid}: {e}")
            return False
