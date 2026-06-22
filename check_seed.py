import sqlite3
import os
from config import Config

def check_data():
    """Check and display database status for Ethiosadat Furniture Store."""
    
    # Get database path from config or use default
    if hasattr(Config, 'DATABASE_PATH'):
        db_path = Config.DATABASE_PATH
    else:
        db_path = os.environ.get('DATABASE_PATH', 'ethiosadat.db')
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"\n❌ Database not found at: {db_path}")
        print("Please run the application first to initialize the database.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n" + "=" * 60)
        print("👗 ETHIOSADAT FASHION STORE - DATABASE STATUS")
        print("=" * 60)
        print(f"📁 Database Path: {db_path}")
        
        # ============================================================
        # PRODUCTS TABLE
        # ============================================================
        print("\n" + "─" * 60)
        
        # Check if products table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM products")
            products = cursor.fetchone()[0]
            print(f"\n📦 PRODUCTS: {products} total")
            
            if products > 0:
                cursor.execute("""
                    SELECT id, name_am, name_en, price, old_price, category, image 
                    FROM products 
                    ORDER BY id DESC 
                    LIMIT 5
                """)
                print("   ├─ Recent Products:")
                for i, p in enumerate(cursor.fetchall()):
                    prefix = "   └─" if i == 4 else "   ├─"
                    old_price_info = f" (was {p[4]} ETB)" if p[4] else ""
                    image_status = "✓" if p[6] else "✗"
                    print(f"{prefix} #{p[0]}: {p[1]} / {p[2]}")
                    print(f"      └─ Price: {p[3]} ETB{old_price_info} | Category: {p[5]} | Image: {image_status}")
                
                # Get min/max prices
                cursor.execute("SELECT MIN(CAST(price AS FLOAT)), MAX(CAST(price AS FLOAT)) FROM products WHERE price IS NOT NULL")
                min_price, max_price = cursor.fetchone()
                if min_price and max_price:
                    print(f"\n   💰 Price Range: {min_price:,.0f} ETB - {max_price:,.0f} ETB")
            else:
                print("\n   ℹ️  No products found. Add some from admin panel!")
        else:
            print("\n❌ Products table does not exist! Run initialization.")
        
        # ============================================================
        # CATEGORIES
        # ============================================================
        print("\n" + "─" * 60)
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM products 
                WHERE category IS NOT NULL AND category != ''
                GROUP BY category
                ORDER BY count DESC
            """)
            categories = cursor.fetchall()
            
            if categories:
                print(f"\n📁 CATEGORIES: {len(categories)}")
                for i, (cat, cnt) in enumerate(categories):
                    prefix = "└─" if i == len(categories) - 1 else "├─"
                    bar = "   " if i == len(categories) - 1 else "│  "
                    print(f"   {prefix} {cat}: {cnt} product{'s' if cnt > 1 else ''}")
                    
                    # Show top product in each category
                    cursor.execute("""
                        SELECT name_am, price FROM products 
                        WHERE category = ? 
                        ORDER BY id DESC LIMIT 1
                    """, (cat,))
                    top_product = cursor.fetchone()
                    if top_product:
                        print(f"   {bar}   └─ Latest: {top_product[0]} ({top_product[1]} ETB)")
            else:
                print("\n📁 CATEGORIES: 0")
                print("   ℹ️  No categories found. Add products with categories!")
        
        # ============================================================
        # ADVERTISEMENTS
        # ============================================================
        print("\n" + "─" * 60)
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ads'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM ads")
            ads = cursor.fetchone()[0]
            print(f"\n📢 ADVERTISEMENTS: {ads} total")
            
            if ads > 0:
                cursor.execute("""
                    SELECT id, text, media FROM ads 
                    ORDER BY id DESC 
                    LIMIT 3
                """)
                ads_list = cursor.fetchall()
                for i, ad in enumerate(ads_list):
                    prefix = "└─" if i == len(ads_list) - 1 else "├─"
                    text_preview = ad[1][:55] + "..." if len(ad[1]) > 55 else ad[1]
                    media_status = "📷 Has media" if ad[2] else "📝 Text only"
                    print(f"   {prefix} [{media_status}] {text_preview}")
            else:
                print("\n   ℹ️  No advertisements found. Add some from admin panel!")
        
        # ============================================================
        # ORDERS
        # ============================================================
        print("\n" + "─" * 60)
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM orders")
            orders = cursor.fetchone()[0]
            print(f"\n🛒 ORDERS: {orders} total")
            
            if orders > 0:
                # Order status breakdown
                cursor.execute("""
                    SELECT status, COUNT(*) FROM orders 
                    GROUP BY status
                    ORDER BY 
                        CASE status 
                            WHEN 'pending' THEN 1 
                            WHEN 'processing' THEN 2 
                            WHEN 'delivered' THEN 3 
                            WHEN 'cancelled' THEN 4 
                        END
                """)
                status_counts = cursor.fetchall()
                print("   Status Breakdown:")
                status_icons = {
                    'pending': '⏳',
                    'processing': '🔄',
                    'delivered': '✅',
                    'cancelled': '❌'
                }
                for status, count in status_counts:
                    icon = status_icons.get(status, '📋')
                    print(f"      {icon} {status.capitalize()}: {count}")
                
                # Recent orders
                cursor.execute("""
                    SELECT id, customer_name, total, status, created_at 
                    FROM orders 
                    ORDER BY id DESC 
                    LIMIT 3
                """)
                recent_orders = cursor.fetchall()
                print("\n   Recent Orders:")
                for i, order in enumerate(recent_orders):
                    prefix = "└─" if i == len(recent_orders) - 1 else "├─"
                    print(f"   {prefix} #{order[0]}: {order[1]} - {order[2]:,.0f} ETB [{order[3]}]")
                
                # Revenue calculations
                cursor.execute("SELECT SUM(total) FROM orders WHERE status = 'delivered'")
                revenue = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT SUM(total) FROM orders WHERE status = 'pending'")
                pending_revenue = cursor.fetchone()[0] or 0
                
                print(f"\n   💰 Total Revenue (Delivered): {revenue:,.0f} ETB")
                print(f"   ⏳ Pending Revenue: {pending_revenue:,.0f} ETB")
                
            else:
                print("\n   ℹ️  No orders yet. Customers will appear here!")
        else:
            print("\n📋 ORDERS: Table not created yet")
            print("   ℹ️  Will be created when first order is placed")
        
        # ============================================================
        # SETTINGS
        # ============================================================
        print("\n" + "─" * 60)
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM settings")
            settings_count = cursor.fetchone()[0]
            print(f"\n⚙️  SETTINGS: {settings_count} configured")
            
            if settings_count > 0:
                cursor.execute("SELECT key, value FROM settings LIMIT 5")
                settings = cursor.fetchall()
                print("   Active Settings:")
                for key, value in settings:
                    display_value = value[:40] + "..." if len(value) > 40 else value
                    print(f"      • {key}: {display_value}")
        
        # ============================================================
        # STORAGE INFO
        # ============================================================
        print("\n" + "─" * 60)
        print("\n💾 STORAGE INFORMATION")
        
        # Check upload directories
        upload_folders = ['static/uploads', 'static/uploads/products', 'static/uploads/ads']
        for folder in upload_folders:
            if os.path.exists(folder):
                file_count = len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
                size = sum(os.path.getsize(os.path.join(folder, f)) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)))
                size_kb = size / 1024
                print(f"   📁 {folder}: {file_count} files ({size_kb:.1f} KB)")
            else:
                print(f"   ❌ {folder}: Not found")
        
        # Database file size
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path) / 1024
            print(f"\n   🗄️  Database size: {db_size:.2f} KB")
        
        # ============================================================
        # SUMMARY
        # ============================================================
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        
        # Get final counts
        cursor.execute("SELECT COUNT(*) FROM products")
        final_products = cursor.fetchone()[0] if cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'").fetchone() else 0
        
        cursor.execute("SELECT COUNT(*) FROM ads")
        final_ads = cursor.fetchone()[0] if cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ads'").fetchone() else 0
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        final_orders = cursor.fetchone()[0] if cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'").fetchone() else 0
        
        print(f"📦 Total Products: {final_products}")
        print(f"📢 Total Ads: {final_ads}")
        print(f"🛒 Total Orders: {final_orders}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if final_products == 0:
            print("   ⚠️  Add products from admin panel (/admin/products/add)")
        elif final_products < 5:
            print("   💡 Add more products to attract customers")
        
        if final_ads == 0:
            print("   💡 Create advertisements to promote products")
        
        if final_orders == 0:
            print("   💡 Share your store link to start receiving orders!")
        
        print("\n" + "=" * 60)
        print("✅ Database check completed!")
        print("=" * 60 + "\n")
        
        conn.close()
        
    except sqlite3.OperationalError as e:
        print(f"\n❌ Database Error: {e}")
        print("Please ensure the database is properly initialized.")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

def fix_database():
    """Attempt to fix common database issues."""
    print("\n🔧 Attempting to fix database issues...")
    
    db_path = Config.DATABASE_PATH if hasattr(Config, 'DATABASE_PATH') else 'ethiosadat.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check and create missing tables
        tables = ['products', 'ads', 'orders', 'settings']
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                if table == 'products':
                    cursor.execute('''
                        CREATE TABLE products (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name_am TEXT NOT NULL,
                            name_en TEXT NOT NULL,
                            price TEXT NOT NULL,
                            old_price TEXT,
                            image TEXT,
                            category TEXT
                        )
                    ''')
                    print(f"   ✓ Created '{table}' table")
                elif table == 'ads':
                    cursor.execute('''
                        CREATE TABLE ads (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            text TEXT NOT NULL,
                            media TEXT
                        )
                    ''')
                    print(f"   ✓ Created '{table}' table")
                elif table == 'orders':
                    cursor.execute('''
                        CREATE TABLE orders (
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
                    print(f"   ✓ Created '{table}' table")
                elif table == 'settings':
                    cursor.execute('''
                        CREATE TABLE settings (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            key TEXT UNIQUE NOT NULL,
                            value TEXT
                        )
                    ''')
                    print(f"   ✓ Created '{table}' table")
        
        conn.commit()
        conn.close()
        
        print("✅ Database fix completed!")
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--fix':
        fix_database()
    
    check_data()