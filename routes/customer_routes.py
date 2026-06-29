"""
Customer Routes for SEMIRA FASHION

Public-facing routes: home, products, categories, branches, auth,
orders, wishlist, tracking, static info pages.
"""

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, jsonify, make_response, current_app
)
from extensions import limiter
from middleware.auth import user_login_required
from middleware.platform import get_platform, is_android_app
from database.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from services.whatsapp_service import WhatsAppService
from services.notification_service import notify_user, notify_admin
from routes.shared import get_lang, WHATSAPP_NUMBER, SUPPORTED_LANGUAGES
from utils.email_service import send_password_reset_email
import re
import os
import urllib.parse
import datetime as datetime_
import uuid

customer_bp = Blueprint('customer', __name__)


# ==================== HOME PAGE ====================

@customer_bp.route('/')
def index():
    """Home page with featured/new products and ads."""
    lang = get_lang()
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*, c.name as category_name, c.name_am as category_name_am
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1 AND p.is_featured = 1 ORDER BY p.id DESC LIMIT 12
        """)
        featured_products = cursor.fetchall()

        cursor.execute("""
            SELECT p.*, c.name as category_name, c.name_am as category_name_am
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1 AND p.is_new = 1 ORDER BY p.id DESC LIMIT 12
        """)
        new_products = cursor.fetchall()

        cursor.execute("""
            SELECT * FROM advertisements
            WHERE is_active = 1
            AND (end_date IS NULL OR end_date > NOW())
            AND (start_date IS NULL OR start_date <= NOW())
            ORDER BY sort_order ASC, id DESC
        """)
        ads = cursor.fetchall()

        cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order ASC")
        categories = cursor.fetchall()

        def row_to_dict(row):
            if row is None:
                return {}
            return {key: row[key] for key in row.keys()}

        featured_list = [row_to_dict(p) for p in featured_products] if featured_products else []
        new_list = [row_to_dict(p) for p in new_products] if new_products else []
        ads_list = [row_to_dict(ad) for ad in ads] if ads else []
        categories_list = [row_to_dict(cat) for cat in categories] if categories else []

        recently_viewed_ids = session.get('recently_viewed', [])
        recently_viewed_list = []
        if recently_viewed_ids:
            # Validate each ID is a safe integer before use in query
            safe_ids = []
            for i in recently_viewed_ids:
                try:
                    safe_ids.append(int(i))
                except (ValueError, TypeError):
                    pass
            if not safe_ids:
                recently_viewed_ids = []
            else:
                placeholders = ','.join(['%s'] * len(safe_ids))
                cursor.execute(f"""
                    SELECT p.*, c.name as category_name, c.name_am as category_name_am
                    FROM products p LEFT JOIN categories c ON p.category_id = c.id
                    WHERE p.id IN ({placeholders}) AND p.is_active = 1
                """, safe_ids)
                rows = cursor.fetchall()
                row_map = {str(row['id']): row_to_dict(row) for row in rows}
                recently_viewed_list = [row_map[i] for i in recently_viewed_ids if i in row_map]

        platform = get_platform()
        show_about = platform in ('desktop', 'mobile_browser')

        hijri_home = None
        daily_ayah = None
        next_event = None
        try:
            from routes.islamic_routes import (
                _gregorian_to_hijri, HIJRI_MONTHS,
                _load_quran_data, SURAHS, _upcoming_holidays
            )
            _today = datetime_.date.today()
            _hy, _hm, _hd = _gregorian_to_hijri(_today.year, _today.month, _today.day)
            hijri_home = {
                'day':   _hd,
                'month': HIJRI_MONTHS[_hm - 1],
                'year':  _hy,
                'full':  f"{_hd} {HIJRI_MONTHS[_hm-1]} {_hy} AH",
            }
            _holidays = _upcoming_holidays(1)
            if _holidays:
                _h = _holidays[0]
                next_event = {
                    'name':      _h['name'],
                    'icon':      _h['icon'],
                    'gregorian': _h['gregorian'],
                    'days_away': _h['days_away'],
                    'is_today':  _h['is_today'],
                }
            _qdata = _load_quran_data()
            if _qdata:
                _featured = [55, 36, 67, 18, 56, 3, 59, 78, 87, 89, 91, 93, 94, 96, 99, 112, 113, 114]
                _doy = _today.timetuple().tm_yday
                _snum = _featured[_doy % len(_featured)]
                _verses = _qdata.get(_snum) or _qdata.get(str(_snum)) or []
                if _verses:
                    _aidx = (_doy // len(_featured)) % max(1, len(_verses))
                    _v = _verses[_aidx]
                    _meta = next((s for s in SURAHS if s[0] == _snum), None)
                    daily_ayah = {
                        'text':       _v.get('text', '') if isinstance(_v, dict) else str(_v),
                        'surah_num':  _snum,
                        'surah_name': _meta[2] if _meta else f'Surah {_snum}',
                        'ayah_num':   _v.get('verse', _aidx + 1) if isinstance(_v, dict) else _aidx + 1,
                    }
        except Exception as _isl_err:
            import logging as _log
            _log.getLogger(__name__).warning("Islamic/Hijri data error: %s", _isl_err)

        return render_template('customer/index.html',
                               featured_products=featured_list,
                               new_products=new_list,
                               ads=ads_list,
                               categories=categories_list,
                               recently_viewed_products=recently_viewed_list,
                               show_about=show_about,
                               platform=platform,
                               lang=lang,
                               hijri_home=hijri_home,
                               daily_ayah=daily_ayah,
                               next_event=next_event)
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error("Home page error: %s", e, exc_info=True)
        return render_template('customer/index.html',
                               featured_products=[], new_products=[], ads=[],
                               categories=[], recently_viewed_products=[],
                               show_about=True, platform='desktop', lang=lang)


# ==================== PRODUCT ROUTES ====================

@customer_bp.route('/products')
def products():
    """All products with pagination."""
    lang = get_lang()
    page = max(1, request.args.get('page', 1, type=int))
    per_page = 12
    offset = (page - 1) * per_page

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM products WHERE is_active = 1"
        )
        total = cursor.fetchone()[0] or 0

        import math
        total_pages = max(1, math.ceil(total / per_page))
        page = min(page, total_pages)
        offset = (page - 1) * per_page

        cursor.execute("""
            SELECT p.*, c.name as category_name, c.name_am as category_name_am,
                   c.id as cat_id
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1 ORDER BY p.id DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        products_rows = cursor.fetchall()

        cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order ASC")
        categories = cursor.fetchall()

        products_list = [dict(p) for p in products_rows] if products_rows else []
        categories_list = [dict(cat) for cat in categories] if categories else []

        return render_template('customer/product_grid.html',
                               products=products_list, categories=categories_list,
                               page=page, total_pages=total_pages, total=total, lang=lang)
    except Exception as e:
        import traceback
        current_app.logger.error(f"Products page error: {e}\n{traceback.format_exc()}")
        return render_template('customer/product_grid.html',
                               products=[], categories=[], page=1, total_pages=0,
                               total=0, lang=lang)


