import sqlite3
import os
import sys
from datetime import datetime
from config import Config

def clear_all_data(confirm=True):
    """Clear all seeded data from database with proper safety checks"""
    
    # Get database path from config or use default
    if hasattr(Config, 'DATABASE_PATH'):
        db_path = Config.DATABASE_PATH
    else:
        db_path = os.environ.get('DATABASE_PATH', 'semirafashion.db')
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get counts before deletion
        cursor.execute("SELECT COUNT(*) FROM products")
        products_count = cursor.fetchone()[0] if table_exists(cursor, 'products') else 0
        
        cursor.execute("SELECT COUNT(*) FROM ads")
        ads_count = cursor.fetchone()[0] if table_exists(cursor, 'ads') else 0
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        orders_count = cursor.fetchone()[0] if table_exists(cursor, 'orders') else 0
        
        if products_count == 0 and ads_count == 0 and orders_count == 0:
            print("📭 Database is already empty. No data to clear.")
            conn.close()
            return True
        
        # Show summary of what will be deleted
        print("\n" + "=" * 60)
        print("⚠️  DATABASE CLEAR WARNING")
        print("=" * 60)
        print(f"📦 Products to delete: {products_count}")
        print(f"📢 Ads to delete: {ads_count}")
        print(f"🛒 Orders to delete: {orders_count}")
        print("=" * 60)
        
        if confirm:
            response = input("\n⚠️  Are you sure you want to clear ALL data? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled.")
                conn.close()
                return False
        
        print("\n🔄 Clearing data...")
        
        # Delete data from tables
        if table_exists(cursor, 'products'):
            cursor.execute("DELETE FROM products")
            print(f"   ✓ Deleted {products_count} products")
        
        if table_exists(cursor, 'ads'):
            cursor.execute("DELETE FROM ads")
            print(f"   ✓ Deleted {ads_count} ads")
        
        if table_exists(cursor, 'orders'):
            cursor.execute("DELETE FROM orders")
            print(f"   ✓ Deleted {orders_count} orders")
        
        # Reset auto-increment counters
        if table_exists(cursor, 'products'):
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='products'")
        if table_exists(cursor, 'ads'):
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='ads'")
        if table_exists(cursor, 'orders'):
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='orders'")
        
        conn.commit()
        
        # Verify deletion
        new_products = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0] if table_exists(cursor, 'products') else 0
        new_ads = cursor.execute("SELECT COUNT(*) FROM ads").fetchone()[0] if table_exists(cursor, 'ads') else 0
        new_orders = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0] if table_exists(cursor, 'orders') else 0
        
        conn.close()
        
        if new_products == 0 and new_ads == 0 and new_orders == 0:
            print("\n✅ All data cleared successfully!")
            print(f"   📦 Products: {new_products}")
            print(f"   📢 Ads: {new_ads}")
            print(f"   🛒 Orders: {new_orders}")
            return True
        else:
            print("\n⚠️  Some data could not be cleared:")
            print(f"   📦 Products remaining: {new_products}")
            print(f"   📢 Ads remaining: {new_ads}")
            print(f"   🛒 Orders remaining: {new_orders}")
            return False
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def table_exists(cursor, table_name):
    """Check if a table exists in the database"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def clear_products_only():
    """Clear only products data"""
    db_path = Config.DATABASE_PATH if hasattr(Config, 'DATABASE_PATH') else 'semirafashion.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0] if table_exists(cursor, 'products') else 0
        
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

def clear_ads_only():
    """Clear only advertisements data"""
    db_path = Config.DATABASE_PATH if hasattr(Config, 'DATABASE_PATH') else 'semirafashion.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM ads")
        count = cursor.fetchone()[0] if table_exists(cursor, 'ads') else 0
        
        if count == 0:
            print("📭 No ads to clear.")
            conn.close()
            return
        
        response = input(f"⚠️  Delete {count} advertisements? (yes/no): ")
        if response.lower() == 'yes':
            cursor.execute("DELETE FROM ads")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='ads'")
            conn.commit()
            print(f"✅ Deleted {count} ads!")
        else:
            print("❌ Cancelled.")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

def clear_orders_only():
    """Clear only orders data"""
    db_path = Config.DATABASE_PATH if hasattr(Config, 'DATABASE_PATH') else 'semirafashion.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0] if table_exists(cursor, 'orders') else 0
        
        if count == 0:
            print("📭 No orders to clear.")
            conn.close()
            return
        
        response = input(f"⚠️  Delete {count} orders? (yes/no): ")
        if response.lower() == 'yes':
            cursor.execute("DELETE FROM orders")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='orders'")
            conn.commit()
            print(f"✅ Deleted {count} orders!")
        else:
            print("❌ Cancelled.")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

def clear_and_seed_demo():
    """Clear all data and seed with fresh demo data"""
    print("\n🔄 Clearing and seeding demo data...")
    
    if clear_all_data(confirm=True):
        print("\n🌱 Seeding new demo data...")
        
        # Import seed data function
        try:
            # Try to run seed command
            import subprocess
            result = subprocess.run([sys.executable, 'app.py', 'seed'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Demo data seeded successfully!")
            else:
                print("⚠️  Could not auto-seed. Please run: python app.py seed")
        except:
            print("⚠️  Please run seeding manually: python app.py seed")
    else:
        print("❌ Failed to clear data.")

def backup_before_clear():
    """Create backup before clearing data"""
    from datetime import datetime
    
    db_path = Config.DATABASE_PATH if hasattr(Config, 'DATABASE_PATH') else 'semirafashion.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return False
    
    # Create backup directory
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'backup_before_clear_{timestamp}.db')
    
    # Copy database
    import shutil
    shutil.copy2(db_path, backup_path)
    
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def show_menu():
    """Show interactive menu for data management"""
    print("\n" + "=" * 50)
    print("🗄️  DATABASE MANAGEMENT TOOL")
    print("=" * 50)
    print("1. Clear ALL data (products, ads, orders)")
    print("2. Clear products only")
    print("3. Clear advertisements only")
    print("4. Clear orders only")
    print("5. Clear and seed fresh demo data")
    print("6. Create backup before clearing")
    print("7. View current data counts")
    print("0. Exit")
    print("=" * 50)
    
    choice = input("\nSelect option (0-7): ").strip()
    
    if choice == '1':
        print("\n⚠️  WARNING: This will delete ALL data!")
        backup_choice = input("Create backup before clearing? (yes/no): ")
        if backup_choice.lower() == 'yes':
            backup_before_clear()
        clear_all_data(confirm=True)
    
    elif choice == '2':
        clear_products_only()
    
    elif choice == '3':
        clear_ads_only()
    
    elif choice == '4':
        clear_orders_only()
    
    elif choice == '5':
        clear_and_seed_demo()
    
    elif choice == '6':
        backup_before_clear()
    
    elif choice == '7':
        view_counts()
    
    elif choice == '0':
        print("👋 Goodbye!")
        return False
    
    else:
        print("❌ Invalid option")
    
    return True

def view_counts():
    """View current data counts without modifying anything"""
    db_path = Config.DATABASE_PATH if hasattr(Config, 'DATABASE_PATH') else 'semirafashion.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 CURRENT DATABASE COUNTS")
        print("-" * 30)
        
        if table_exists(cursor, 'products'):
            count = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            print(f"📦 Products: {count}")
        else:
            print("📦 Products: 0 (table not found)")
        
        if table_exists(cursor, 'ads'):
            count = cursor.execute("SELECT COUNT(*) FROM ads").fetchone()[0]
            print(f"📢 Ads: {count}")
        else:
            print("📢 Ads: 0 (table not found)")
        
        if table_exists(cursor, 'orders'):
            count = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            print(f"🛒 Orders: {count}")
        else:
            print("🛒 Orders: 0 (table not found)")
        
        conn.close()
        print("-" * 30)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import argparse
    
    # Command line argument parsing
    parser = argparse.ArgumentParser(description='Database management tool for SEMIRA FASHION')
    parser.add_argument('--all', action='store_true', help='Clear all data')
    parser.add_argument('--products', action='store_true', help='Clear only products')
    parser.add_argument('--ads', action='store_true', help='Clear only ads')
    parser.add_argument('--orders', action='store_true', help='Clear only orders')
    parser.add_argument('--reset', action='store_true', help='Clear and seed demo data')
    parser.add_argument('--backup', action='store_true', help='Create backup only')
    parser.add_argument('--counts', action='store_true', help='Show current counts')
    parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    args = parser.parse_args()
    
    # Process command line arguments
    if args.all:
        if args.force or input("⚠️  Clear ALL data? (yes/no): ").lower() == 'yes':
            clear_all_data(confirm=not args.force)
        else:
            print("Cancelled.")
    
    elif args.products:
        clear_products_only()
    
    elif args.ads:
        clear_ads_only()
    
    elif args.orders:
        clear_orders_only()
    
    elif args.reset:
        clear_and_seed_demo()
    
    elif args.backup:
        backup_before_clear()
    
    elif args.counts:
        view_counts()
    
    else:
        # Interactive menu
        while show_menu():
            pass