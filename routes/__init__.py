"""
Routes Package for SEMIRA FASHION

This package contains all route modules for the application:
- customer_routes: Public-facing routes (home, products, cart, checkout, branches, etc.)
- admin_routes: Admin panel routes (dashboard, products, orders, ads, etc.)
- api_routes: API endpoints for AJAX requests
- cart_routes: Cart management routes (add, remove, update, etc.)
"""

import logging as _log
from flask import Blueprint

# ==================== BLUEPRINT REGISTRATION ====================

def register_routes(app):
    """
    Register all route blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    # Import route modules
    from routes.customer_routes import customer_bp
    from routes.admin_routes import admin_bp
    from routes.api_routes import api_bp
    from routes.cart_routes import cart_bp
    from routes.utility_routes import utility_bp
    from routes.islamic_routes import islamic_bp
    from routes.ai_routes import ai_bp

    # Register blueprints with URL prefixes
    app.register_blueprint(customer_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(utility_bp, url_prefix='/')
    app.register_blueprint(islamic_bp, url_prefix='/')
    app.register_blueprint(ai_bp, url_prefix='/api')

    _log.getLogger(__name__).warning("✅ All routes registered successfully")
    _log.getLogger(__name__).warning("   - Customer routes: /")
    _log.getLogger(__name__).warning("   - Admin routes: /admin")
    _log.getLogger(__name__).warning("   - API routes: /api")
    _log.getLogger(__name__).warning("   - Cart routes: /cart")
    _log.getLogger(__name__).warning("   - Utility routes: / (health, sitemap, robots, lang)")
    _log.getLogger(__name__).warning("   - Islamic routes: /islamic")


# ==================== ROUTE HELPERS ====================

def get_menu_items(lang='am'):
    """
    Get navigation menu items based on language.
    
    Args:
        lang (str): Language code (am, en, ar)
    
    Returns:
        list: Menu items with name and URL
    """
    menu_items = {
        'am': [
            {'name': 'መነሻ', 'url': '/'},
            {'name': 'ምርቶች', 'url': '/products'},
            {'name': 'ምድቦች', 'url': '/categories'},
            {'name': 'ቅርንጫፎች', 'url': '/branches'},
            {'name': 'እውቂያ', 'url': '/contact'},
            {'name': 'ስለ እኛ', 'url': '/about'}
        ],
        'en': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Products', 'url': '/products'},
            {'name': 'Categories', 'url': '/categories'},
            {'name': 'Branches', 'url': '/branches'},
            {'name': 'Contact', 'url': '/contact'},
            {'name': 'About', 'url': '/about'}
        ],
        'ar': [
            {'name': 'الرئيسية', 'url': '/'},
            {'name': 'المنتجات', 'url': '/products'},
            {'name': 'الفئات', 'url': '/categories'},
            {'name': 'الفروع', 'url': '/branches'},
            {'name': 'اتصل بنا', 'url': '/contact'},
            {'name': 'معلومات عنا', 'url': '/about'}
        ]
    }
    
    return menu_items.get(lang, menu_items['am'])


def get_footer_links(lang='am'):
    """
    Get footer links based on language.
    
    Args:
        lang (str): Language code (am, en, ar)
    
    Returns:
        dict: Footer links organized by section
    """
    footer_links = {
        'am': {
            'quick_links': [
                {'name': 'መነሻ', 'url': '/'},
                {'name': 'ምርቶች', 'url': '/products'},
                {'name': 'ስለ እኛ', 'url': '/about'},
                {'name': 'እውቂያ', 'url': '/contact'}
            ],
            'customer_service': [
                {'name': 'የደንበኛ አገልግሎት', 'url': '/contact'},
                {'name': 'መመሪያ', 'url': '/shipping-info'},
                {'name': 'መመለስ ፖሊሲ', 'url': '/returns'},
                {'name': 'ጥያቄዎች', 'url': '/faq'}
            ],
            'account': [
                {'name': 'መግቢያ', 'url': '/login'},
                {'name': 'ተመዝገብ', 'url': '/register'},
                {'name': 'መገለጫ', 'url': '/profile'},
                {'name': 'ትዕዛዞች', 'url': '/orders'}
            ]
        },
        'en': {
            'quick_links': [
                {'name': 'Home', 'url': '/'},
                {'name': 'Products', 'url': '/products'},
                {'name': 'About', 'url': '/about'},
                {'name': 'Contact', 'url': '/contact'}
            ],
            'customer_service': [
                {'name': 'Customer Service', 'url': '/contact'},
                {'name': 'Shipping Info', 'url': '/shipping-info'},
                {'name': 'Returns Policy', 'url': '/returns'},
                {'name': 'FAQ', 'url': '/faq'}
            ],
            'account': [
                {'name': 'Login', 'url': '/login'},
                {'name': 'Register', 'url': '/register'},
                {'name': 'Profile', 'url': '/profile'},
                {'name': 'Orders', 'url': '/orders'}
            ]
        },
        'ar': {
            'quick_links': [
                {'name': 'الرئيسية', 'url': '/'},
                {'name': 'المنتجات', 'url': '/products'},
                {'name': 'معلومات عنا', 'url': '/about'},
                {'name': 'اتصل بنا', 'url': '/contact'}
            ],
            'customer_service': [
                {'name': 'خدمة العملاء', 'url': '/contact'},
                {'name': 'معلومات الشحن', 'url': '/shipping-info'},
                {'name': 'سياسة الإرجاع', 'url': '/returns'},
                {'name': 'الأسئلة الشائعة', 'url': '/faq'}
            ],
            'account': [
                {'name': 'تسجيل الدخول', 'url': '/login'},
                {'name': 'التسجيل', 'url': '/register'},
                {'name': 'الملف الشخصي', 'url': '/profile'},
                {'name': 'الطلبات', 'url': '/orders'}
            ]
        }
    }
    
    return footer_links.get(lang, footer_links['am'])


# ==================== PACKAGE EXPORTS ====================

__all__ = [
    'register_routes',
    'get_menu_items',
    'get_footer_links'
]

__version__ = '1.0.0'

import logging as _log
_log.getLogger(__name__).debug("✅ Routes package initialized")