@customer_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page."""
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*, c.name as category_name, c.name_am as category_name_am
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s AND p.is_active = 1
        """, (product_id,))
        product = cursor.fetchone()

        if not product:
            flash('Product not found!', 'danger')
            return redirect(url_for('customer.products'))

        cursor.execute("UPDATE products SET views = views + 1 WHERE id = %s", (product_id,))
        conn.commit()

        # Track recently viewed
        recently_viewed = session.get('recently_viewed', [])
        pid_str = str(product_id)
        if pid_str in recently_viewed:
            recently_viewed.remove(pid_str)
        recently_viewed.insert(0, pid_str)
        session['recently_viewed'] = recently_viewed[:10]

        cursor.execute("""
            SELECT * FROM products
            WHERE category_id = %s AND id != %s AND is_active = 1
            ORDER BY id DESC LIMIT 4
        """, (product['category_id'], product_id))
        related_products = cursor.fetchall()

        product_dict = dict(product)
        related_list = [dict(p) for p in related_products] if related_products else []

        # Fetch recently viewed products (from session, excluding current)
        recently_viewed_ids = session.get('recently_viewed', [])
        rv_ids_excl = [i for i in recently_viewed_ids if i != str(product_id)]
        recently_viewed_list = []
        if rv_ids_excl:
            try:
                placeholders = ','.join(['%s'] * len(rv_ids_excl))
                cursor.execute(
                    f"SELECT id, name, name_am, price, compare_price, thumbnail FROM products WHERE id IN ({placeholders}) AND is_active = 1 LIMIT 6",
                    rv_ids_excl
                )
                rv_rows = cursor.fetchall()
                rv_map = {str(r['id']): dict(r) for r in rv_rows}
                recently_viewed_list = [rv_map[i] for i in rv_ids_excl if i in rv_map]
            except Exception:
                recently_viewed_list = []

        discount = None
        if product_dict.get('compare_price') and product_dict['compare_price'] > product_dict['price']:
            discount = int(((product_dict['compare_price'] - product_dict['price']) / product_dict['compare_price']) * 100)

        is_logged_in = session.get('user_id') is not None
        from routes.shared import USER_DISCOUNT_RATE
        final_price = float(product_dict['price'])
        if is_logged_in:
            final_price = float(product_dict['price']) * (1 - USER_DISCOUNT_RATE)

        # Fetch live avg rating for this product
        try:
            cursor.execute("""
                SELECT AVG(rating) as avg_r, COUNT(*) as cnt
                FROM reviews WHERE product_id = %s AND is_approved = 1
            """, (product_id,))
            rrow = cursor.fetchone()
            product_dict['rating'] = round(rrow[0], 1) if rrow and rrow[0] else 0
            product_dict['reviews'] = rrow[1] if rrow else 0
        except Exception:
            product_dict['rating'] = 0
            product_dict['reviews'] = 0

        return render_template('customer/product_detail.html',
                               product=product_dict, related_products=related_list,
                               recently_viewed_products=recently_viewed_list,
                               discount=discount, final_price=round(final_price, 2),
                               is_logged_in=is_logged_in, lang=lang)
    except Exception as e:
        current_app.logger.error(f"Product detail error: {e}")
        flash('Error loading product.', 'error')
        return redirect(url_for('customer.products'))


# ==================== CATEGORY ROUTES ====================

