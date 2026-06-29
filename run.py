#!/usr/bin/env python3
"""
SEMIRA FASHION - Application Runner
This script provides a unified entry point for running the application
with various command-line options and environment configurations.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from the project .env file.
ENV_FILE = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=ENV_FILE, override=False)

def print_banner():
    """Display application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        👗  SEMIRA FASHION  👗                            ║
    ║                                                          ║
    ║        የሴቶች እና የልጆች ልብስ መሸጫ                          ║
    ║        Women's & Children's Fashion Store               ║
    ║                                                          ║
    ║                   Version 1.0.0                         ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = []
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        print(f"⚠️  Warning: Missing optional environment variables: {', '.join(missing)}")
        print("   Using default values.\n")
    
    # Create .env file if it doesn't exist
    env_file = Path('.env')
    if not env_file.exists():
        print("📝 Creating default .env file...")
        with open(env_file, 'w') as f:
            f.write("""# SEMIRA FASHION Environment Configuration
FLASK_ENV=development
SECRET_KEY=semirafashion_default_secret_key_2026
ADMIN_PASSWORD=1234
WHATSAPP_NUMBER=251987957957
DEBUG=True
HOST=0.0.0.0
PORT=5000
FREE_SHIPPING_THRESHOLD=5000
SHIPPING_COST=200
MAINTENANCE_MODE=False
""")
        print("✅ .env file created successfully!\n")

