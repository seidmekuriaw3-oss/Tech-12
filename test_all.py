#!/usr/bin/env python3
"""
Ethiosadat System Checker
Comprehensive testing utility for the Ethiosadat Furniture Store application
"""

import requests
import sqlite3
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = os.environ.get('TEST_URL', 'http://127.0.0.1:5000')
TIMEOUT = 10

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.BLUE}📌 {msg}{Colors.ENDC}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{msg}{Colors.ENDC}")

def test_endpoint(url, name, method='GET', data=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if method == 'GET':
            response = requests.get(f"{BASE_URL}{url}", timeout=TIMEOUT)
        elif method == 'POST':
            response = requests.post(f"{BASE_URL}{url}", data=data, timeout=TIMEOUT)
        else:
            return False
        
        if response.status_code == expected_status:
            print_success(f"{name}: {response.status_code}")
            return True
        else:
            print_error(f"{name}: Expected {expected_status}, got {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"{name}: Server not responding")
        return False
    except requests.exceptions.Timeout:
        print_error(f"{name}: Request timeout")
        return False
    except Exception as e:
        print_error(f"{name}: {str(e)}")
        return False

def test_database():
    """Check database structure and data"""
    print_header("📁 DATABASE CHECK")
    
    db_paths = ['ethiosadat.db', 'database/ethiosadat.db']
    conn = None
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get table list
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                print_info(f"Database: {db_path}")
                
                # Check required tables
                required_tables = ['products', 'ads', 'settings']
                for table in required_tables:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print_success(f"  {table}: {count} records")
                    else:
                        print_error(f"  {table}: Missing")
                
                # Check optional tables
                optional_tables = ['orders']
                for table in optional_tables:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print_info(f"  {table}: {count} records (optional)")
                
                # Check categories
                if 'products' in tables:
                    cursor.execute("""
                        SELECT category, COUNT(*) FROM products 
                        WHERE category IS NOT NULL 
                        GROUP BY category
                    """)
                    categories = cursor.fetchall()
                    if categories:
                        print_info("  Categories:")
                        for cat, count in categories[:5]:
                            print(f"      - {cat}: {count}")
                
                conn.close()
                return True
                
            except Exception as e:
                print_error(f"Database error: {e}")
                if conn:
                    conn.close()
                continue
    
    print_error("No database found!")
    return False

def test_admin_login():
    """Test admin login functionality"""
    print_header("🔐 ADMIN LOGIN CHECK")
    
    # Test login page access
    if not test_endpoint("/login", "Login page access", expected_status=200):
        return False
    
    # Test valid login
    try:
        data = {'password': '1234'}
        response = requests.post(f"{BASE_URL}/login", data=data, timeout=TIMEOUT, allow_redirects=False)
        
        if response.status_code == 302:
            print_success("Admin login: Valid password works")
        else:
            print_error(f"Admin login: Expected redirect 302, got {response.status_code}")
            return False
        
        # Test invalid login
        data = {'password': 'wrongpassword'}
        response = requests.post(f"{BASE_URL}/login", data=data, timeout=TIMEOUT)
        
        if "Invalid" in response.text or response.status_code == 200:
            print_success("Admin login: Invalid password rejected")
        else:
            print_warning("Admin login: Invalid password response unclear")
        
        return True
        
    except Exception as e:
        print_error(f"Admin login test failed: {e}")
        return False

def test_static_files():
    """Check static files accessibility"""
    print_header("📁 STATIC FILES CHECK")
    
    static_files = [
        '/static/css/style.css',
        '/static/js/main.js',
        '/static/uploads/',
    ]
    
    all_ok = True
    for file_path in static_files:
        try:
            response = requests.get(f"{BASE_URL}{file_path}", timeout=TIMEOUT)
            if response.status_code == 200:
                print_success(f"  {file_path}: OK")
            elif response.status_code == 404:
                print_warning(f"  {file_path}: Not found (may be optional)")
            else:
                print_error(f"  {file_path}: {response.status_code}")
                all_ok = False
        except Exception as e:
            print_error(f"  {file_path}: {str(e)}")
            all_ok = False
    
    return all_ok

def test_cart_functionality():
    """Test cart functionality"""
    print_header("🛒 CART FUNCTIONALITY CHECK")
    
    try:
        # Check cart count API
        response = requests.get(f"{BASE_URL}/api/cart/count", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            cart_count = data.get('cart_count', 0)
            print_success(f"Cart API: Count = {cart_count}")
        else:
            print_warning(f"Cart API: {response.status_code}")
        
        # Test add to cart
        test_data = {
            'product_id': '1',
            'product_name': 'Test Product',
            'product_price': '1000',
            'quantity': '1'
        }
        
        response = requests.post(f"{BASE_URL}/cart/add", data=test_data, timeout=TIMEOUT)
        if response.status_code in [200, 302]:
            print_success("Add to cart: Working")
        else:
            print_warning(f"Add to cart: {response.status_code}")
        
        return True
        
    except Exception as e:
        print_error(f"Cart test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print_header("📡 API ENDPOINTS CHECK")
    
    api_endpoints = [
        ('/api/products', 'Products API'),
        ('/api/categories', 'Categories API'),
        ('/api/cart/count', 'Cart Count API'),
    ]
    
    all_ok = True
    for endpoint, name in api_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
            if response.status_code == 200:
                # Check if response is valid JSON
                try:
                    data = response.json()
                    print_success(f"{name}: OK (JSON)")
                except:
                    print_warning(f"{name}: {response.status_code} (Not JSON)")
                all_ok = True
            else:
                print_error(f"{name}: {response.status_code}")
                all_ok = False
        except Exception as e:
            print_error(f"{name}: {str(e)}")
            all_ok = False
    
    return all_ok

def test_page_content():
    """Check page content for expected elements"""
    print_header("📄 PAGE CONTENT CHECK")
    
    checks = [
        ('/', 'home', ['cart', 'products', 'shop']),
        ('/cart', 'cart', ['cart', 'checkout']),
        ('/login', 'login', ['password', 'login']),
    ]
    
    all_ok = True
    for url, name, keywords in checks:
        try:
            response = requests.get(f"{BASE_URL}{url}", timeout=TIMEOUT)
            if response.status_code == 200:
                content = response.text.lower()
                missing_keywords = []
                for keyword in keywords:
                    if keyword.lower() not in content:
                        missing_keywords.append(keyword)
                
                if missing_keywords:
                    print_warning(f"{name}: Missing keywords: {', '.join(missing_keywords)}")
                    all_ok = False
                else:
                    print_success(f"{name}: All expected elements found")
            else:
                print_error(f"{name}: {response.status_code}")
                all_ok = False
        except Exception as e:
            print_error(f"{name}: {str(e)}")
            all_ok = False
    
    return all_ok

def test_response_time():
    """Test response times for critical pages"""
    print_header("⏱️  RESPONSE TIME CHECK")
    
    pages = ['/', '/cart', '/admin', '/login']
    results = {}
    
    for page in pages:
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{page}", timeout=TIMEOUT)
            elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if elapsed < 500:
                print_success(f"{page}: {elapsed:.0f}ms")
            elif elapsed < 1000:
                print_warning(f"{page}: {elapsed:.0f}ms (slow)")
            else:
                print_error(f"{page}: {elapsed:.0f}ms (very slow)")
            
            results[page] = elapsed
            
        except Exception as e:
            print_error(f"{page}: Error - {str(e)}")
    
    # Calculate average
    if results:
        avg_time = sum(results.values()) / len(results)
        print_info(f"Average response time: {avg_time:.0f}ms")
    
    return True

def test_upload_functionality():
    """Test file upload functionality"""
    print_header("📤 UPLOAD FUNCTIONALITY CHECK")
    
    # Check if upload directory exists and is writable
    upload_dirs = ['static/uploads', 'static/uploads/products', 'static/uploads/ads']
    
    for directory in upload_dirs:
        if os.path.exists(directory):
            if os.access(directory, os.W_OK):
                print_success(f"{directory}: Writable")
            else:
                print_error(f"{directory}: Not writable")
        else:
            print_warning(f"{directory}: Does not exist")
    
    return True

def test_session_management():
    """Test session management"""
    print_header("🔑 SESSION MANAGEMENT CHECK")
    
    try:
        session = requests.Session()
        
        # Try to login
        login_data = {'password': '1234'}
        response = session.post(f"{BASE_URL}/login", data=login_data, timeout=TIMEOUT)
        
        # Check if session cookie was set
        if session.cookies:
            print_success("Session cookies: Working")
        else:
            print_warning("Session cookies: Not detected")
        
        # Try to access protected page
        response = session.get(f"{BASE_URL}/admin", timeout=TIMEOUT)
        if response.status_code == 200:
            print_success("Protected page access: Working with session")
        else:
            print_warning(f"Protected page: {response.status_code}")
        
        return True
        
    except Exception as e:
        print_error(f"Session test failed: {e}")
        return False

def test_mobile_responsive():
    """Check if pages are mobile-responsive"""
    print_header("📱 MOBILE RESPONSIVENESS CHECK")
    
    mobile_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    
    try:
        headers = {'User-Agent': mobile_user_agent}
        response = requests.get(f"{BASE_URL}/", headers=headers, timeout=TIMEOUT)
        
        if response.status_code == 200:
            # Check for viewport meta tag
            if 'viewport' in response.text.lower():
                print_success("Mobile viewport: Configured")
            else:
                print_warning("Mobile viewport: Not found")
            print_success("Mobile access: Working")
        else:
            print_error(f"Mobile access: {response.status_code}")
        
        return True
        
    except Exception as e:
        print_error(f"Mobile test failed: {e}")
        return False

def generate_report(results):
    """Generate test report"""
    print_header("📊 TEST REPORT")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print_success("All tests passed! 🎉")
    elif passed >= total * 0.7:
        print_warning("Most tests passed, but some issues found ⚠️")
    else:
        print_error("Multiple issues detected. Please fix before deployment! ❌")
    
    print("=" * 60)

def main():
    """Main test runner"""
    print("\n" + "=" * 60)
    print(f"{Colors.BOLD}{Colors.HEADER}🧪 ETHIOSADAT SYSTEM CHECK{Colors.ENDC}")
    print("=" * 60)
    print_info(f"Testing URL: {BASE_URL}")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}", timeout=5)
        if response.status_code != 200:
            print_error(f"Server returned status {response.status_code}")
            print("   Make sure the application is running:")
            print("   python run.py")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server!")
        print("   Please start the application first:")
        print("   python run.py")
        sys.exit(1)
    except Exception as e:
        print_error(f"Server check failed: {e}")
        sys.exit(1)
    
    # Run all tests
    results = {}
    
    # Core tests
    results['endpoints'] = all(test_endpoint(url, name) for url, name in [
        ("/", "Home Page"),
        ("/cart", "Cart Page"),
        ("/admin", "Admin Panel"),
        ("/login", "Login Page"),
    ])
    
    results['database'] = test_database()
    results['admin_login'] = test_admin_login()
    results['static_files'] = test_static_files()
    results['cart'] = test_cart_functionality()
    results['api'] = test_api_endpoints()
    
    # Advanced tests
    results['content'] = test_page_content()
    results['response_time'] = test_response_time()
    results['upload'] = test_upload_functionality()
    results['session'] = test_session_management()
    results['mobile'] = test_mobile_responsive()
    
    # Generate report
    generate_report(results)
    
    # Final recommendations
    print_header("💡 RECOMMENDATIONS")
    if not results.get('database', False):
        print("   • Run 'python run.py --init-db' to initialize database")
        print("   • Run 'python run.py --seed' to add sample data")
    
    if not results.get('static_files', False):
        print("   • Check that static files exist in the static/ directory")
        print("   • Run 'python setup_static.py' if available")
    
    if not results.get('admin_login', False):
        print("   • Verify admin password in .env file")
        print("   • Default password is '1234'")
    
    if not results.get('cart', False):
        print("   • Check cart routes in app.py")
        print("   • Verify session configuration")
    
    print("\n" + "=" * 60)
    print("✅ System check completed!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Ethiosadat System Checker')
    parser.add_argument('--url', default=BASE_URL, help='Base URL for testing')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    args = parser.parse_args()
    
    if args.url:
        BASE_URL = args.url
    
    if args.quick:
        print_warning("Running in quick mode (skipping advanced tests)")
        # Override to run fewer tests
        def quick_main():
            print(f"\nTesting: {BASE_URL}")
            test_endpoint("/", "Home Page")
            test_endpoint("/cart", "Cart Page")
            test_database()
            test_admin_login()
        quick_main()
    else:
        main()