@customer_bp.route('/categories')
def categories():
    """All categories page."""
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, COUNT(p.id) as product_count
            FROM categories c LEFT JOIN products p ON p.category_id = c.id AND p.is_active = 1
            WHERE c.is_active = 1 GROUP BY c.id ORDER BY c.sort_order ASC
        """)
        cats = cursor.fetchall()
        return render_template('customer/categories.html',
                               categories=[dict(c) for c in cats] if cats else [], lang=lang)
    except Exception as e:
        current_app.logger.error(f"Categories error: {e}")
        return render_template('customer/categories.html', categories=[], lang=lang)


@customer_bp.route('/category')
@customer_bp.route('/category/<int:category_id>')
def category_products(category_id=None):
    """Products filtered by category."""
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order ASC")
        all_cats = cursor.fetchall()

        page_title = None
        if category_id:
            cursor.execute("SELECT * FROM categories WHERE id = %s AND is_active = 1", (category_id,))
            cat_row = cursor.fetchone()
            if cat_row:
                page_title = cat_row['name_am'] if lang == 'am' else cat_row['name']
                cursor.execute("""
                    SELECT p.*, c.name as cat_name
                    FROM products p LEFT JOIN categories c ON p.category_id = c.id
                    WHERE p.category_id = %s AND p.is_active = 1 ORDER BY p.id DESC
                """, (category_id,))
            else:
                page_title = 'ሁሉም ምርቶች' if lang == 'am' else 'All Products'
                cursor.execute("""
                    SELECT p.*, c.name as cat_name
                    FROM products p LEFT JOIN categories c ON p.category_id = c.id
                    WHERE p.is_active = 1 ORDER BY p.id DESC
                """)
        else:
            page_title = 'ሁሉም ምርቶች' if lang == 'am' else 'All Products'
            cursor.execute("""
                SELECT p.*, c.name as cat_name
                FROM products p LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 ORDER BY p.id DESC
            """)

        products_rows = cursor.fetchall()
        products_list = [dict(p) for p in products_rows] if products_rows else []
        categories_list = [dict(c) for c in all_cats] if all_cats else []

        return render_template('customer/category.html',
                               products=products_list, categories=categories_list,
                               page_title=page_title, current_category=category_id,
                               lang=lang)
    except Exception as e:
        current_app.logger.error(f"Category products error: {e}")
        flash('Unable to load category products.', 'error')
        return render_template('customer/category.html',
                               products=[], categories=[], page_title='Products',
                               current_category=None, lang=lang)


# ==================== WEDE SEMIRA CLOTHING SECTION ====================

@customer_bp.route('/wede-semira')
def wede_semira():
    """Dedicated ሰሚራ women's and children's clothing section."""
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order ASC")
        clothing_cats = cursor.fetchall()
        clothing_cat_ids = [c['id'] for c in clothing_cats]

        if clothing_cat_ids:
            placeholders = ','.join(['%s'] * len(clothing_cat_ids))
            cursor.execute(f"""
                SELECT p.*, c.name as cat_name, c.name_am as cat_name_am
                FROM products p LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 AND p.category_id IN ({placeholders})
                ORDER BY p.is_featured DESC, p.id DESC LIMIT 40
            """, clothing_cat_ids)
        else:
            cursor.execute("""
                SELECT p.*, c.name as cat_name, c.name_am as cat_name_am
                FROM products p LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 ORDER BY p.is_featured DESC, p.id DESC LIMIT 40
            """)

        products_rows = cursor.fetchall()

        # Products by category for per-section display — built from the bulk query (no N+1)
        cat_products = {cat['id']: [] for cat in clothing_cats}
        for p in products_rows:
            cid = p['category_id']
            if cid in cat_products and len(cat_products[cid]) < 8:
                cat_products[cid].append(dict(p))

        return render_template('customer/wede_semira.html',
                               clothing_categories=[dict(c) for c in clothing_cats],
                               products=[dict(p) for p in products_rows],
                               cat_products=cat_products,
                               lang=lang)
    except Exception as e:
        current_app.logger.error(f"Wede Semira page error: {e}")
        return render_template('customer/wede_semira.html',
                               clothing_categories=[], products=[],
                               cat_products={}, lang=lang)


# ==================== SEARCH ====================

@customer_bp.route('/search')
def search():
    """Search products page."""
    lang = get_lang()
    query = request.args.get('q', '').strip()

    if not query:
        return redirect(url_for('customer.products'))

    try:
        conn = get_db()
        cursor = conn.cursor()

        search_pattern = f'%{query}%'
        cursor.execute("""
            SELECT p.*, c.name as category_name, c.name_am as category_name_am
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
            AND (p.name ILIKE %s OR p.name_en ILIKE %s OR p.name_am ILIKE %s OR p.name_ar ILIKE %s
                 OR p.description ILIKE %s OR p.description_am ILIKE %s OR p.description_ar ILIKE %s)
            ORDER BY CASE WHEN p.name_am ILIKE %s THEN 0
                          WHEN p.name ILIKE %s   THEN 1
                          ELSE 2 END,
                     p.is_featured DESC, p.id DESC
            LIMIT 200
        """, (search_pattern,) * 7 + (search_pattern, search_pattern))
        products_rows = cursor.fetchall()

        cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order ASC LIMIT 6")
        cats = cursor.fetchall()

        return render_template('customer/search.html',
                               products=[dict(p) for p in products_rows] if products_rows else [],
                               categories=[dict(c) for c in cats] if cats else [],
                               query=query, lang=lang)
    except Exception as e:
        current_app.logger.error(f"Search error: {e}")
        flash('Search failed.', 'error')
        return render_template('customer/search.html', products=[], categories=[],
                               query=query, lang=lang)


# ==================== BRANCHES ====================

@customer_bp.route('/branches')
def branches():
    """Branches page with Google Maps."""
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM branches WHERE is_active = 1 ORDER BY sort_order ASC")
        branches_rows = cursor.fetchall()

        branches_list = []
        for branch in branches_rows:
            bd = dict(branch)
            bd['maps_url'] = f"https://www.google.com/maps/dir/?api=1&destination={bd.get('latitude', 0)},{bd.get('longitude', 0)}"
            branches_list.append(bd)

        from routes.shared import BRANCH_PHONE_NUMBERS
        phone_numbers = [WHATSAPP_NUMBER] + BRANCH_PHONE_NUMBERS
        return render_template('customer/branches.html',
                               branches=branches_list, phone_numbers=phone_numbers,
                               lang=lang)
    except Exception as e:
        current_app.logger.error(f"Branches error: {e}")
        return render_template('customer/branches.html', branches=[], phone_numbers=[], lang=lang)


# ==================== ABOUT ====================

@customer_bp.route('/about')
def about():
    """About us page."""
    lang = get_lang()
    platform = get_platform()
    return render_template('customer/about.html', lang=lang, platform=platform)


# ==================== CONTACT ====================

@customer_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page with WhatsApp integration."""
    lang = get_lang()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not message:
            flash('Please fill in name and message', 'error')
            return redirect(url_for('customer.contact'))

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO contact_messages (name, email, phone, message)
                VALUES (%s, %s, %s, %s)
            """, (name, email, phone, message))
            conn.commit()
        except Exception as e:
            current_app.logger.error(f"Error saving contact: {e}")

        whatsapp_msg = (f"📬 New Contact Message - SEMIRA FASHION\n\n"
                        f"👤 Name: {name}\n")
        if email:
            whatsapp_msg += f"📧 Email: {email}\n"
        if phone:
            whatsapp_msg += f"📞 Phone: {phone}\n"
        whatsapp_msg += f"\n💬 Message:\n{message}"

        encoded = urllib.parse.quote(whatsapp_msg)
        whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={encoded}"

        flash('Message sent! You will be redirected to WhatsApp.', 'success')
        return redirect(whatsapp_url)

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM branches WHERE is_active = 1 ORDER BY sort_order ASC")
        branches_rows = cursor.fetchall()
        branches_list = [dict(b) for b in branches_rows] if branches_rows else []
    except Exception:
        branches_list = []

    return render_template('customer/contact.html',
                           branches=branches_list, whatsapp_number=WHATSAPP_NUMBER, lang=lang)


# ==================== STATIC INFO PAGES ====================

@customer_bp.route('/faq')
def faq():
    lang = get_lang()
    return render_template('customer/faq.html', lang=lang)


@customer_bp.route('/shipping-info')
def shipping_info():
    lang = get_lang()
    return render_template('customer/shipping_info.html', lang=lang)


@customer_bp.route('/returns')
def returns_policy():
    lang = get_lang()
    return render_template('customer/returns.html', lang=lang)


@customer_bp.route('/terms')
def terms():
    lang = get_lang()
    return render_template('customer/terms.html', lang=lang)


@customer_bp.route('/privacy')
def privacy():
    lang = get_lang()
    return render_template('customer/privacy.html', lang=lang)


# ==================== USER AUTHENTICATION ====================

@customer_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute; 20 per hour", methods=["POST"])
def user_login():
    """User login page."""
    if session.get('user_id'):
        return redirect(url_for('customer.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s AND is_active = 1", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password_hash'], password):
                # Merge guest session cart → DB cart before setting session
                guest_cart = session.get('cart', {})
                session['user_id'] = user['id']
                session['user_name'] = user['full_name']
                session['user_email'] = user['email']
                session['user_phone'] = user['phone']
                if guest_cart:
                    try:
                        for pid_str, qty in guest_cart.items():
                            pid = int(pid_str)
                            cursor.execute(
                                "SELECT id, quantity FROM cart_items WHERE user_id=%s AND product_id=%s",
                                (user['id'], pid)
                            )
                            existing = cursor.fetchone()
                            if existing:
                                cursor.execute(
                                    "UPDATE cart_items SET quantity = quantity + %s WHERE id = %s",
                                    (qty, existing['id'])
                                )
                            else:
                                cursor.execute(
                                    "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s,%s,%s)",
                                    (user['id'], pid, qty)
                                )
                        conn.commit()
                        session.pop('cart', None)
                    except Exception as _me:
                        current_app.logger.error(f"Cart merge error: {_me}")
                flash('Login successful!', 'success')
                next_page = request.args.get('next', '')
                from urllib.parse import urlparse as _urlparse
                _p = _urlparse(next_page)
                # Only allow same-site relative URLs (no scheme / netloc)
                if next_page and not _p.scheme and not _p.netloc and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('customer.index'))
            else:
                flash('Invalid email or password!', 'danger')
        except Exception as e:
            current_app.logger.error(f"Login error: {e}")
            flash('Login error. Please try again.', 'danger')

    return render_template('auth/user_login.html')


@customer_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute; 10 per hour", methods=["POST"])
def user_register():
    """User registration page."""
    if session.get('user_id'):
        return redirect(url_for('customer.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []
        if not full_name:
            errors.append('Full name is required')
        if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append('Valid email is required')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('customer.user_register'))

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Email already registered!', 'danger')
                return redirect(url_for('customer.user_register'))

            import random as _random
            base_username = email.split('@')[0].lower()
            username = base_username
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                username = base_username + str(_random.randint(100, 9999))

            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            cursor.execute("""
                INSERT INTO users (username, full_name, email, phone, password_hash, is_admin, is_active)
                VALUES (%s, %s, %s, %s, %s, 0, 1) RETURNING id
            """, (username, full_name, email, phone, password_hash))
            row = cursor.fetchone()
            conn.commit()
            user_id = row[0] if row else None

            session['user_id'] = user_id
            session['user_name'] = full_name
            session['user_email'] = email
            session['user_phone'] = phone

            # Merge any guest session cart into DB cart
            guest_cart = session.get('cart', {})
            if guest_cart:
                try:
                    for pid_str, qty in guest_cart.items():
                        pid = int(pid_str)
                        cursor.execute(
                            "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s,%s,%s)",
                            (user_id, pid, qty)
                        )
                    conn.commit()
                    session.pop('cart', None)
                except Exception as _me:
                    current_app.logger.error(f"Cart merge on register error: {_me}")

            flash('Registration successful! Welcome to SEMIRA FASHION!', 'success')

            try:
                notify_user(
                    user_id,
                    '🎉 Welcome to SEMIRA FASHION!',
                    f'Hello {full_name}! Your account is ready. Enjoy 10% discount on all orders.',
                    type='welcome',
                    link='/dashboard'
                )
                notify_admin(
                    '👤 New Customer Registered',
                    f'{full_name} ({email}) just created an account.',
                    type='new_user',
                    link='/admin/users',
                    ref_user_id=user_id
                )
            except Exception:
                pass

            return redirect(url_for('customer.index'))
        except Exception as e:
            current_app.logger.error(f"Register error: {e}")
            flash('Registration failed. Please try again.', 'danger')

    return render_template('auth/user_register.html')


@customer_bp.route('/logout')
def user_logout():
    """User logout."""
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('user_phone', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('customer.index'))


# ==================== USER PROFILE ====================

@customer_bp.route('/profile')
@user_login_required
def user_profile():
    """User profile page."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
                   SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                   SUM(total) as total_spent
            FROM orders WHERE user_id = %s
        """, (session['user_id'],))
        order_stats_row = cursor.fetchone()
        order_stats = dict(order_stats_row) if order_stats_row else {}

        cursor.execute("""
            SELECT * FROM orders WHERE user_id = %s ORDER BY id DESC LIMIT 20
        """, (session['user_id'],))
        orders_raw = cursor.fetchall()
        orders = [dict(o) for o in orders_raw] if orders_raw else []

        return render_template('auth/user_profile.html',
                               user=user, order_stats=order_stats, orders=orders)
    except Exception as e:
        current_app.logger.error(f"Profile error: {e}")
        flash('Error loading profile.', 'error')
        return redirect(url_for('customer.index'))


@customer_bp.route('/profile/update', methods=['POST'])
@user_login_required
def update_profile():
    """Update user profile."""
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET full_name = %s, phone = %s, address = %s, city = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (full_name, phone, address, city, session['user_id']))
        conn.commit()
        session['user_name'] = full_name
        session['user_phone'] = phone
        if is_ajax:
            return jsonify({'success': True, 'message': 'Profile updated successfully!'})
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f"Update profile error: {e}")
        if is_ajax:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error updating profile.', 'error')

    return redirect(url_for('customer.user_profile'))


@customer_bp.route('/change-password', methods=['POST'])
@user_login_required
def change_password():
    """Change user password (AJAX)."""
    data = request.get_json(silent=True) or {}
    new_password = data.get('password', '')

    if not new_password or len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()
        password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s",
                       (password_hash, session['user_id']))
        conn.commit()
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    except Exception as e:
        current_app.logger.error(f"Password change error: {e}")
        return jsonify({'success': False, 'error': 'Failed to change password'}), 500


@customer_bp.route('/delete-account', methods=['POST'])
@user_login_required
def delete_account():
    """Delete user account (AJAX)."""
    data = request.get_json(silent=True) or {}
    password = data.get('password', '')

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()

        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'success': False, 'error': 'Invalid password'}), 401

        cursor.execute("DELETE FROM users WHERE id = %s", (session['user_id'],))
        conn.commit()
        session.clear()
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
    except Exception as e:
        current_app.logger.error(f"Delete account error: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete account'}), 500


# ==================== ORDER ROUTES ====================

@customer_bp.route('/orders')
@user_login_required
def user_orders():
    """User order history, optionally filtered by status."""
    lang = get_lang()
    from flask import request as _req
    status_filter = _req.args.get('status', '').strip().lower()
    try:
        conn = get_db()
        cursor = conn.cursor()
        if status_filter == 'delivered':
            cursor.execute(
                "SELECT * FROM orders WHERE user_id = %s AND status = 'delivered' ORDER BY id DESC",
                (session['user_id'],)
            )
        elif status_filter == 'pending':
            cursor.execute(
                "SELECT * FROM orders WHERE user_id = %s AND status NOT IN ('delivered','cancelled') ORDER BY id DESC",
                (session['user_id'],)
            )
        else:
            cursor.execute(
                "SELECT * FROM orders WHERE user_id = %s ORDER BY id DESC",
                (session['user_id'],)
            )
        orders = cursor.fetchall()
        return render_template('auth/user_orders.html',
                               orders=[dict(o) for o in orders] if orders else [],
                               lang=lang, status_filter=status_filter)
    except Exception as e:
        current_app.logger.error(f"User orders error: {e}")
        return render_template('auth/user_orders.html', orders=[], lang=lang, status_filter='')


@customer_bp.route('/order/<int:order_id>')
@user_login_required
def order_detail(order_id):
    """Order detail page."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s",
                       (order_id, session['user_id']))
        order = cursor.fetchone()
        if not order:
            flash('Order not found!', 'danger')
            return redirect(url_for('customer.user_orders'))

        cursor.execute("""
            SELECT oi.*, p.name, p.name_am, p.name_ar, p.thumbnail
            FROM order_items oi JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_id,))
        items = cursor.fetchall()

        return render_template('auth/order_detail.html',
                               order=dict(order),
                               items=[dict(i) for i in items] if items else [],
                               whatsapp_number=WHATSAPP_NUMBER)
    except Exception as e:
        current_app.logger.error(f"Order detail error: {e}")
        flash('Error loading order.', 'error')
        return redirect(url_for('customer.user_orders'))


@customer_bp.route('/order-confirmation/<int:order_id>')
def order_confirmation(order_id):
    """Order confirmation page — accessible to both logged-in users and guests."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        user_id = session.get('user_id')

        if user_id:
            # Logged-in user: must own the order
            cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s",
                           (order_id, user_id))
        else:
            # Guest: validate using secure token from session
            # Token prevents unauthorized access to other guests' orders
            guest_order_token = session.get('guest_order_token')
            if not guest_order_token:
                flash('ትዕዛዝ ማየት ያልተፈቀደ ነው።', 'danger')
                return redirect(url_for('customer.index'))
            
            # Query the order and verify token matches
            cursor.execute("""
                SELECT * FROM orders WHERE id = %s AND user_id IS NULL
            """, (order_id,))
            order = cursor.fetchone()
            
            if not order:
                flash('ትዕዛዝ አልተገኘም።', 'danger')
                return redirect(url_for('customer.index'))
            
            # Verify token is valid for this specific order
            # Token should be a hash of order_id + order_number + phone to prevent guessing
            import hmac
            import hashlib
            expected_token = hmac.new(
                current_app.config['SECRET_KEY'].encode(),
                f"{order['id']}-{order['order_number']}-{order['shipping_phone']}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            if guest_order_token != expected_token:
                current_app.logger.warning(f"Invalid guest order token for order {order_id}")
                flash('ትዕዛዝ ማየት ያልተፈቀደ ነው።', 'danger')
                return redirect(url_for('customer.index'))
            
        if not 'order' in locals():
            # For logged-in users, fetch the order if not already fetched
            order = cursor.fetchone()

        if not order:
            flash('Order not found!', 'danger')
            return redirect(url_for('customer.index'))

        cursor.execute("""
            SELECT oi.*, p.name, p.name_am, p.name_ar, p.thumbnail
            FROM order_items oi JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_id,))
        items = cursor.fetchall()
        items_list = [dict(i) for i in items] if items else []

        order_dict = dict(order)
        customer_name = order_dict.get('customer_name') or session.get('user_name', 'Customer')
        customer_phone = order_dict.get('shipping_phone') or session.get('user_phone', '')

        wa_items = [
            {
                'name': it.get('name', 'Product'),
                'quantity': it.get('quantity', 1),
                'price': it.get('price_at_time', 0),
                'discounted_price': it.get('price_at_time', 0),
            }
            for it in items_list
        ]
        whatsapp_url = WhatsAppService.send_order_message(
            customer_name=customer_name,
            customer_phone=customer_phone,
            items=wa_items,
            total=order_dict.get('total', 0),
            order_number=order_dict.get('order_number', '')
        )

        return render_template('auth/order_confirmation.html',
                               order=order_dict,
                               items=items_list,
                               whatsapp_url=whatsapp_url)
    except Exception as e:
        current_app.logger.error(f"Order confirmation error: {e}")
        flash('Error loading order.', 'error')
        return redirect(url_for('customer.index'))


# ==================== FORGOT / RESET PASSWORD ====================

@customer_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page."""
    lang = get_lang()

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Please enter your email address', 'error')
            return render_template('auth/forgot_password.html', lang=lang)

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, full_name FROM users WHERE email = %s AND is_active = 1",
                           (email,))
            user = cursor.fetchone()

            if user:
                cursor.execute(
                    "UPDATE password_reset_tokens SET used = 1 WHERE email = %s AND used = 0",
                    (email,)
                )
                reset_token = uuid.uuid4().hex
                expires_at = datetime_.datetime.now() + datetime_.timedelta(hours=1)
                cursor.execute("""
                    INSERT INTO password_reset_tokens (email, token, expires_at)
                    VALUES (%s, %s, %s)
                """, (email, reset_token, expires_at))
                conn.commit()

                reset_url = url_for('customer.reset_password',
                                    token=reset_token, _external=True)
                user_name = user['full_name'] or email
                email_sent = send_password_reset_email(email, user_name, reset_url)

                if email_sent:
                    flash('Password reset link sent! Check your email inbox (and spam folder).', 'success')
                else:
                    flash(
                        f'Email service not configured. '
                        f'Share this reset link manually: {reset_url}',
                        'info'
                    )
            else:
                flash('If an account exists with that email, you will receive a reset link.', 'info')

        except Exception as e:
            current_app.logger.error(f"Forgot password error: {e}")
            flash('Error processing request. Please try again.', 'error')

    return render_template('auth/forgot_password.html', lang=lang)


@customer_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password page."""
    lang = get_lang()

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT email, expires_at, used FROM password_reset_tokens WHERE token = %s
        """, (token,))
        token_row = cursor.fetchone()
    except Exception as e:
        current_app.logger.error(f"Token lookup error: {e}")
        token_row = None

    if (not token_row or token_row['used']
            or token_row['expires_at'] < datetime_.datetime.now()):
        flash('Invalid or expired reset link. Please request a new one.', 'error')
        return redirect(url_for('customer.forgot_password'))

    stored_email = token_row['email']

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('auth/reset_password.html', token=token, lang=lang)

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html', token=token, lang=lang)

        try:
            conn = get_db()
            cursor = conn.cursor()
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s",
                           (password_hash, stored_email))
            cursor.execute("UPDATE password_reset_tokens SET used = 1 WHERE token = %s", (token,))
            conn.commit()
            flash('Password reset successful! Please login with your new password.', 'success')
            return redirect(url_for('customer.user_login'))
        except Exception as e:
            current_app.logger.error(f"Reset password error: {e}")
            flash('Error resetting password. Please try again.', 'error')

    return render_template('auth/reset_password.html', token=token, lang=lang)


