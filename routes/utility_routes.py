"""
Utility Routes for SEMIRA FASHION

Handles sitewide utility endpoints:
- Language switching
- Health checks
- robots.txt / sitemap.xml
- Diagnostic test routes
"""

import os
import sys
import datetime as datetime_

from flask import (
    Blueprint, request, redirect, url_for, session,
    jsonify, make_response, send_from_directory
)
from database.db import get_db
from middleware.auth import admin_required
from routes.shared import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, get_lang as _get_lang

utility_bp = Blueprint('utility', __name__)


def _set_lang(lang):
    if lang in SUPPORTED_LANGUAGES:
        session['lang'] = lang
        return True
    return False


# ==================== LANGUAGE SWITCHING ====================

@utility_bp.route('/set_lang/<lang>')
def set_language(lang):
    _set_lang(lang)
    next_page = request.referrer
    if next_page and next_page != request.url:
        return redirect(next_page)
    return redirect(url_for('customer.index'))


# ==================== HEALTH CHECKS ====================

@utility_bp.route('/health')
def health_check():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': datetime_.datetime.now().isoformat()
    })


@utility_bp.route('/health/details')
@admin_required
def health_check_details():
    from flask import current_app
    health_status = {
        'status': 'healthy',
        'timestamp': datetime_.datetime.now().isoformat(),
        'version': '2.0.0',
        'system': {'python_version': sys.version, 'platform': sys.platform},
        'services': {}
    }
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        health_status['services']['database'] = 'connected'
    except Exception as e:
        health_status['services']['database'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    try:
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        health_status['services']['storage'] = (
            'accessible' if os.path.exists(upload_dir) else 'not_found'
        )
    except Exception as e:
        health_status['services']['storage'] = f'error: {str(e)}'
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code


# ==================== SEO / CRAWLERS ====================

@utility_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


@utility_bp.route('/robots.txt')
def robots_txt():
    content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /login/
Disallow: /logout/
Disallow: /cart/clear/
Sitemap: https://semirafashion.com/sitemap.xml
"""
    return make_response(content, 200, {'Content-Type': 'text/plain'})


@utility_bp.route('/sitemap.xml')
def sitemap_xml():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, updated_at FROM products WHERE is_active = 1 ORDER BY id DESC"
        )
        products = cursor.fetchall()
        cursor.execute("SELECT id FROM categories WHERE is_active = 1")
        categories = cursor.fetchall()

        base_url = request.url_root.rstrip('/')
        current_date = datetime_.datetime.now().strftime('%Y-%m-%d')

        xml = '<%sxml version="1.0" encoding="UTF-8"%s>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for page in ['/', '/products', '/about', '/contact', '/branches',
                     '/faq', '/shipping-info', '/returns']:
            xml += (
                f'  <url>\n    <loc>{base_url}{page}</loc>\n'
                f'    <lastmod>{current_date}</lastmod>\n'
                f'    <changefreq>weekly</changefreq>\n'
                f'    <priority>0.8</priority>\n  </url>\n'
            )
        for cat in categories:
            xml += (
                f'  <url>\n    <loc>{base_url}/category/{cat[0]}</loc>\n'
                f'    <lastmod>{current_date}</lastmod>\n'
                f'    <changefreq>weekly</changefreq>\n'
                f'    <priority>0.7</priority>\n  </url>\n'
            )
        for prod in products:
            lastmod = str(prod[1]).split()[0] if prod[1] else current_date
            xml += (
                f'  <url>\n    <loc>{base_url}/product/{prod[0]}</loc>\n'
                f'    <lastmod>{lastmod}</lastmod>\n'
                f'    <changefreq>monthly</changefreq>\n'
                f'    <priority>0.9</priority>\n  </url>\n'
            )
        xml += '</urlset>'
        return make_response(xml, 200, {'Content-Type': 'application/xml'})
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Sitemap error: {str(e)}")
        return make_response('Error generating sitemap', 500)


# ==================== DIAGNOSTIC ====================

@utility_bp.route('/test-add/<int:product_id>', methods=['GET'])
def test_add_to_cart(product_id):
    """Diagnostic GET route — no JSON body, no CSRF, no stock gate."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name FROM products WHERE id = %s AND is_active = 1",
            (product_id,)
        )
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'error': f'Product {product_id} not found'}), 404
        if session.get('user_id'):
            cursor.execute(
                "SELECT id, quantity FROM cart_items WHERE user_id = %s AND product_id = %s",
                (session['user_id'], product_id)
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE cart_items SET quantity = %s WHERE id = %s",
                    (existing[1] + 1, existing[0])
                )
            else:
                cursor.execute(
                    "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                    (session['user_id'], product_id, 1)
                )
            conn.commit()
            source = 'database'
        else:
            cart = session.get('cart', {})
            cart[str(product_id)] = cart.get(str(product_id), 0) + 1
            session['cart'] = cart
            session.modified = True
            session.permanent = True
            source = 'session'
        return jsonify({
            'success': True,
            'product': product[1],
            'source': source,
            'cart': dict(session.get('cart', {}))
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