def check_database():
    """Check PostgreSQL database connectivity and required tables."""
    try:
        import psycopg2
        import psycopg2.extras
        db_url = os.environ.get('DATABASE_URL', '')
        if not db_url:
            print("⚠️  DATABASE_URL not set — cannot check database.")
            return False
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'products'
            )
        """)
        exists = cursor.fetchone()[0]
        conn.close()
        if not exists:
            print("⚠️  Products table missing. Run --init-db first.")
            return False
        return True
    except Exception as e:
        print(f"⚠️  Database check failed: {e}")
        return False

def init_database():
    """Initialize the database"""
    print("\n📦 Initializing database...")
    try:
        from database.db import init_db
        init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    return True

def seed_database(args):
    """Seed the database with sample data"""
    print("\n🌱 Seeding database...")
    
    if args.products_only:
        try:
            from seed_products import seed_products
            seed_products(clear_existing=not args.append, add_images=args.images)
        except ImportError:
            print("❌ Could not import seed_products module")
            return False
    elif args.ads_only:
        try:
            from seed_ads import seed_ads
            seed_ads(with_media=args.images)
        except ImportError:
            print("❌ Could not import seed_ads module")
            return False
    else:
        try:
            from seed_all import seed_all
            seed_all(clear_existing=not args.append)
        except ImportError:
            print("❌ Could not import seed_all module")
            return False
    
    return True

def clear_database(args):
    """Clear data from database"""
    print("\n🗑️  Clearing database...")
    
    if args.products:
        try:
            from seed_products import clear_products
            clear_products()
        except ImportError:
            print("❌ Could not import seed_products module")
            return False
    elif args.ads:
        try:
            # Import clear_ads from seed_ads (create if needed)
            from seed_ads import clear_ads
            clear_ads()
        except ImportError:
            print("❌ Could not import seed_ads module")
            return False
    elif args.orders:
        try:
            import psycopg2
            db_url = os.environ.get('DATABASE_URL', '')
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM order_items")
            cursor.execute("DELETE FROM orders")
            conn.commit()
            conn.close()
            print("✅ Orders cleared.")
        except Exception as e:
            print(f"❌ Could not clear orders: {e}")
            return False
    else:
        response = input("⚠️  Clear ALL data? (yes/no): ")
        if response.lower() == 'yes':
            try:
                import psycopg2
                db_url = os.environ.get('DATABASE_URL', '')
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()
                for table in ['order_items', 'orders', 'cart_items', 'ads', 'products', 'settings']:
                    cursor.execute(f"DELETE FROM {table}")
                conn.commit()
                conn.close()
                print("✅ All data cleared.")
            except Exception as e:
                print(f"❌ Could not clear data: {e}")
                return False
        else:
            print("❌ Cancelled.")
            return False
    
    return True

def run_development():
    """Run the application in development mode"""
    print("\n🚀 Starting development server...")
    print("   Press CTRL+C to stop\n")
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['DEBUG'] = 'True'
    
    try:
        from app import app
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('DEBUG', 'True').lower() == 'true'
        
        print(f"🌐 Server running at: http://localhost:{port}")
        print(f"🔐 Admin login: http://localhost:{port}/login")
        print(f"📱 WhatsApp: {os.environ.get('WHATSAPP_NUMBER', '251987957957')}")
        print("\n" + "=" * 60)
        
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

def run_production():
    """Run the application in production mode using gunicorn"""
    print("\n🚀 Starting production server with Gunicorn...")
    
    # Check if gunicorn is installed
    try:
        import gunicorn
    except ImportError:
        print("❌ Gunicorn not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gunicorn"])
    
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))
    workers = int(os.environ.get('WORKERS', 4))
    
    cmd = [
        sys.executable, "-m", "gunicorn",
        "--bind", f"{host}:{port}",
        "--workers", str(workers),
        "--timeout", "120",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "app:app"
    ]
    
    print(f"🌐 Server running at: http://{host}:{port}")
    print(f"🔧 Workers: {workers}")
    print("\n" + "=" * 60)
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

def check_database_status():
    """Check and display database status"""
    print("\n📊 Checking database status...")
    try:
        from check_data import check_data
        check_data()
    except ImportError:
        print("⚠️  check_data module not found")
        return False
    return True

def backup_database():
    """Create a backup of the database"""
    print("\n💾 Creating database backup...")
    try:
        from clear_data import backup_before_clear
        backup_path = backup_before_clear()
        if backup_path:
            print(f"✅ Backup created: {backup_path}")
        else:
            print("❌ Backup failed")
            return False
    except ImportError:
        print("⚠️  backup function not found")
        return False
    return True

def show_info():
    """Display application information"""
    print("\n📋 Application Information")
    print("=" * 60)
    
    # Load config
    try:
        from config import Config
        print(f"📁 Database Path: {Config.DATABASE_PATH}")
        print(f"📁 Upload Folder: {Config.UPLOAD_FOLDER}")
        print(f"🌐 Default Language: {Config.DEFAULT_LANGUAGE}")
        print(f"📱 WhatsApp Number: {Config.WHATSAPP_NUMBER}")
    except ImportError:
        print("⚠️  Could not load configuration")
    
    # Check file sizes
    db_path = 'ethiosadat.db'
    if os.path.exists(db_path):
        size = os.path.getsize(db_path) / 1024
        print(f"💾 Database Size: {size:.2f} KB")
    
    # Check upload folder
    upload_folder = 'static/uploads'
    if os.path.exists(upload_folder):
        file_count = sum(1 for _ in Path(upload_folder).rglob('*') if _.is_file())
        print(f"📁 Uploaded Files: {file_count}")
    
    print("=" * 60)

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    requirements = [
        'flask',
        'werkzeug',
        'python-dotenv',
        'pillow',  # For image processing
    ]
    
    for package in requirements:
        print(f"   Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except Exception as e:
            print(f"   ⚠️  Failed to install {package}: {e}")
    
    print("✅ Dependencies installed successfully!")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Ethiosadat Furniture Store - Application Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run in development mode
  %(prog)s --production       # Run in production mode
  %(prog)s --init-db          # Initialize database
  %(prog)s --seed             # Seed with sample data
  %(prog)s --seed --products-only  # Seed only products
  %(prog)s --check-db         # Check database status
  %(prog)s --backup           # Backup database
  %(prog)s --info             # Show application info
  %(prog)s --install-deps     # Install dependencies
        """
    )
    
    # Run options
    parser.add_argument('--production', action='store_true', help='Run in production mode')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, help='Port to bind to')
    
    # Database options
    parser.add_argument('--init-db', action='store_true', help='Initialize database')
    parser.add_argument('--seed', action='store_true', help='Seed database with sample data')
    parser.add_argument('--check-db', action='store_true', help='Check database status')
    parser.add_argument('--backup', action='store_true', help='Backup database')
    parser.add_argument('--clear', action='store_true', help='Clear database data')
    
    # Seed options
    parser.add_argument('--products-only', action='store_true', help='Seed only products')
    parser.add_argument('--ads-only', action='store_true', help='Seed only advertisements')
    parser.add_argument('--append', action='store_true', help='Append data without clearing')
    parser.add_argument('--images', action='store_true', help='Include image references')
    
    # Clear options
    parser.add_argument('--clear-products', action='store_true', help='Clear only products')
    parser.add_argument('--clear-ads', action='store_true', help='Clear only ads')
    parser.add_argument('--clear-orders', action='store_true', help='Clear only orders')
    
    # Utility options
    parser.add_argument('--info', action='store_true', help='Show application information')
    parser.add_argument('--install-deps', action='store_true', help='Install dependencies')
    parser.add_argument('--no-banner', action='store_true', help='Hide banner')
    
    args = parser.parse_args()
    
    # Print banner
    if not args.no_banner:
        print_banner()
    
    # Check environment
    check_environment()
    
    # Handle utility commands first
    if args.install_deps:
        install_dependencies()
        return
    
    if args.info:
        show_info()
        return
    
    # Handle database operations
    if args.init_db:
        init_database()
        return
    
    if args.check_db:
        check_database_status()
        return
    
    if args.backup:
        backup_database()
        return
    
    if args.clear or args.clear_products or args.clear_ads or args.clear_orders:
        clear_database(args)
        return
    
    if args.seed:
        # Check database first
        if not check_database():
            init_database()
        seed_database(args)
        return
    
    # Set host/port from command line if provided
    if args.host:
        os.environ['HOST'] = args.host
    if args.port:
        os.environ['PORT'] = str(args.port)
    
    # Check if database exists
    if not check_database():
        print("\n📦 Database not ready. Initializing...")
        if init_database():
            response = input("\n🌱 Would you like to seed sample data? (yes/no): ")
            if response.lower() == 'yes':
                seed_database(args)
    
    # Run the application
    if args.production:
        run_production()
    else:
        run_development()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Ethiosadat application stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)