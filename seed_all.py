import sqlite3
import os
import sys
from datetime import datetime
from config import Config

def seed_all(clear_existing=True):
    """Insert all sample data into database with improved structure"""
    
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
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n" + "=" * 60)
        print("🌱 ETHIOSADAT DATABASE SEEDER")
        print("=" * 60)
        
        # ==================== CHECK TABLE STRUCTURE ====================
        print("\n📋 Checking database structure...")
        
        # Get existing columns for each table
        cursor.execute("PRAGMA table_info(products)")
        product_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(ads)")
        ad_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(settings)")
        settings_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(orders)")
        orders_exists = cursor.fetchone() is not None
        
        # ==================== PRODUCTS ====================
        print("\n📦 Seeding products...")
        
        if clear_existing:
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='products'")
            print("   ✓ Cleared existing products")
        
        # Enhanced product data with images
        products = [
            # Sofas
            ('ሉክስ ሶፋ', 'Luxury Sofa', '25000', '35000', 'sofa_luxury.jpg', 'ሶፋ', 'High-end luxury sofa with premium fabric and solid wood frame', 5, 1),
            ('ሞደርን ሶፋ', 'Modern Sofa', '18000', '25000', 'sofa_modern.jpg', 'ሶፋ', 'Contemporary design sofa with comfortable seating', 4, 1),
            ('ቆዳ ሶፋ', 'Leather Sofa', '35000', '45000', 'sofa_leather.jpg', 'ሶፋ', 'Genuine Italian leather sofa with elegant design', 5, 1),
            ('ሚኒማል ሶፋ', 'Minimalist Sofa', '12000', '18000', 'sofa_minimalist.jpg', 'ሶፋ', 'Sleek minimalist design for modern homes', 4, 1),
            ('ኮርነር ሶፋ', 'Corner Sofa', '32000', '42000', 'sofa_corner.jpg', 'ሶፋ', 'Spacious L-shaped corner sofa', 5, 1),
            
            # Beds
            ('ኪንግ ሳይዝ አልጋ', 'King Size Bed', '35000', '45000', 'bed_king.jpg', 'አልጋ', 'Premium king size bed with storage drawers', 5, 1),
            ('ኩዊን ሳይዝ አልጋ', 'Queen Size Bed', '28000', '38000', 'bed_queen.jpg', 'አልጋ', 'Elegant queen size bed with headboard', 4, 1),
            ('ድብል አልጋ', 'Double Bed', '18000', '25000', 'bed_double.jpg', 'አልጋ', 'Comfortable double bed with mattress', 4, 1),
            ('ሲንግል አልጋ', 'Single Bed', '12000', '18000', 'bed_single.jpg', 'አልጋ', 'Single bed with under-bed storage', 3, 1),
            
            # Mejlis (Traditional seating)
            ('ክላሲክ መጅሊስ', 'Classic Mejlis', '15000', '22000', 'mejlis_classic.jpg', 'መጅሊስ', 'Traditional Ethiopian mejlis set', 5, 1),
            ('ሞደርን መጅሊስ', 'Modern Mejlis', '22000', '30000', 'mejlis_modern.jpg', 'መጅሊስ', 'Contemporary mejlis with cushions', 4, 1),
            ('ሚኒ መጅሊስ', 'Mini Mejlis', '8000', '12000', 'mejlis_mini.jpg', 'መጅሊስ', 'Compact mejlis for small spaces', 4, 1),
            ('ዴሉክስ መጅሊስ', 'Deluxe Mejlis', '28000', '38000', 'mejlis_deluxe.jpg', 'መጅሊስ', 'Premium mejlis with velvet cushions', 5, 1),
            
            # Curtains
            ('ቬልቬት መጋረጃ', 'Velvet Curtain', '5000', '8000', 'curtain_velvet.jpg', 'መጋረጃ', 'Luxury velvet curtains for living room', 4, 1),
            ('ብላክአዉት መጋረጃ', 'Blackout Curtain', '4500', '7000', 'curtain_blackout.jpg', 'መጋረጃ', 'Complete blackout curtains for bedroom', 5, 1),
            ('ሼር መጋረጃ', 'Sheer Curtain', '2000', '3500', 'curtain_sheer.jpg', 'መጋረጃ', 'Light and airy sheer curtains', 3, 1),
            ('ሮማን መጋረጃ', 'Roman Curtain', '3500', '5500', 'curtain_roman.jpg', 'መጋረጃ', 'Elegant Roman shade curtains', 4, 1),
            
            # Wardrobes
            ('4 በር ቁምሳጥን', '4 Door Wardrobe', '28000', '38000', 'wardrobe_4door.jpg', 'ቁምሳጥን', 'Spacious 4-door wardrobe with mirrors', 5, 1),
            ('3 በር ቁምሳጥን', '3 Door Wardrobe', '22000', '30000', 'wardrobe_3door.jpg', 'ቁምሳጥን', 'Sliding door wardrobe with organizers', 4, 1),
            ('2 በር ቁምሳጥን', '2 Door Wardrobe', '15000', '22000', 'wardrobe_2door.jpg', 'ቁምሳጥን', 'Compact 2-door wardrobe', 4, 1),
            ('ዎል ክሎዘት', 'Wall Closet', '18000', '26000', 'wardrobe_wall.jpg', 'ቁምሳጥን', 'Built-in wall closet system', 4, 1),
        ]
        
        # Build insert query based on available columns
        insert_product = "INSERT INTO products (name_am, name_en, price, old_price, image, category, description"
        placeholders = "?, ?, ?, ?, ?, ?, ?"
        values_list = []
        
        if 'rating' in product_columns:
            insert_product += ", rating"
            placeholders += ", ?"
        if 'is_active' in product_columns:
            insert_product += ", is_active"
            placeholders += ", ?"
        if 'created_at' in product_columns:
            insert_product += ", created_at"
            placeholders += ", ?"
        
        insert_product += f") VALUES ({placeholders})"
        
        inserted_products = 0
        for p in products:
            values = list(p[:7])  # First 7 values
            if 'rating' in product_columns:
                values.append(p[7] if len(p) > 7 else 4)
            if 'is_active' in product_columns:
                values.append(p[8] if len(p) > 8 else 1)
            if 'created_at' in product_columns:
                values.append(datetime.now().isoformat())
            
            try:
                cursor.execute(insert_product, tuple(values))
                inserted_products += 1
            except sqlite3.Error as e:
                print(f"   ⚠️  Could not insert product {p[0]}: {e}")
        
        print(f"   ✅ Inserted {inserted_products} products")
        
        # ==================== ADS ====================
        print("\n📢 Seeding advertisements...")
        
        if clear_existing:
            cursor.execute("DELETE FROM ads")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='ads'")
            print("   ✓ Cleared existing ads")
        
        # Enhanced ads with types and links
        ads = [
            ('🎉 ልዩ ቅናሽ! እስከ 30% ቅናሽ በሁሉም ምርቶች ላይ! ውሱን ጊዜ ብቻ!', 'discount', '#ff4444', '/category/all', 1, 1),
            ('🚚 ነጻ ማጓጓዝ ከ5000 ብር በላይ ግዢ ላይ! ዛሬውኑ ይግዙ!', 'shipping', '#4CAF50', '/cart', 1, 2),
            ('✨ አዲስ የቤት እቃዎች ደርሰዋል! ዘመናዊ ዲዛይን፣ ምርጥ ጥራት!', 'new', '#2196F3', '/category/all', 1, 3),
            ('💝 የበዓል ልዩ ቅናሽ! ለቤተሰብዎ ምርጥ ስጦታ ከኤትዮሳዳት ጋር!', 'holiday', '#9C27B0', '/category/all', 1, 4),
            ('🛋️ ሶፋ ልዩ ቅናሽ! የምርጥ ሶፋዎች ዋጋ ከ20,000 ብር ጀምሮ!', 'product', '#FF9800', '/category/ሶፋ', 1, 5),
            ('📱 በዋትሳፕ በማዘዝ ተጨማሪ 5% ቅናሽ ያግኙ!', 'whatsapp', '#25D366', '/contact', 1, 6),
            ('⭐ የደንበኞች ምርጫ 2024! ኤትዮሳዳት ምርጥ የቤት እቃ አቅራቢ ተመርጧል!', 'award', '#FFC107', '/about', 1, 7),
            ('🔥 ፈጣን ሽያጭ! የተወሰኑ ምርቶች በ50% ቅናሽ! አያምልጥዎት!', 'flash_sale', '#FF4444', '/category/all', 1, 8),
            ('🎁 ለእያንዳንዱ ግዢ ነጻ ስጦታ! ውሱን ብዛት ብቻ!', 'gift', '#E91E63', '/cart', 1, 9),
            ('🏠 ሙሉ የቤት እቃ ስብስብ በልዩ ቅናሽ! አሁን ይግዙ!', 'bundle', '#009688', '/category/all', 1, 10),
        ]
        
        # Build insert query for ads
        insert_ad = "INSERT INTO ads (text"
        ad_placeholders = "?"
        ad_values_list = []
        
        if 'type' in ad_columns:
            insert_ad += ", type"
            ad_placeholders += ", ?"
        if 'color' in ad_columns:
            insert_ad += ", color"
            ad_placeholders += ", ?"
        if 'link' in ad_columns:
            insert_ad += ", link"
            ad_placeholders += ", ?"
        if 'is_active' in ad_columns:
            insert_ad += ", is_active"
            ad_placeholders += ", ?"
        if 'sort_order' in ad_columns:
            insert_ad += ", sort_order"
            ad_placeholders += ", ?"
        if 'created_at' in ad_columns:
            insert_ad += ", created_at"
            ad_placeholders += ", ?"
        
        insert_ad += f") VALUES ({ad_placeholders})"
        
        inserted_ads = 0
        for ad in ads:
            ad_values = [ad[0]]  # text
            
            if 'type' in ad_columns:
                ad_values.append(ad[1])
            if 'color' in ad_columns:
                ad_values.append(ad[2])
            if 'link' in ad_columns:
                ad_values.append(ad[3])
            if 'is_active' in ad_columns:
                ad_values.append(ad[4])
            if 'sort_order' in ad_columns:
                ad_values.append(ad[5])
            if 'created_at' in ad_columns:
                ad_values.append(datetime.now().isoformat())
            
            try:
                cursor.execute(insert_ad, tuple(ad_values))
                inserted_ads += 1
            except sqlite3.Error as e:
                print(f"   ⚠️  Could not insert ad: {e}")
        
        print(f"   ✅ Inserted {inserted_ads} advertisements")
        
        # ==================== SETTINGS ====================
        print("\n⚙️ Adding default settings...")
        
        if clear_existing:
            cursor.execute("DELETE FROM settings")
            print("   ✓ Cleared existing settings")
        
        settings = [
            ('site_name', 'Ethiosadat Furniture'),
            ('site_email', 'info@ethiosadat.com'),
            ('site_phone', '+251987957957'),
            ('whatsapp_number', '251987957957'),
            ('free_shipping_threshold', '5000'),
            ('shipping_cost', '200'),
            ('currency', 'ETB'),
            ('currency_symbol', 'ETB'),
            ('default_language', 'am'),
            ('products_per_page', '12'),
            ('admin_password_hint', '1234'),
            ('maintenance_mode', 'false'),
            ('last_seeded', datetime.now().isoformat()),
        ]
        
        insert_setting = "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)"
        
        for key, value in settings:
            if 'key' in settings_columns and 'value' in settings_columns:
                cursor.execute(insert_setting, (key, value))
        
        print(f"   ✅ Inserted {len(settings)} settings")
        
        # ==================== CHECK ORDERS TABLE ====================
        if not orders_exists:
            print("\n📋 Creating orders table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number TEXT UNIQUE,
                    customer_name TEXT NOT NULL,
                    customer_phone TEXT NOT NULL,
                    customer_address TEXT,
                    customer_email TEXT,
                    items TEXT,
                    subtotal REAL,
                    shipping_cost REAL,
                    total REAL,
                    status TEXT DEFAULT 'pending',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("   ✅ Orders table created")
        
        # ==================== CREATE UPLOAD DIRECTORIES ====================
        print("\n📁 Creating upload directories...")
        
        upload_dirs = [
            'static/uploads',
            'static/uploads/products',
            'static/uploads/ads',
            'logs'
        ]
        
        for directory in upload_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"   ✓ Created: {directory}")
            else:
                print(f"   ✓ Already exists: {directory}")
        
        # ==================== COMMIT CHANGES ====================
        conn.commit()
        
        # ==================== SUMMARY ====================
        cursor.execute("SELECT COUNT(*) FROM products")
        final_products = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ads")
        final_ads = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM settings")
        final_settings = cursor.fetchone()[0]
        
        # Get category distribution
        cursor.execute("""
            SELECT category, COUNT(*) FROM products 
            WHERE category IS NOT NULL 
            GROUP BY category 
            ORDER BY COUNT(*) DESC
        """)
        categories = cursor.fetchall()
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("📊 SEEDING SUMMARY")
        print("=" * 60)
        print(f"📦 Products: {final_products}")
        print(f"📢 Advertisements: {final_ads}")
        print(f"⚙️ Settings: {final_settings}")
        
        if categories:
            print("\n📁 Categories:")
            for cat, count in categories:
                print(f"   • {cat}: {count} products")
        
        print("=" * 60)
        print("\n✅ Database seeded successfully!")
        print("\n🔐 Admin Login:")
        print("   Password: 1234")
        print("\n🌐 Website:")
        print("   http://localhost:5000")
        print("\n📱 WhatsApp Number:")
        print("   251987957957")
        print("\n💡 Next Steps:")
        print("   1. Add product images to static/uploads/products/")
        print("   2. Customize settings in admin panel")
        print("   3. Start receiving orders!")
        print("=" * 60 + "\n")
        
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

def seed_products_only():
    """Seed only products data"""
    print("\n🌱 Seeding only products...")
    return seed_all(clear_existing=False)  # Keep existing ads and settings

def seed_ads_only():
    """Seed only advertisements"""
    print("\n🌱 Seeding only advertisements...")
    # This would need a modified version that only seeds ads
    pass

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed database for Ethiosadat Furniture Store')
    parser.add_argument('--keep', action='store_true', help='Keep existing data (don\'t clear)')
    parser.add_argument('--products-only', action='store_true', help='Seed only products')
    parser.add_argument('--verify', action='store_true', help='Verify database after seeding')
    
    args = parser.parse_args()
    
    if args.products_only:
        seed_products_only()
    else:
        seed_all(clear_existing=not args.keep)
    
    if args.verify:
        print("\n🔍 Verifying database...")
        # Import and run verification
        try:
            from check_data import check_data
            check_data()
        except ImportError:
            print("⚠️  Verification module not found")