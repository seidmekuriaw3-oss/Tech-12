from database.db import get_db


class ProductService:
    """Service class for product management"""
    
    @staticmethod
    def get_all():
        """
        Get all products ordered by newest first.
        
        Returns:
            list: List of all products
        """
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
            print(f"Error getting all products: {e}")
            return []
    
    @staticmethod
    def get_all_admin():
        """
        Get all products including inactive for admin panel.
        
        Returns:
            list: All products
        """
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.id DESC
            """).fetchall()
        except Exception as e:
            print(f"Error getting all admin products: {e}")
            return []
    
    @staticmethod
    def get_by_id(pid):
        """
        Get a single product by ID.
        
        Args:
            pid (int): Product ID
        
        Returns:
            dict or None: Product data if found, None otherwise
        """
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name, c.name_am as category_name_am
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id = ?
            """, (pid,)).fetchone()
        except Exception as e:
            print(f"Error getting product by ID {pid}: {e}")
            return None
    
    @staticmethod
    def get_by_category(category_id):
        """
        Get all products in a specific category.
        
        Args:
            category_id (int): Category ID
        
        Returns:
            list: Products in the category
        """
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.category_id = ? AND p.is_active = 1 
                ORDER BY p.id DESC
            """, (category_id,)).fetchall()
        except Exception as e:
            print(f"Error getting products by category {category_id}: {e}")
            return []
    
    @staticmethod
    def get_featured(limit=8):
        """
        Get featured products.
        
        Args:
            limit (int): Maximum number of products to return
        
        Returns:
            list: Featured products
        """
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_featured = 1 AND p.is_active = 1 
                ORDER BY p.id DESC LIMIT ?
            """, (limit,)).fetchall()
        except Exception as e:
            print(f"Error getting featured products: {e}")
            return []
    
    @staticmethod
    def get_new(limit=8):
        """
        Get new products.
        
        Args:
            limit (int): Maximum number of products to return
        
        Returns:
            list: New products
        """
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_new = 1 AND p.is_active = 1 
                ORDER BY p.id DESC LIMIT ?
            """, (limit,)).fetchall()
        except Exception as e:
            print(f"Error getting new products: {e}")
            return []
    
    @staticmethod
    def get_by_ids(ids):
        """
        Get products by multiple IDs.
        
        Args:
            ids (list): List of product IDs
        
        Returns:
            list: Products matching the IDs
        """
        if not ids:
            return []
        
        try:
            placeholders = ','.join('?' * len(ids))
            db = get_db()
            return db.execute(f"""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id IN ({placeholders}) AND p.is_active = 1 
                ORDER BY p.id DESC
            """, ids).fetchall()
        except Exception as e:
            print(f"Error getting products by IDs: {e}")
            return []
    
    @staticmethod
    def search(query):
        """
        Search products by name (Amharic, English, or Arabic).
        
        Args:
            query (str): Search query
        
        Returns:
            list: Matching products
        """
        try:
            db = get_db()
            search = f'%{query}%'
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE (p.name LIKE ? OR p.name_am LIKE ? OR p.name_ar LIKE ?)
                AND p.is_active = 1 
                ORDER BY p.id DESC
            """, (search, search, search)).fetchall()
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    @staticmethod
    def create(data):
        """
        Create a new product.
        
        Args:
            data (dict): Product data with keys:
                - name, name_am, name_ar (required)
                - price (required)
                - category_id (required)
                - description, description_am, description_ar (optional)
                - compare_price, cost (optional)
                - sku, barcode (optional)
                - stock_quantity (optional)
                - images, thumbnail (optional)
                - is_featured, is_new (optional)
                - material, color, weight, dimensions (optional)
        
        Returns:
            int or None: New product ID if successful, None otherwise
        """
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
            print(f"Error creating product: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def update(pid, data):
        """
        Update an existing product.
        
        Args:
            pid (int): Product ID
            data (dict): Product data to update
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute("""
                UPDATE products SET 
                    name=?, name_am=?, name_ar=?,
                    description=?, description_am=?, description_ar=?,
                    price=?, compare_price=?, cost=?,
                    sku=?, barcode=?,
                    stock_quantity=?, low_stock_threshold=?,
                    images=?, thumbnail=?,
                    is_featured=?, is_new=?,
                    material=?, color=?, weight=?, dimensions=?,
                    category_id=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
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
            print(f"Error updating product {pid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def delete(pid):
        """
        Soft delete a product (set is_active to 0).
        
        Args:
            pid (int): Product ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute("UPDATE products SET is_active = 0 WHERE id = ?", (pid,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error deleting product {pid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def hard_delete(pid):
        """
        Permanently delete a product.
        
        Args:
            pid (int): Product ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute("DELETE FROM products WHERE id = ?", (pid,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error hard deleting product {pid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def update_stock(pid, quantity):
        """
        Update product stock quantity (subtract).
        
        Args:
            pid (int): Product ID
            quantity (int): Quantity to subtract
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute(
                "UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ? AND stock_quantity >= ?",
                (quantity, pid, quantity)
            )
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating stock for product {pid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def restore_stock(pid, quantity):
        """
        Restore product stock quantity (add).
        
        Args:
            pid (int): Product ID
            quantity (int): Quantity to add
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute(
                "UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
                (quantity, pid)
            )
            db.commit()
            return True
        except Exception as e:
            print(f"Error restoring stock for product {pid}: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_low_stock(threshold=5):
        """
        Get products with low stock.
        
        Args:
            threshold (int): Stock threshold (default: 5)
        
        Returns:
            list: Products with stock <= threshold and stock > 0
        """
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.stock_quantity <= ? AND p.stock_quantity > 0 AND p.is_active = 1 
                ORDER BY p.stock_quantity ASC
            """, (threshold,)).fetchall()
        except Exception as e:
            print(f"Error getting low stock products: {e}")
            return []
    
    @staticmethod
    def get_out_of_stock():
        """
        Get products that are out of stock.
        
        Returns:
            list: Products with stock = 0
        """
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
            print(f"Error getting out of stock products: {e}")
            return []
    
    @staticmethod
    def get_by_price_range(min_price, max_price):
        """
        Get products within a price range.
        
        Args:
            min_price (float): Minimum price
            max_price (float): Maximum price
        
        Returns:
            list: Products within the price range
        """
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.price BETWEEN ? AND ? AND p.is_active = 1 
                ORDER BY p.price ASC
            """, (min_price, max_price)).fetchall()
        except Exception as e:
            print(f"Error getting products by price range: {e}")
            return []
    
    @staticmethod
    def get_categories():
        """
        Get all categories with product counts.
        
        Returns:
            list: List of categories with counts
        """
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
            print(f"Error getting categories: {e}")
            return []
    
    @staticmethod
    def get_count():
        """
        Get total number of active products.
        
        Returns:
            int: Total product count
        """
        try:
            db = get_db()
            result = db.execute("SELECT COUNT(*) FROM products WHERE is_active = 1").fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Error getting product count: {e}")
            return 0
    
    @staticmethod
    def get_popular(limit=8):
        """
        Get most popular products (based on sales count).
        
        Args:
            limit (int): Maximum number of products to return
        
        Returns:
            list: Popular products
        """
        try:
            db = get_db()
            return db.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 
                ORDER BY p.sales_count DESC, p.id DESC 
                LIMIT ?
            """, (limit,)).fetchall()
        except Exception as e:
            print(f"Error getting popular products: {e}")
            return []
    
    @staticmethod
    def increment_view(pid):
        """
        Increment product view count.
        
        Args:
            pid (int): Product ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = get_db()
            db.execute("UPDATE products SET views = views + 1 WHERE id = ?", (pid,))
            db.commit()
            return True
        except Exception as e:
            print(f"Error incrementing view for product {pid}: {e}")
            return False