# ==================== ORDER TRACKING ====================

@customer_bp.route('/track-order', methods=['GET'])
def track_order_public():
    """Public order tracking — requires order number + phone for security."""
    lang = get_lang()
    order_number = request.args.get('order', '').strip().upper()
    phone_raw    = request.args.get('phone', '').strip()

    # Normalize phone: strip spaces/dashes, handle 09xx → 2519xx
    def normalize_phone(p):
        p = p.replace(' ', '').replace('-', '')
        if p.startswith('09') or p.startswith('07'):
            p = '251' + p[1:]
        return p

    if not order_number:
        return render_template('customer/track_order.html',
                               order=None, items=[], lang=lang,
                               whatsapp_number=WHATSAPP_NUMBER, error=None)

    if not phone_raw:
        return render_template('customer/track_order.html',
                               order=None, items=[], lang=lang,
                               whatsapp_number=WHATSAPP_NUMBER,
                               error='Please enter both your order number and phone number.')

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, u.full_name, u.email, u.phone
            FROM orders o LEFT JOIN users u ON o.user_id = u.id
            WHERE o.order_number = %s
        """, (order_number,))
        order = cursor.fetchone()

        if not order:
            return render_template('customer/track_order.html',
                                   order=None, items=[], lang=lang,
                                   whatsapp_number=WHATSAPP_NUMBER,
                                   error=f'Order "{order_number}" not found. Please check and try again.')

        order_dict = dict(order)

        # Verify phone matches the order (shipping_phone or user phone)
        stored_phones = set()
        for raw in [order_dict.get('shipping_phone'), order_dict.get('phone')]:
            if raw:
                stored_phones.add(normalize_phone(str(raw)))
        entered = normalize_phone(phone_raw)

        if not stored_phones or entered not in stored_phones:
            return render_template('customer/track_order.html',
                                   order=None, items=[], lang=lang,
                                   whatsapp_number=WHATSAPP_NUMBER,
                                   error='The phone number does not match this order. Please check and try again.')

        cursor.execute("""
            SELECT oi.*, p.name, p.name_am, p.name_ar, p.thumbnail
            FROM order_items oi JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_dict['id'],))
        items = cursor.fetchall()
        items_list = [dict(i) for i in items] if items else []

        # Fetch status history for timeline timestamps
        cursor.execute("""
            SELECT status, note, changed_at
            FROM order_status_history
            WHERE order_id = %s
            ORDER BY changed_at ASC
        """, (order_dict['id'],))
        history_rows = cursor.fetchall()
        # Build dict: status → first timestamp it was reached
        status_history = {}
        for row in history_rows:
            s = row['status']
            if s not in status_history:
                status_history[s] = {'time': row['changed_at'], 'note': row['note']}

        # Fallback: if no history yet, use order created_at for pending
        if not status_history and order_dict.get('created_at'):
            status_history['pending'] = {'time': order_dict['created_at'], 'note': None}

        return render_template('customer/track_order.html',
                               order=order_dict, items=items_list, lang=lang,
                               status_history=status_history,
                               whatsapp_number=WHATSAPP_NUMBER, error=None)
    except Exception as e:
        current_app.logger.error(f"Order tracking error: {e}")
        return render_template('customer/track_order.html',
                               order=None, items=[], lang=lang,
                               status_history={},
                               whatsapp_number=WHATSAPP_NUMBER,
                               error='Error loading order. Please try again.')


