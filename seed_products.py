import sqlite3
import os
import sys
from datetime import datetime
from config import Config

def seed_products(clear_existing=True, add_images=False):
    """Insert sample products into database with improved features"""
    
    # Get database path from config
    if hasattr(Config, 'DATABASE_PATH'):
        db_path = Config.DATABASE_PATH
    else:
        db_path = os.environ.get('DATABASE_PATH', 'database/ethiosadat.db')
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("Please run the application first to initialize the database.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if products table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if not cursor.fetchone():
            print("❌ Products table does not exist!")
            print("Please run the application to create tables first.")
            conn.close()
            return False
        
        # Check table structure
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Found columns: {', '.join(columns)}")
        
        print("\n" + "=" * 60)
        print("🌱 SEEDING PRODUCTS")
        print("=" * 60)
        
        # Clear existing products if requested
        if clear_existing:
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='products'")
            print("✅ Cleared existing products")
        
        # Sample products data with images
        products = [
            # ========== SOFAS (5 products) ==========
            {
                'name_am': 'ሉክስ ሶፋ',
                'name_en': 'Luxury Sofa',
                'price': '25000',
                'old_price': '35000',
                'image': 'sofa_luxury.jpg' if add_images else '',
                'category': 'ሶፋ',
                'description': 'High-end luxury sofa with premium fabric and comfortable cushions. Features solid wood frame and high-density foam.',
                'rating': 5,
                'is_active': 1,
                'featured': 1,
                'stock': 10
            },
            {
                'name_am': 'ሞደርን ሶፋ',
                'name_en': 'Modern Sofa',
                'price': '18000',
                'old_price': '25000',
                'image': 'sofa_modern.jpg' if add_images else '',
                'category': 'ሶፋ',
                'description': 'Modern design sofa perfect for contemporary homes. Available in multiple colors with removable covers.',
                'rating': 4,
                'is_active': 1,
                'featured': 1,
                'stock': 15
            },
            {
                'name_am': 'ቆዳ ሶፋ',
                'name_en': 'Leather Sofa',
                'price': '35000',
                'old_price': '45000',
                'image': 'sofa_leather.jpg' if add_images else '',
                'category': 'ሶፋ',
                'description': 'Genuine Italian leather sofa with elegant finish. Premium quality with 5-year warranty.',
                'rating': 5,
                'is_active': 1,
                'featured': 1,
                'stock': 5
            },
            {
                'name_am': 'ሚኒማል ሶፋ',
                'name_en': 'Minimalist Sofa',
                'price': '12000',
                'old_price': '18000',
                'image': 'sofa_minimalist.jpg' if add_images else '',
                'category': 'ሶፋ',
                'description': 'Simple and elegant minimalist sofa perfect for small spaces and modern apartments.',
                'rating': 4,
                'is_active': 1,
                'featured': 0,
                'stock': 20
            },
            {
                'name_am': 'ኮርነር ሶፋ',
                'name_en': 'Corner Sofa',
                'price': '42000',
                'old_price': '55000',
                'image': 'sofa_corner.jpg' if add_images else '',
                'category': 'ሶፋ',
                'description': 'Spacious corner sofa perfect for large families and entertainment areas. Includes chaise lounge.',
                'rating': 5,
                'is_active': 1,
                'featured': 1,
                'stock': 8
            },
            
            # ========== BEDS (5 products) ==========
            {
                'name_am': 'ኪንግ ሳይዝ አልጋ',
                'name_en': 'King Size Bed',
                'price': '35000',
                'old_price': '45000',
                'image': 'bed_king.jpg' if add_images else '',
                'category': 'አልጋ',
                'description': 'Premium king size bed with storage drawers. Solid wood construction with hydraulic lift mechanism.',
                'rating': 5,
                'is_active': 1,
                'featured': 1,
                'stock': 7
            },
            {
                'name_am': 'ኩዊን ሳይዝ አልጋ',
                'name_en': 'Queen Size Bed',
                'price': '28000',
                'old_price': '38000',
                'image': 'bed_queen.jpg' if add_images else '',
                'category': 'አልጋ',
                'description': 'Comfortable queen size bed with elegant headboard and under-bed storage.',
                'rating': 4,
                'is_active': 1,
                'featured': 1,
                'stock': 12
            },
            {
                'name_am': 'ሲንግል አልጋ',
                'name_en': 'Single Bed',
                'price': '12000',
                'old_price': '18000',
                'image': 'bed_single.jpg' if add_images else '',
                'category': 'አልጋ',
                'description': 'Space-saving single bed perfect for kids rooms and guest rooms. Includes mattress.',
                'rating': 4,
                'is_active': 1,
                'featured': 0,
                'stock': 25
            },
            {
                'name_am': 'ባንክ አልጋ',
                'name_en': 'Bunk Bed',
                'price': '32000',
                'old_price': '42000',
                'image': 'bed_bunk.jpg' if add_images else '',
                'category': 'አልጋ',
                'description': 'Sturdy bunk bed perfect for kids room. Includes safety rails and ladder.',
                'rating': 4,
                'is_active': 1,
                'featured': 0,
                'stock': 6
            },
            {
                'name_am': 'ኤሌክትሪክ አልጋ',
                'name_en': 'Electric Bed',
                'price': '55000',
                'old_price': '75000',
                'image': 'bed_electric.jpg' if add_images else '',
                'category': 'አልጋ',
                'description': 'Adjustable electric bed with remote control. Perfect for elderly and medical needs.',
                'rating': 5,
                'is_active': 1,
                'featured': 1,
                'stock': 3
            },
            
            # ========== MEJLIS (4 products) ==========
            {
                'name_am': 'ክላሲክ መጅሊስ',
                'name_en': 'Classic Mejlis',
                'price': '15000',
                'old_price': '22000',
                'image': 'mejlis_classic.jpg' if add_images else '',
                'category': 'መጅሊስ',
                'description': 'Traditional Ethiopian mejlis set with comfortable cushions and elegant design.',
                'rating': 5,
                'is_active': 1,
                'featured': 1,
                'stock': 10
            },
            {
                'name_am': 'ሞደርን መጅሊስ',
                'name_en': 'Modern Mejlis',
                'price': '22000',
                'old_price': '30000',
                'image': 'mejlis_modern.jpg' if add_images else '',
                'category': 'መጅሊስ',
                'description': 'Contemporary mejlis with modern design and comfortable cushions.',
                'rating': 4,
                'is_active': 1,
                'featured': 1,
                'stock': 12
            },
            {
                'name_am': 'ዲልክስ መጅሊስ',
                'name_en': 'Deluxe Mejlis',
                'price': '32000',
                'old_price': '45000',
                'image': 'mejlis_deluxe.jpg' if add_images else '',
                'category': 'መጅሊስ',
                'description': 'Premium mejlis with intricate embroidery and luxury fabrics.',
                'rating': 5,
                'is_active': 1,
                'featured': 1,
                'stock': 5
            },
            {
                'name_am': 'ሚኒ መጅሊስ',
                'name_en': 'Mini Mejlis',
                'price': '8000',
                'old_price': '12000',
                'image': 'mejlis_mini.jpg' if add_images else '',
                'category': 'መጅሊስ',
                'description': 'Compact mejlis perfect for small apartments and balconies.',
                'rating': 4,
                'is_active': 1,
                'featured': 0,
                'stock': 15
            },
            
            # ========== CURTAINS (4 products) ==========
            {
                'name_am': 'ቬልቬት መጋረጃ',
                'name_en': 'Velvet Curtain',
                'price': '5000',
                'old_price': '8000',
                'image': 'curtain_velvet.jpg' if add_images else '',
                'category': 'መጋረጃ',
                'description': 'Luxury velvet curtains with thermal lining for insulation.',
                'rating': 5,
                'is_active': 1,
                'featured': 1,
                'stock': 30
            },
            {
                'name_am': 'ሊነን መጋረጃ',
                'name_en': 'Linen Curtain',
                'price': '3500',
                'old_price': '5500',
                'image': 'curtain_linen.jpg' if add_images else '',
                'category': 'መጋረጃ',
                'description': 'Natural linen curtains that filter light beautifully.',
                'rating': 4,
                'is_active': 1,
                'featured': 0,
                'stock': 40
            },
            {
                'name_am': 'ብላክአዉት መጋረጃ',
                'name_en': 'Blackout Curtain',
                'price': '4500',
                'old_price': '7000',
                'image': 'curtain_blackout.jpg' if add_images else '',
                'category': 'መጋረጃ',
                'description': 'Complete blackout curtains perfect for bedrooms and media rooms.',
                'rating': 5,
                'is_active': 1,
                'featured': 1,
                'stock': 25
            },
            {
                'name_am': 'ሼር መጋረጃ',
                'name_en': 'Sheer Curtain',
                'price': '2000',
                'old_price': '3500',
                'image': 'curtain_sheer.jpg' if add_images else '',
                'category': 'መጋረጃ',
                'description': 'Elegant sheer curtains that add a soft touch to any room.',
                'rating': 4,
                'is_active': 1,
                'featured': 0,
                'stock': 50
            },
            
            # ========== WARDROBES (5 products) ==========
            {
                'name_am': '4 በር ቁምሳጥን',
                'name_en': '4 Door Wardrobe',
                'price': '28000',
                'old_price': '38000',
                'image': 'wardrobe_4door.jpg' if add_images else '',
                'category': 'ቁምሳጥን',
                'description': 'Spacious wardrobe with 4 doors and full-length mirror.',
                'rating': 5,
                'is_active': 1,
                'featured': 1,
                'stock': 8
            },
            {
                'name_am': '3 በር ቁምሳጥን',
                'name_en': '3 Door Wardrobe',
                'price': '22000',
                'old_price': '30000',
                'image': 'wardrobe_3door.jpg' if add_images else '',
                'category': 'ቁምሳጥን',
                'description': 'Modern wardrobe with sliding doors and internal organizers.',
                'rating': 4,
                'is_active': 1,
                'featured': 1,
                'stock': 10
            },
            {
                'name_am': '2 በር ቁምሳጥን',
                'name_en': '2 Door Wardrobe',
                'price': '15000',
                'old_price': '22000',
                'image': 'wardrobe_2door.jpg' if add_images else '',
                'category': 'ቁምሳጥን',
                'description': 'Compact wardrobe perfect for small bedrooms and guest rooms.',
                'rating': 4,
                'is_active': 1,
                'featured': 0,
                'stock': 15
            },
            {
                'name_am': 'ኮርነር ቁምሳጥን',
                'name_en': 'Corner Wardrobe',
                'price': '32000',
                'old_price': '45000',
                'image': 'wardrobe_corner.jpg' if add_images else '',
                'category': 'ቁምሳጥን',
                'description': 'Space-saving corner wardrobe that maximizes room space.',
                'rating': 5,
                'is_active': 1,
                'featured': 1,
                'stock': 6
            },
            {
                'name_am': 'ዎል ክሎዘት',
                'name_en': 'Wall Closet',
                'price': '25000',
                'old_price': '35000',
                'image': 'wardrobe_wall.jpg' if add_images else '',
                'category': 'ቁምሳጥን',
                'description': 'Built-in wall closet system with customizable shelves.',
                'rating': 5,
                'is_active': 1,
                'featured': 0,
                'stock': 5
            }
        ]
        
        # Build insert query based on available columns
        insert_query = "INSERT INTO products (name_am, name_en, price, old_price, image, category, description"
        placeholders = "%s, %s, %s, %s, %s, %s, %s"
        values_list = []
        
        # Check for optional columns
        if 'rating' in columns:
            insert_query += ", rating"
            placeholders += ", %s"
        if 'is_active' in columns:
            insert_query += ", is_active"
            placeholders += ", %s"
        if 'featured' in columns:
            insert_query += ", featured"
            placeholders += ", %s"
        if 'stock' in columns:
            insert_query += ", stock"
            placeholders += ", %s"
        if 'created_at' in columns:
            insert_query += ", created_at"
            placeholders += ", %s"
        
        insert_query += f") VALUES ({placeholders})"
        
        # Insert products
        inserted_count = 0
        for product in products:
            values = [
                product['name_am'],
                product['name_en'],
                product['price'],
                product['old_price'],
                product['image'],
                product['category'],
                product['description']
            ]
            
            if 'rating' in columns:
                values.append(product.get('rating', 4))
            if 'is_active' in columns:
                values.append(product.get('is_active', 1))
            if 'featured' in columns:
                values.append(product.get('featured', 0))
            if 'stock' in columns:
                values.append(product.get('stock', 10))
            if 'created_at' in columns:
                values.append(datetime.now().isoformat())
            
            try:
                cursor.execute(insert_query, tuple(values))
                inserted_count += 1
            except sqlite3.Error as e:
                print(f"   ⚠️  Could not insert {product['name_am']}: {e}")
        
        conn.commit()
        print(f"✅ Inserted {inserted_count} sample products")
        
        # Show product count
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        print(f"📊 Total products in database: {count}")
        
        # Show products by category
        cursor.execute("""
            SELECT category, COUNT(*) FROM products 
            GROUP BY category
            ORDER BY COUNT(*) DESC
        """)
        categories = cursor.fetchall()
        
        print("\n📁 Products by category:")
        print("-" * 40)
        for cat, cnt in categories:
            bar_length = min(30, cnt * 3)
            bar = "█" * bar_length
            print(f"   {cat:12} : {cnt:2} items {bar}")
        
        # Show price range
        cursor.execute("""
            SELECT 
                MIN(CAST(price AS FLOAT)) as min_price,
                MAX(CAST(price AS FLOAT)) as max_price,
                AVG(CAST(price AS FLOAT)) as avg_price
            FROM products
        """)
        min_price, max_price, avg_price = cursor.fetchone()
        
        print("\n💰 Price Statistics:")
        print(f"   Minimum Price: {min_price:,.0f} ETB")
        print(f"   Maximum Price: {max_price:,.0f} ETB")
        print(f"   Average Price: {avg_price:,.0f} ETB")
        
        # Show featured products count
        if 'featured' in columns:
            cursor.execute("SELECT COUNT(*) FROM products WHERE featured = 1")
            featured_count = cursor.fetchone()[0]
            print(f"\n⭐ Featured Products: {featured_count}")
        
        # Show low stock products
        if 'stock' in columns:
            cursor.execute("SELECT COUNT(*) FROM products WHERE stock < 5")
            low_stock = cursor.fetchone()[0]
            if low_stock > 0:
                print(f"⚠️  Low Stock Products: {low_stock}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Seed completed successfully!")
        
        if add_images:
            print("\n📸 Note: Image files are referenced but may not exist.")
            print("   Add images to: static/uploads/products/")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False

def show_products():
    """Display all products in the database"""
    
    # Get database path
    if hasattr(Config, 'DATABASE_PATH'):
        db_path = Config.DATABASE_PATH
    else:
        db_path = os.environ.get('DATABASE_PATH', 'database/ethiosadat.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name_am, name_en, price, old_price, category, description 
            FROM products 
            ORDER BY category, id
        """)
        products = cursor.fetchall()
        
        if not products:
            print("📭 No products found.")
            conn.close()
            return
        
        print("\n" + "=" * 80)
        print("📦 PRODUCTS LIST")
        print("=" * 80)
        
        current_category = None
        for product in products:
            if product[5] != current_category:
                current_category = product[5]
                print(f"\n🏷️  {current_category}")
                print("-" * 60)
            
            print(f"   [{product[0]}] {product[1]} / {product[2]}")
            print(f"        Price: {product[3]} ETB", end='')
            if product[4]:
                print(f" (was {product[4]} ETB)", end='')
            print()
            if product[6]:
                desc_preview = product[6][:60] + "..." if len(product[6]) > 60 else product[6]
                print(f"        {desc_preview}")
        
        print("\n" + "=" * 80)
        print(f"Total: {len(products)} products")
        print("=" * 80)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def clear_products():
    """Clear all products from database"""
    
    db_path = Config.DATABASE_PATH if hasattr(Config, 'DATABASE_PATH') else 'database/ethiosadat.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📭 No products to clear.")
            conn.close()
            return
        
        response = input(f"⚠️  Delete {count} products? (yes/no): ")
        if response.lower() == 'yes':
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='products'")
            conn.commit()
            print(f"✅ Deleted {count} products!")
        else:
            print("❌ Cancelled.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed products for Ethiosadat Furniture Store')
    parser.add_argument('--images', action='store_true', help='Include image filenames in seeding')
    parser.add_argument('--show', action='store_true', help='Show existing products')
    parser.add_argument('--clear', action='store_true', help='Clear all products')
    parser.add_argument('--append', action='store_true', help='Append without clearing existing')
    
    args = parser.parse_args()
    
    if args.show:
        show_products()
    elif args.clear:
        clear_products()
    else:
        print("\n" + "=" * 60)
        print("👗 ETHIOSADAT PRODUCT SEEDER")
        print("=" * 60)
        seed_products(clear_existing=not args.append, add_images=args.images)