@customer_bp.route('/track-order/<order_number>')
def track_order(order_number):
    """Legacy route — redirect to the search page."""
    return redirect(url_for('customer.track_order_public', order=order_number))


# ==================== WISHLIST ====================

@customer_bp.route('/wishlist')
@user_login_required
def wishlist():
    """User wishlist page."""
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT w.id, w.product_id, w.created_at, w.price_at_add,
                   p.name, p.name_am, p.name_ar, p.price, p.compare_price, p.thumbnail,
                   p.stock_quantity
            FROM wishlist w JOIN products p ON w.product_id = p.id
            WHERE w.user_id = %s AND p.is_active = 1
            ORDER BY w.created_at DESC
        """, (session['user_id'],))
        wishlist_items = cursor.fetchall()
        wishlist_list = []
        for item in (wishlist_items or []):
            d = dict(item)
            # Calculate price drop info
            if d.get('price_at_add') and d['price_at_add'] > d['price']:
                d['price_dropped'] = True
                d['price_drop_amount'] = round(float(d['price_at_add']) - float(d['price']), 2)
                d['price_drop_pct'] = round(
                    (d['price_drop_amount'] / float(d['price_at_add'])) * 100
                )
            else:
                d['price_dropped'] = False
                d['price_drop_amount'] = 0
                d['price_drop_pct'] = 0
            wishlist_list.append(d)

        return render_template('customer/wishlist.html',
                               wishlist=wishlist_list, lang=lang)
    except Exception as e:
        current_app.logger.error(f"Wishlist error: {e}")
        flash('Error loading wishlist', 'error')
        return redirect(url_for('customer.index'))


# ==================== CUSTOMER DASHBOARD ====================

@customer_bp.route('/dashboard')
@user_login_required
def dashboard():
    """Unified customer dashboard with all user features."""
    lang = get_lang()
    tab = request.args.get('tab', 'overview')
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user_row = cursor.fetchone()
        user = dict(user_row) if user_row else {}

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(CASE WHEN status NOT IN ('delivered','cancelled') THEN 1 ELSE 0 END) as active,
                COALESCE(SUM(total), 0) as total_spent
            FROM orders WHERE user_id = %s
        """, (session['user_id'],))
        stats_row = cursor.fetchone()
        order_stats = dict(stats_row) if stats_row else {}

        cursor.execute("""
            SELECT * FROM orders WHERE user_id = %s ORDER BY id DESC LIMIT 50
        """, (session['user_id'],))
        orders_raw = cursor.fetchall()
        orders = [dict(o) for o in orders_raw] if orders_raw else []

        try:
            cursor.execute("""
                SELECT w.*, p.name, p.name_am, p.name_ar, p.price, p.compare_price,
                       p.thumbnail, p.is_active
                FROM wishlist w JOIN products p ON w.product_id = p.id
                WHERE w.user_id = %s AND p.is_active = 1
                ORDER BY w.created_at DESC
            """, (session['user_id'],))
            wishlist_raw = cursor.fetchall()
            wishlist_items = [dict(i) for i in wishlist_raw] if wishlist_raw else []
        except Exception:
            wishlist_items = []

        loyalty_points = 0
        loyalty_transactions = []
        try:
            cursor.execute("SELECT COALESCE(loyalty_points, 0) FROM users WHERE id = %s", (session['user_id'],))
            lp_row = cursor.fetchone()
            loyalty_points = int(lp_row[0]) if lp_row else 0

            cursor.execute("""
                SELECT lt.points, lt.type, lt.description, lt.created_at,
                       o.order_number
                FROM loyalty_transactions lt
                LEFT JOIN orders o ON lt.order_id = o.id
                WHERE lt.user_id = %s
                ORDER BY lt.created_at DESC LIMIT 30
            """, (session['user_id'],))
            lt_raw = cursor.fetchall()
            for row in (lt_raw or []):
                loyalty_transactions.append({
                    'points':       row[0],
                    'type':         row[1],
                    'description':  row[2],
                    'created_at':   str(row[3])[:10] if row[3] else '',
                    'order_number': row[4] or '',
                })
        except Exception:
            pass

        return render_template('auth/dashboard.html',
                               user=user,
                               order_stats=order_stats,
                               orders=orders,
                               wishlist_items=wishlist_items,
                               loyalty_points=loyalty_points,
                               loyalty_transactions=loyalty_transactions,
                               active_tab=tab,
                               lang=lang)
    except Exception as e:
        import traceback
        current_app.logger.error(f"Dashboard error: {e}\n{traceback.format_exc()}")
        flash('Error loading dashboard.', 'error')
        return redirect(url_for('customer.index'))


# ==================== ADMIN LOGIN REDIRECT ====================

@customer_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Redirect to admin login."""
    return redirect(url_for('admin.admin_login'))
