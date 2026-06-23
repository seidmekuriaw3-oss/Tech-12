"""
Admin Routes for ኢትዮሳዳት ፈርኒቸር ወድ ሰሚራ

All admin panel routes: dashboard, products, ads, orders, users,
inbox, reports, settings, reviews, translations, notifications.
"""

from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, jsonify, make_response, send_from_directory, abort
)
from middleware.auth import admin_required
from database.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from routes.shared import get_lang, WHATSAPP_NUMBER
import os
import json
import uuid
import csv
from io import StringIO
import datetime as datetime_
from services.notification_service import (
    notify_user, notify_admin,
    get_admin_alerts, get_admin_unread_count, mark_admin_alerts_read
)

admin_bp = Blueprint('admin', __name__)


# ==================== ADMIN LOGIN ====================

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', '')

        if username == admin_username and password == admin_password:
            session['admin'] = True
            session['admin_username'] = username
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password!', 'danger')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
def admin_logout():
    session.pop('admin', None)
    session.pop('admin_username', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin.admin_login'))


# ==================== DASHBOARD ====================

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Single round-trip instead of 7 separate queries
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM products WHERE is_active = 1),
                (SELECT COUNT(*) FROM advertisements WHERE is_active = 1),
                (SELECT COUNT(*) FROM orders),
                (SELECT COUNT(*) FROM orders WHERE status = 'pending'),
                (SELECT COUNT(*) FROM users WHERE is_admin = 0),
                (SELECT COALESCE(SUM(total), 0) FROM orders WHERE status != 'cancelled'),
                (SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURRENT_DATE)
        """)
        _row = cursor.fetchone()
        products_count  = _row[0] or 0
        ads_count       = _row[1] or 0
        total_orders    = _row[2] or 0
        pending_orders  = _row[3] or 0
        customers_count = _row[4] or 0
        total_revenue   = _row[5] or 0
        today_orders    = _row[6] or 0

        cursor.execute("""
            SELECT o.*, u.full_name as customer_name
            FROM orders o LEFT JOIN users u ON o.user_id = u.id
            ORDER BY o.id DESC LIMIT 10
        """)
        recent_orders_rows = cursor.fetchall()
        recent_orders = [dict(o) for o in recent_orders_rows] if recent_orders_rows else []

        cursor.execute("""
            SELECT * FROM products
            WHERE stock_quantity <= low_stock_threshold AND stock_quantity > 0
            LIMIT 10
        """)
        low_stock_rows = cursor.fetchall()
        low_stock_products = [dict(p) for p in low_stock_rows] if low_stock_rows else []

        stats = {
            'products_count': products_count,
            'ads_count': ads_count,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'customers_count': customers_count,
            'total_revenue': total_revenue,
            'today_orders': today_orders
        }

        return render_template('admin/dashboard.html',
                               stats=stats, recent_orders=recent_orders,
                               low_stock_products=low_stock_products, lang=lang)
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('Error loading dashboard.', 'error')
        return render_template('admin/dashboard.html',
                               stats={}, recent_orders=[], low_stock_products=[], lang=lang)


# ==================== PRODUCT MANAGEMENT ====================

@admin_bp.route('/products')
@admin_required
def products():
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.id DESC
        """)
        products_rows = cursor.fetchall()
        return render_template('admin/products/index.html',
                               products=[dict(p) for p in products_rows] if products_rows else [],
                               lang=lang)
    except Exception as e:
        print(f"Admin products error: {e}")
        flash('Error loading products.', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/products/create', methods=['GET', 'POST'])
@admin_required
def product_create():
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, name_am FROM categories ORDER BY sort_order")
        categories = [dict(c) for c in cursor.fetchall()]

        if request.method == 'POST':
            name = request.form.get('name', '')
            name_am = request.form.get('name_am', '')
            name_ar = request.form.get('name_ar', '')
            name_en = request.form.get('name_en', '') or name
            description = request.form.get('description', '')
            description_am = request.form.get('description_am', '')
            description_ar = request.form.get('description_ar', '')
            description_en = request.form.get('description_en', '') or description
            price = float(request.form.get('price', 0) or 0)
            compare_price = request.form.get('compare_price')
            compare_price = float(compare_price) if compare_price else None
            stock_quantity = int(request.form.get('stock_quantity', 0) or 0)
            category_id = int(request.form.get('category_id', 0) or 0) or None
            material = request.form.get('material', '')
            color = request.form.get('color', '')
            sku = request.form.get('sku', '')
            is_featured = 1 if request.form.get('is_featured') else 0
            is_new = 1 if request.form.get('is_new') else 0

            from werkzeug.utils import secure_filename
            upload_dir = 'static/uploads/products'
            os.makedirs(upload_dir, exist_ok=True)

            _MAX_IMG_BYTES = 5 * 1024 * 1024  # 5 MB per image

            def save_upload(file_obj):
                file_obj.seek(0, os.SEEK_END)
                size = file_obj.tell()
                file_obj.seek(0)
                if size > _MAX_IMG_BYTES:
                    raise ValueError(f"'{file_obj.filename}' exceeds 5 MB limit")
                fname = secure_filename(file_obj.filename)
                ext = fname.rsplit('.', 1)[1].lower() if '.' in fname else 'jpg'
                unique = f"product_{uuid.uuid4().hex[:8]}.{ext}"
                file_obj.save(os.path.join(upload_dir, unique))
                return f'uploads/products/{unique}'

            image_filename = ''
            image = request.files.get('image')
            if image and image.filename:
                image_filename = save_upload(image)

            # Handle multiple extra gallery images
            extra_images = request.files.getlist('extra_images')
            gallery_paths = []
            for extra in extra_images:
                if extra and extra.filename:
                    gallery_paths.append(save_upload(extra))

            import json as _json
            images_json = _json.dumps(gallery_paths) if gallery_paths else None

            cursor.execute("""
                INSERT INTO products (
                    name, name_am, name_ar, name_en,
                    description, description_am, description_ar, description_en,
                    price, compare_price, stock_quantity, category_id,
                    material, color, sku, is_featured, is_new, thumbnail, images, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """, (name, name_am, name_ar, name_en,
                  description, description_am, description_ar, description_en,
                  price, compare_price, stock_quantity, category_id,
                  material, color, sku, is_featured, is_new, image_filename, images_json))
            conn.commit()
            flash('Product created successfully!', 'success')
            return redirect(url_for('admin.products'))

        return render_template('admin/products/create.html', categories=categories, lang=lang)
    except Exception as e:
        print(f"Product create error: {e}")
        flash(f'Error creating product: {e}', 'error')
        return redirect(url_for('admin.products'))


@admin_bp.route('/products/edit/<int:pid>', methods=['GET', 'POST'])
@admin_required
def product_edit(pid):
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = %s", (pid,))
        product = cursor.fetchone()
        if not product:
            flash('Product not found!', 'danger')
            return redirect(url_for('admin.products'))

        cursor.execute("SELECT id, name, name_am FROM categories ORDER BY sort_order")
        categories = [dict(c) for c in cursor.fetchall()]

        if request.method == 'POST':
            name = request.form.get('name', '')
            name_am = request.form.get('name_am', '')
            name_ar = request.form.get('name_ar', '')
            name_en = request.form.get('name_en', '') or name
            description = request.form.get('description', '')
            description_am = request.form.get('description_am', '')
            description_ar = request.form.get('description_ar', '')
            description_en = request.form.get('description_en', '') or description
            price = float(request.form.get('price', 0) or 0)
            compare_price = request.form.get('compare_price')
            compare_price = float(compare_price) if compare_price else None
            stock_quantity = int(request.form.get('stock_quantity', 0) or 0)
            category_id = int(request.form.get('category_id', 0) or 0) or None
            material = request.form.get('material', '')
            color = request.form.get('color', '')
            sku = request.form.get('sku', '')
            is_featured = 1 if request.form.get('is_featured') else 0
            is_new = 1 if request.form.get('is_new') else 0

            from werkzeug.utils import secure_filename
            import json as _json
            upload_dir = 'static/uploads/products'
            os.makedirs(upload_dir, exist_ok=True)

            _MAX_IMG_BYTES = 5 * 1024 * 1024  # 5 MB per image

            def save_upload(file_obj):
                file_obj.seek(0, os.SEEK_END)
                size = file_obj.tell()
                file_obj.seek(0)
                if size > _MAX_IMG_BYTES:
                    raise ValueError(f"'{file_obj.filename}' exceeds 5 MB limit")
                fname = secure_filename(file_obj.filename)
                ext = fname.rsplit('.', 1)[1].lower() if '.' in fname else 'jpg'
                unique = f"product_{uuid.uuid4().hex[:8]}.{ext}"
                file_obj.save(os.path.join(upload_dir, unique))
                return f'uploads/products/{unique}'

            def _normalize_img(path):
                """Normalise a stored image path to 'uploads/products/<file>'."""
                if not path:
                    return None
                path = path.strip()
                if path.startswith('static/'):
                    path = path[len('static/'):]
                if '/' not in path:
                    path = f'uploads/products/{path}'
                return path

            image_filename = _normalize_img(product['thumbnail']) or ''
            image = request.files.get('image')
            if image and image.filename:
                image_filename = save_upload(image)

            # Existing gallery images the user kept — normalise paths from legacy data
            keep_images_raw = request.form.get('keep_images', '')
            try:
                kept_raw = _json.loads(keep_images_raw) if keep_images_raw else []
                if not isinstance(kept_raw, list):
                    kept_raw = []
                kept = [_normalize_img(p) for p in kept_raw if p]
            except Exception:
                kept = []

            # New extra gallery images
            extra_images = request.files.getlist('extra_images')
            new_gallery = []
            for extra in extra_images:
                if extra and extra.filename:
                    new_gallery.append(save_upload(extra))

            all_gallery = kept + new_gallery
            images_json = _json.dumps(all_gallery) if all_gallery else None

            cursor.execute("""
                UPDATE products SET
                    name=%s, name_am=%s, name_ar=%s, name_en=%s,
                    description=%s, description_am=%s, description_ar=%s, description_en=%s,
                    price=%s, compare_price=%s, stock_quantity=%s, category_id=%s,
                    material=%s, color=%s, sku=%s, is_featured=%s, is_new=%s, thumbnail=%s, images=%s,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=%s
            """, (name, name_am, name_ar, name_en,
                  description, description_am, description_ar, description_en,
                  price, compare_price, stock_quantity, category_id,
                  material, color, sku, is_featured, is_new, image_filename, images_json, pid))
            conn.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin.products'))

        return render_template('admin/products/edit.html',
                               product=dict(product), categories=categories, lang=lang)
    except Exception as e:
        print(f"Product edit error: {e}")
        flash(f'Error editing product: {e}', 'error')
        return redirect(url_for('admin.products'))


@admin_bp.route('/products/delete/<int:pid>', methods=['GET', 'POST', 'DELETE'])
@admin_required
def product_delete(pid):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET is_active = 0 WHERE id = %s", (pid,))
        conn.commit()
        if request.method in ('DELETE', 'POST') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Product deleted successfully'})
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        print(f"Product delete error: {e}")
        if request.method in ('DELETE', 'POST') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error deleting product.', 'error')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/duplicate/<int:pid>', methods=['GET', 'POST'])
@admin_required
def product_duplicate(pid):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = %s", (pid,))
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        p = dict(product)
        new_name = f"Copy of {p.get('name', '')}"
        new_name_am = f"ቅጂ - {p.get('name_am', '')}" if p.get('name_am') else new_name

        # Generate a guaranteed-unique SKU by appending a short random suffix
        import random, string
        base_sku = p.get('sku') or str(pid)
        while True:
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            new_sku = f"COPY-{base_sku}-{suffix}"
            cursor.execute("SELECT id FROM products WHERE sku = %s", (new_sku,))
            if not cursor.fetchone():
                break

        cursor.execute("""
            INSERT INTO products (
                name, name_am, name_ar, name_en,
                description, description_am, description_ar, description_en,
                price, compare_price, stock_quantity, category_id,
                material, color, sku, is_featured, is_new, thumbnail, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
            RETURNING id
        """, (
            new_name, new_name_am, p.get('name_ar'), p.get('name_en'),
            p.get('description'), p.get('description_am'), p.get('description_ar'), p.get('description_en'),
            p.get('price'), p.get('compare_price'), p.get('stock_quantity'), p.get('category_id'),
            p.get('material'), p.get('color'), new_sku,
            p.get('is_featured', 0), p.get('is_new', 0), p.get('thumbnail')
        ))
        row = cursor.fetchone()
        new_id = row[0] if row else None
        conn.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Product duplicated successfully', 'new_id': new_id})
        flash('Product duplicated successfully!', 'success')
        return redirect(url_for('admin.products'))
    except Exception as e:
        print(f"Product duplicate error: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error duplicating product.', 'error')
        return redirect(url_for('admin.products'))


@admin_bp.route('/products/toggle-featured/<int:pid>', methods=['POST'])
@admin_required
def product_toggle_featured(pid):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT is_featured FROM products WHERE id = %s", (pid,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        new_state = 0 if row[0] else 1
        cursor.execute("UPDATE products SET is_featured = %s WHERE id = %s", (new_state, pid))
        conn.commit()
        return jsonify({'success': True, 'is_featured': bool(new_state)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/products/update-stock/<int:pid>', methods=['POST'])
@admin_required
def product_update_stock(pid):
    try:
        data = request.get_json()
        stock_quantity = int(data.get('stock_quantity', 0))
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET stock_quantity = %s WHERE id = %s", (stock_quantity, pid))
        conn.commit()
        return jsonify({'success': True, 'stock_quantity': stock_quantity})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/products/bulk-delete', methods=['POST'])
@admin_required
def bulk_delete_products():
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return jsonify({'success': False, 'error': 'No products selected'}), 400

        conn = get_db()
        cursor = conn.cursor()
        placeholders = ','.join(['%s'] * len(ids))
        cursor.execute(f"SELECT id, thumbnail FROM products WHERE id IN ({placeholders})", ids)
        products_rows = cursor.fetchall()

        for prod in products_rows:
            thumb = prod[1] or ''
            if thumb:
                static_path = os.path.join('static', thumb.lstrip('/'))
                if os.path.exists(static_path):
                    try:
                        os.remove(static_path)
                    except Exception:
                        pass

        cursor.execute(f"DELETE FROM products WHERE id IN ({placeholders})", ids)
        conn.commit()
        return jsonify({'success': True, 'deleted': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/products/export')
@admin_required
def export_products():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.name_am, p.name_ar, p.price, p.compare_price,
                   p.stock_quantity, c.name as category_name, p.is_featured, p.created_at
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1 ORDER BY p.id DESC
        """)
        products_rows = cursor.fetchall()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name (EN)', 'Name (AM)', 'Name (AR)', 'Price', 'Compare Price',
                         'Stock', 'Category', 'Featured', 'Created Date'])
        for p in products_rows:
            writer.writerow([
                p['id'], p['name'] or '', p['name_am'] or '', p['name_ar'] or '',
                p['price'], p['compare_price'] or '', p['stock_quantity'],
                p['category_name'] or '', 'Yes' if p['is_featured'] else 'No', p['created_at']
            ])

        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = (
            f'attachment; filename=products_export_{datetime_.datetime.now().strftime("%Y%m%d")}.csv'
        )
        return response
    except Exception as e:
        print(f"Export products error: {e}")
        flash('Error exporting products', 'error')
        return redirect(url_for('admin.products'))


@admin_bp.route('/products/import/sample')
@admin_required
def import_products_sample():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['name_en', 'name_am', 'name_ar', 'price', 'compare_price', 'stock',
                     'category', 'description_en', 'description_am', 'featured', 'is_new',
                     'sku', 'image_url'])
    writer.writerow(['Luxury Sofa', 'ቅርጫ ሶፋ', 'صوفا فاخرة', '15000', '20000', '10',
                     'Sofa', 'Premium quality sofa', 'ከፍተኛ ጥራት ያለው ሶፋ', 'yes', 'yes',
                     'SKU-001', 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc%sw=400'])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=products_import_sample.csv'
    return response


@admin_bp.route('/products/import', methods=['GET', 'POST'])
@admin_required
def import_products():
    lang = get_lang()
    import secrets as _sec
    if 'import_csrf' not in session:
        session['import_csrf'] = _sec.token_hex(32)
    csrf_token = session['import_csrf']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, name_am FROM categories WHERE is_active = 1 ORDER BY sort_order")
    categories_list = [dict(c) for c in cursor.fetchall()]

    cat_lookup = {}
    for c in categories_list:
        cat_lookup[str(c['id'])] = c['id']
        if c.get('name_am'):
            cat_lookup[c['name_am'].strip().lower()] = c['id']
        if c.get('name'):
            cat_lookup[c['name'].strip().lower()] = c['id']

    if request.method == 'GET':
        return render_template('admin/products/import.html',
                               categories=categories_list, csrf_token=csrf_token, lang=lang)

    submitted_token = request.form.get('csrf_token', '')
    if submitted_token != session.get('import_csrf', ''):
        flash('Invalid or expired security token. Please try again.', 'error')
        return redirect(url_for('admin.import_products'))
    session.pop('import_csrf', None)

    csv_file = request.files.get('csv_file')
    if not csv_file or csv_file.filename == '':
        flash('Please select a CSV file to upload.', 'error')
        return redirect(url_for('admin.import_products'))
    if not csv_file.filename.lower().endswith('.csv'):
        flash('Invalid file type. Please upload a .csv file.', 'error')
        return redirect(url_for('admin.import_products'))

    try:
        raw = csv_file.read()
        try:
            content = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            content = raw.decode('latin-1')
    except Exception:
        flash('Could not read the uploaded file.', 'error')
        return redirect(url_for('admin.import_products'))

    reader = csv.DictReader(StringIO(content))
    if reader.fieldnames is None:
        flash('The CSV file appears to be empty.', 'error')
        return redirect(url_for('admin.import_products'))

    headers_norm = {h.strip().lower() for h in reader.fieldnames}
    REQUIRED = {'name_en', 'price', 'category'}
    missing_cols = REQUIRED - headers_norm
    if missing_cols:
        flash(f'Missing required columns: {", ".join(sorted(missing_cols))}.', 'error')
        return redirect(url_for('admin.import_products'))

    reader.fieldnames = [h.strip() for h in reader.fieldnames]
    upload_dir = 'static/uploads/products'
    os.makedirs(upload_dir, exist_ok=True)

    validated_rows = []
    row_errors = []

    def _bool_field(val):
        return 1 if val.strip().lower() in ('yes', '1', 'true') else 0

    for row_num, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): (v or '').strip() for k, v in raw_row.items() if k}

        name_en = row.get('name_en', '')
        if not name_en:
            row_errors.append({'row': row_num, 'field': 'name_en', 'message': '"name_en" is required.'})
            continue

        price_raw = row.get('price', '')
        try:
            price = float(price_raw)
            if price <= 0:
                raise ValueError
        except (ValueError, TypeError):
            row_errors.append({'row': row_num, 'field': 'price',
                               'message': f'Must be a positive number (got "{price_raw}").'})
            continue

        compare_price_raw = row.get('compare_price', '')
        compare_price = None
        if compare_price_raw:
            try:
                compare_price = float(compare_price_raw)
            except (ValueError, TypeError):
                row_errors.append({'row': row_num, 'field': 'compare_price',
                                   'message': f'Must be a number (got "{compare_price_raw}").'})
                continue

        stock_raw = row.get('stock', '').strip()
        try:
            stock = int(float(stock_raw)) if stock_raw else 99
        except (ValueError, TypeError):
            stock = 99

        category_raw = row.get('category', '').strip()
        category_id = cat_lookup.get(category_raw.lower()) or cat_lookup.get(category_raw)
        if category_id is None:
            row_errors.append({'row': row_num, 'field': 'category',
                               'message': f'Unknown category "{category_raw}".'})
            continue

        validated_rows.append({
            'name': name_en,
            'name_en': name_en,
            'name_am': row.get('name_am', ''),
            'name_ar': row.get('name_ar', ''),
            'price': price,
            'compare_price': compare_price,
            'stock_quantity': stock,
            'category_id': category_id,
            'description': row.get('description_en', ''),
            'description_en': row.get('description_en', ''),
            'description_am': row.get('description_am', ''),
            'sku': row.get('sku', ''),
            'is_featured': _bool_field(row.get('featured', '0')),
            'is_new': _bool_field(row.get('is_new', '0')),
            'image_url': row.get('image_url', '').strip(),
        })

    if row_errors and not validated_rows:
        flash(f'No valid rows found. {len(row_errors)} error(s) detected.', 'error')
        return render_template('admin/products/import.html',
                               categories=categories_list, csrf_token=csrf_token,
                               row_errors=row_errors, lang=lang)

    imported = 0
    for vrow in validated_rows:
        thumbnail = ''
        if vrow['image_url']:
            try:
                import requests as _req
                resp = _req.get(vrow['image_url'], timeout=10, stream=True)
                if resp.status_code == 200:
                    ct = resp.headers.get('Content-Type', '').split(';')[0].strip()
                    ext_map = {'image/jpeg': 'jpg', 'image/png': 'png',
                               'image/webp': 'webp', 'image/gif': 'gif'}
                    ext = ext_map.get(ct, 'jpg')
                    fname = f"import_{uuid.uuid4().hex}.{ext}"
                    with open(os.path.join(upload_dir, fname), 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            f.write(chunk)
                    thumbnail = f'uploads/products/{fname}'
            except Exception:
                pass

        try:
            cursor.execute("""
                INSERT INTO products (
                    name, name_en, name_am, name_ar,
                    description, description_en, description_am,
                    price, compare_price, stock_quantity, category_id,
                    sku, is_featured, is_new, thumbnail, is_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """, (vrow['name'], vrow['name_en'], vrow['name_am'], vrow['name_ar'],
                  vrow['description'], vrow['description_en'], vrow['description_am'],
                  vrow['price'], vrow['compare_price'], vrow['stock_quantity'], vrow['category_id'],
                  vrow['sku'], vrow['is_featured'], vrow['is_new'], thumbnail))
            imported += 1
        except Exception as e:
            print(f"Import row error: {e}")

    conn.commit()
    flash(f'Successfully imported {imported} product(s). {len(row_errors)} row(s) skipped.', 'success')
    return redirect(url_for('admin.products'))


# ==================== ADVERTISEMENT MANAGEMENT ====================

@admin_bp.route('/ads')
@admin_required
def ads():
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM advertisements ORDER BY sort_order ASC, id DESC")
        ads_list = cursor.fetchall()
        return render_template('admin/ads/index.html',
                               ads=[dict(a) for a in ads_list] if ads_list else [], lang=lang)
    except Exception as e:
        print(f"Admin ads error: {e}")
        flash('Error loading ads.', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/ads/create', methods=['GET', 'POST'])
@admin_required
def ad_create():
    if request.method == 'POST':
        title = request.form.get('title', '')
        title_am = request.form.get('title_am', '')
        title_ar = request.form.get('title_ar', '')
        description = request.form.get('description', '')
        description_am = request.form.get('description_am', '')
        description_ar = request.form.get('description_ar', '')
        link = request.form.get('link', '')
        sort_order = int(request.form.get('sort_order', 0) or 0)

        image_filename = ''
        image = request.files.get('image')
        if image and image.filename:
            from werkzeug.utils import secure_filename
            filename = secure_filename(image.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
            unique_filename = f"ad_{uuid.uuid4().hex[:8]}.{ext}"
            upload_dir = 'static/uploads/ads'
            os.makedirs(upload_dir, exist_ok=True)
            image.save(os.path.join(upload_dir, unique_filename))
            image_filename = f'uploads/ads/{unique_filename}'

        media_url = request.form.get('media_url', '').strip()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO advertisements (
                title, title_am, title_ar, description, description_am, description_ar,
                image, media_url, link, sort_order, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
        """, (title, title_am, title_ar, description, description_am, description_ar,
              image_filename, media_url, link, sort_order))
        conn.commit()
        flash('Advertisement created successfully!', 'success')
        return redirect(url_for('admin.ads'))

    return render_template('admin/ads/create.html')


@admin_bp.route('/ads/edit/<int:aid>', methods=['GET', 'POST'])
@admin_required
def ad_edit(aid):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM advertisements WHERE id = %s", (aid,))
    ad = cursor.fetchone()
    if not ad:
        flash('Advertisement not found!', 'danger')
        return redirect(url_for('admin.ads'))

    if request.method == 'POST':
        title = request.form.get('title', '')
        title_am = request.form.get('title_am', '')
        title_ar = request.form.get('title_ar', '')
        description = request.form.get('description', '')
        description_am = request.form.get('description_am', '')
        description_ar = request.form.get('description_ar', '')
        link = request.form.get('link', '')
        sort_order = int(request.form.get('sort_order', 0) or 0)

        image_filename = ad['image']
        image = request.files.get('image')
        if image and image.filename:
            from werkzeug.utils import secure_filename
            filename = secure_filename(image.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
            unique_filename = f"ad_{uuid.uuid4().hex[:8]}.{ext}"
            upload_dir = 'static/uploads/ads'
            os.makedirs(upload_dir, exist_ok=True)
            image.save(os.path.join(upload_dir, unique_filename))
            image_filename = f'uploads/ads/{unique_filename}'

        media_url = request.form.get('media_url', ad.get('media_url', '') or '').strip()

        cursor.execute("""
            UPDATE advertisements SET
                title=%s, title_am=%s, title_ar=%s, description=%s, description_am=%s, description_ar=%s,
                image=%s, media_url=%s, link=%s, sort_order=%s
            WHERE id=%s
        """, (title, title_am, title_ar, description, description_am, description_ar,
              image_filename, media_url, link, sort_order, aid))
        conn.commit()
        flash('Advertisement updated successfully!', 'success')
        return redirect(url_for('admin.ads'))

    return render_template('admin/ads/edit.html', ad=dict(ad))


@admin_bp.route('/ads/toggle/<int:aid>')
@admin_required
def ad_toggle(aid):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE advertisements SET is_active = NOT is_active WHERE id = %s", (aid,))
        conn.commit()
        flash('Advertisement status toggled!', 'success')
    except Exception as e:
        print(f"Ad toggle error: {e}")
        flash('Error toggling ad.', 'error')
    return redirect(url_for('admin.ads'))


@admin_bp.route('/ads/delete/<int:aid>', methods=['GET', 'POST', 'DELETE'])
@admin_required
def ad_delete(aid):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM advertisements WHERE id = %s", (aid,))
        conn.commit()
        if request.method in ('DELETE', 'POST') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Advertisement deleted successfully'})
        flash('Advertisement deleted successfully!', 'success')
    except Exception as e:
        print(f"Ad delete error: {e}")
        if request.method in ('DELETE', 'POST') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error deleting ad.', 'error')
    return redirect(url_for('admin.ads'))


@admin_bp.route('/ads/reorder', methods=['POST'])
@admin_required
def ad_reorder():
    try:
        data = request.get_json()
        src_id = data.get('src_id')
        dest_id = data.get('dest_id')
        if not src_id or not dest_id:
            return jsonify({'success': False, 'error': 'Invalid request'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT sort_order FROM advertisements WHERE id = %s", (src_id,))
        src_order = cursor.fetchone()
        cursor.execute("SELECT sort_order FROM advertisements WHERE id = %s", (dest_id,))
        dest_order = cursor.fetchone()
        if src_order and dest_order:
            cursor.execute("UPDATE advertisements SET sort_order = %s WHERE id = %s", (dest_order[0], src_id))
            cursor.execute("UPDATE advertisements SET sort_order = %s WHERE id = %s", (src_order[0], dest_id))
            conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ORDER MANAGEMENT ====================

@admin_bp.route('/orders')
@admin_required
def orders():
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()

        status = request.args.get('status', 'all')
        search = request.args.get('search', '').strip()

        query = """
            SELECT o.*, u.full_name as customer_name
            FROM orders o LEFT JOIN users u ON o.user_id = u.id WHERE 1=1
        """
        params = []
        if status != 'all':
            query += " AND o.status = %s"
            params.append(status)
        if search:
            query += " AND (o.order_number LIKE %s OR u.full_name LIKE %s OR o.shipping_phone LIKE %s)"
            s = f'%{search}%'
            params.extend([s, s, s])
        query += " ORDER BY o.id DESC"

        cursor.execute(query, params)
        orders_rows = cursor.fetchall()
        orders_list = [dict(o) for o in orders_rows] if orders_rows else []

        cursor.execute("SELECT status, COUNT(*) as count FROM orders GROUP BY status")
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

        return render_template('admin/orders/index.html',
                               orders=orders_list, status_counts=status_counts,
                               current_status=status, search=search, lang=lang)
    except Exception as e:
        print(f"Admin orders error: {e}")
        flash('Error loading orders.', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/orders/<int:oid>')
@admin_required
def order_detail(oid):
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT o.*, u.full_name, u.email, u.phone
            FROM orders o LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = %s
        """, (oid,))
        order = cursor.fetchone()
        if not order:
            flash('Order not found!', 'danger')
            return redirect(url_for('admin.orders'))

        cursor.execute("""
            SELECT oi.*, p.name, p.name_am, p.name_ar, p.thumbnail
            FROM order_items oi JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (oid,))
        items = cursor.fetchall()

        return render_template('admin/orders/detail.html',
                               order=dict(order),
                               order_items=[dict(i) for i in items] if items else [],
                               lang=lang)
    except Exception as e:
        print(f"Order detail error: {e}")
        flash('Error loading order details.', 'error')
        return redirect(url_for('admin.orders'))


@admin_bp.route('/orders/update/<int:oid>', methods=['POST'])
@admin_required
def order_update_status(oid):
    try:
        status = request.form.get('status', 'pending')
        valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
        if status not in valid_statuses:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT status, user_id, total, order_number FROM orders WHERE id = %s", (oid,))
        prev = cursor.fetchone()
        prev_status   = prev[0] if prev else None
        user_id       = prev[1] if prev else None
        order_total   = float(prev[2]) if prev and prev[2] else 0
        order_number  = prev[3] if prev else str(oid)

        cursor.execute("UPDATE orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                       (status, oid))

        if status == 'delivered' and prev_status != 'delivered' and user_id:
            points_earned = max(1, int(order_total // 100))
            cursor.execute(
                "UPDATE users SET loyalty_points = COALESCE(loyalty_points, 0) + %s WHERE id = %s",
                (points_earned, user_id)
            )
            cursor.execute(
                "INSERT INTO loyalty_transactions (user_id, order_id, points, type, description) VALUES (%s, %s, %s, 'earn', %s)",
                (user_id, oid, points_earned, f'Points earned for order #{oid}')
            )

        conn.commit()

        status_icons = {
            'confirmed':  '✅', 'processing': '⚙️', 'shipped': '🚚',
            'delivered':  '🎉', 'cancelled':  '❌', 'pending': '⏳'
        }
        status_msgs = {
            'confirmed':  'Your order has been confirmed and is being prepared.',
            'processing': 'Your order is being processed by our team.',
            'shipped':    'Your order is on its way! Expect delivery soon.',
            'delivered':  f'Your order has been delivered! You earned {max(1,int(order_total//100)) if order_total else 1} loyalty points.',
            'cancelled':  'Your order has been cancelled. Contact us if you have questions.',
            'pending':    'Your order is pending review.',
        }
        if user_id and prev_status != status:
            try:
                icon = status_icons.get(status, '📦')
                msg  = status_msgs.get(status, f'Order status updated to {status}.')
                notify_user(
                    user_id,
                    f'{icon} Order #{order_number} — {status.title()}',
                    msg,
                    type='order',
                    link=f'/track-order/{order_number}'
                )
            except Exception:
                pass

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'status': status})

        flash(f'Order status updated to {status}!', 'success')
        return redirect(url_for('admin.order_detail', oid=oid))
    except Exception as e:
        print(f"Order update error: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Error updating order status.', 'error')
        return redirect(url_for('admin.order_detail', oid=oid))


@admin_bp.route('/orders/delete/<int:oid>')
@admin_required
def delete_order(oid):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM order_items WHERE order_id = %s", (oid,))
        cursor.execute("DELETE FROM orders WHERE id = %s", (oid,))
        conn.commit()
        flash('Order deleted successfully!', 'success')
    except Exception as e:
        print(f"Delete order error: {e}")
        flash('Error deleting order.', 'error')
    return redirect(url_for('admin.orders'))


@admin_bp.route('/orders/export/<int:oid>')
@admin_required
def export_order(oid):
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT o.*, u.full_name, u.email, u.phone
            FROM orders o LEFT JOIN users u ON o.user_id = u.id WHERE o.id = %s
        """, (oid,))
        order = cursor.fetchone()
        if not order:
            flash('Order not found!', 'danger')
            return redirect(url_for('admin.orders'))

        cursor.execute("""
            SELECT oi.*, p.name, p.name_am, p.name_ar
            FROM order_items oi JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (oid,))
        items = cursor.fetchall()

        export_data = {
            'order': dict(order),
            'items': [dict(i) for i in items]
        }
        response = make_response(json.dumps(export_data, indent=2, default=str))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = (
            f'attachment; filename=order_{oid}_{datetime_.datetime.now().strftime("%Y%m%d")}.json'
        )
        return response
    except Exception as e:
        print(f"Export order error: {e}")
        flash('Error exporting order.', 'error')
        return redirect(url_for('admin.orders'))


@admin_bp.route('/orders/invoice/<int:oid>')
@admin_required
def order_invoice(oid):
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM orders WHERE id = %s", (oid,))
        order = cursor.fetchone()
        if not order:
            flash('Order not found!', 'danger')
            return redirect(url_for('admin.orders'))

        cursor.execute("""
            SELECT oi.*, p.name, p.name_am, p.name_ar
            FROM order_items oi JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (oid,))
        items = cursor.fetchall()

        rows_html = ''.join(
            f"<tr><td>{item['name_am'] or item['name']}</td>"
            f"<td>{item['quantity']}</td>"
            f"<td>{item['price_at_time']:.2f} ETB</td>"
            f"<td>{item['price_at_time'] * item['quantity']:.2f} ETB</td></tr>"
            for item in items
        )

        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Invoice #{order['order_number']}</title>
<style>
body{{font-family:Arial,sans-serif;margin:40px}}
.header{{text-align:center;margin-bottom:30px}}
.invoice-title{{font-size:28px;color:#1a73e8}}
table{{width:100%;border-collapse:collapse;margin:20px 0}}
th,td{{border:1px solid #ddd;padding:10px;text-align:left}}
th{{background:#1a73e8;color:white}}
.total{{font-size:18px;font-weight:bold;text-align:right}}
.footer{{margin-top:40px;text-align:center;font-size:12px;color:#666}}
</style></head>
<body>
<div class="header">
  <h1 class="invoice-title">ኢትዮሳዳት ፈርኒቸር ወድ ሰሚራ</h1>
  <h2>INVOICE</h2>
</div>
<p><strong>Order #:</strong> {order['order_number']}</p>
<p><strong>Date:</strong> {order['created_at']}</p>
<p><strong>Status:</strong> {order['status']}</p>
<table>
<thead><tr><th>Product</th><th>Quantity</th><th>Price</th><th>Total</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>
<div class="total">
  <p>Subtotal: {order['subtotal']:.2f} ETB</p>
  <p>Discount: {order.get('discount', 0) or 0:.2f} ETB</p>
  <p>Shipping: {order.get('shipping_fee', 0) or 0:.2f} ETB</p>
  <p><strong>Total: {order['total']:.2f} ETB</strong></p>
</div>
<div class="footer">
  <p>Thank you for shopping with ኢትዮሳዳት ፈርኒቸር ወድ ሰሚራ!</p>
  <p>ወሎ ደሴ ኩታበር, Ethiopia | +251 90 602 0606</p>
</div>
</body></html>"""
        return html
    except Exception as e:
        print(f"Invoice error: {e}")
        flash('Error generating invoice.', 'error')
        return redirect(url_for('admin.order_detail', oid=oid))


# ==================== USER MANAGEMENT ====================

@admin_bp.route('/users')
@admin_required
def admin_users():
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, full_name, phone, is_admin, is_active, created_at, last_login
            FROM users ORDER BY created_at DESC
        """)
        users = [dict(u) for u in cursor.fetchall()]
        return render_template('admin/users/index.html', users=users, lang=lang)
    except Exception as e:
        print(f"Admin users error: {e}")
        flash('Error loading users.', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/toggle/<int:uid>', methods=['POST'])
@admin_required
def toggle_user(uid):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT is_active, is_admin FROM users WHERE id = %s", (uid,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        if user['is_admin']:
            return jsonify({'success': False, 'error': 'Cannot deactivate admin accounts'}), 403
        new_status = 0 if user['is_active'] else 1
        cursor.execute("UPDATE users SET is_active = %s WHERE id = %s", (new_status, uid))
        conn.commit()
        return jsonify({'success': True, 'is_active': new_status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/delete/<int:uid>', methods=['POST'])
@admin_required
def delete_user(uid):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE id = %s", (uid,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        if user['is_admin']:
            return jsonify({'success': False, 'error': 'Cannot delete admin accounts'}), 403
        cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (uid,))
        cursor.execute("DELETE FROM users WHERE id = %s", (uid,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== INBOX ====================

@admin_bp.route('/inbox')
@admin_required
def admin_inbox():
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()

        filter_status = request.args.get('filter', 'all')
        search = request.args.get('search', '').strip()

        query = "SELECT * FROM contact_messages WHERE 1=1"
        params = []
        if filter_status == 'unread':
            query += " AND is_read = 0"
        elif filter_status == 'read':
            query += " AND is_read = 1"
        if search:
            query += " AND (name ILIKE %s OR email ILIKE %s OR phone ILIKE %s OR message ILIKE %s)"
            s = f'%{search}%'
            params.extend([s, s, s, s])
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        messages = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) FROM contact_messages WHERE is_read = 0")
        unread_count = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM contact_messages")
        total_count = cursor.fetchone()[0] or 0

        return render_template('admin/inbox/index.html',
                               messages=messages, filter_status=filter_status,
                               search=search, unread_count=unread_count,
                               total_count=total_count, lang=lang)
    except Exception as e:
        print(f"Admin inbox error: {e}")
        flash('Error loading inbox.', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/inbox/<int:mid>/mark-read', methods=['POST'])
@admin_required
def inbox_mark_read(mid):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT is_read FROM contact_messages WHERE id = %s", (mid,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Message not found'}), 404
        new_status = 0 if row['is_read'] else 1
        cursor.execute("UPDATE contact_messages SET is_read = %s WHERE id = %s", (new_status, mid))
        conn.commit()
        return jsonify({'success': True, 'is_read': new_status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/inbox/mark-all-read', methods=['POST'])
@admin_required
def inbox_mark_all_read():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE contact_messages SET is_read = 1 WHERE is_read = 0")
        conn.commit()
        count = cursor.rowcount
        return jsonify({'success': True, 'updated': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/inbox/<int:mid>/delete', methods=['POST'])
@admin_required
def inbox_delete(mid):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contact_messages WHERE id = %s", (mid,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Message not found'}), 404
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/inbox/<int:mid>/note', methods=['POST'])
@admin_required
def inbox_save_note(mid):
    try:
        data = request.get_json(silent=True) or {}
        note = data.get('note', '').strip()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM contact_messages WHERE id = %s", (mid,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Message not found'}), 404
        cursor.execute("UPDATE contact_messages SET admin_notes = %s WHERE id = %s",
                       (note if note else None, mid))
        conn.commit()
        return jsonify({'success': True, 'note': note})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== REPORTS ====================

@admin_bp.route('/reports')
@admin_required
def reports():
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
        total_products = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0")
        total_customers = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(total) FROM orders WHERE status = 'delivered'")
        total_revenue = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
        pending_orders = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'delivered'")
        completed_orders = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT c.id, c.name_am, c.name, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON p.category_id = c.id AND p.is_active = 1
            WHERE c.is_active = 1 GROUP BY c.id, c.name_am, c.name
            ORDER BY product_count DESC
        """)
        categories = [dict(c) for c in cursor.fetchall()]

        cursor.execute("""
            SELECT TO_CHAR(created_at, 'YYYY-MM') as month,
                   COUNT(*) as order_count, SUM(total) as revenue
            FROM orders WHERE status != 'cancelled'
            AND created_at >= NOW() - INTERVAL '12 months'
            GROUP BY TO_CHAR(created_at, 'YYYY-MM')
            ORDER BY month DESC
        """)
        monthly_sales = [dict(s) for s in cursor.fetchall()]

        cursor.execute("""
            SELECT p.id, p.name_am, p.name, SUM(oi.quantity) as total_sold,
                   SUM(oi.quantity * oi.price_at_time) as revenue
            FROM order_items oi JOIN products p ON oi.product_id = p.id
            GROUP BY p.id, p.name_am, p.name
            ORDER BY total_sold DESC LIMIT 10
        """)
        top_products = [dict(p) for p in cursor.fetchall()]

        cursor.execute("""
            SELECT p.id, p.name_am, p.name, p.stock_quantity, p.low_stock_threshold
            FROM products p
            WHERE p.stock_quantity <= p.low_stock_threshold AND p.stock_quantity > 0
            ORDER BY p.stock_quantity ASC LIMIT 10
        """)
        low_stock = [dict(p) for p in cursor.fetchall()]

        stats = {
            'total_products': total_products, 'total_orders': total_orders,
            'total_customers': total_customers, 'total_revenue': total_revenue,
            'pending_orders': pending_orders, 'completed_orders': completed_orders
        }

        return render_template('admin/reports/index.html',
                               stats=stats, categories=categories,
                               monthly_sales=monthly_sales, top_products=top_products,
                               low_stock=low_stock,
                               total_products=total_products, total_orders=total_orders,
                               total_revenue=total_revenue, total_customers=total_customers,
                               pending_orders=pending_orders, completed_orders=completed_orders,
                               lang=lang)
    except Exception as e:
        print(f"Reports error: {e}")
        import traceback; print(traceback.format_exc())
        flash('Error loading reports.', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/reports/sales')
@admin_required
def reports_sales():
    lang = get_lang()
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    try:
        conn = get_db()
        cursor = conn.cursor()

        query = """
            SELECT o.*, u.full_name
            FROM orders o LEFT JOIN users u ON o.user_id = u.id
            WHERE o.status != 'cancelled'
        """
        params = []
        if start_date:
            query += " AND DATE(o.created_at) >= %s"
            params.append(start_date)
        if end_date:
            query += " AND DATE(o.created_at) <= %s"
            params.append(end_date)
        query += " ORDER BY o.created_at DESC"
        cursor.execute(query, params)
        orders_rows = cursor.fetchall()

        orders_list = []
        total_revenue = 0
        for o in orders_rows:
            od = dict(o)
            od['customer_name'] = od.pop('full_name', None) or 'Guest'
            od['date'] = (od.get('created_at') or '')[:10]
            total_revenue += od.get('total', 0) or 0
            orders_list.append(od)

        total_orders = len(orders_list)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as order_count, SUM(total) as revenue
            FROM orders WHERE status != 'cancelled'
            GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 30
        """)
        daily_sales = [dict(s) for s in cursor.fetchall()]
        chart_labels = [s.get('date', '') for s in daily_sales]
        chart_values = [s.get('revenue') or 0 for s in daily_sales]

        cursor.execute("""
            SELECT p.id, p.name_am as name, c.name_am as category,
                   COALESCE(SUM(oi.quantity), 0) as units_sold,
                   COALESCE(SUM(oi.quantity * oi.price_at_time), 0) as revenue
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN order_items oi ON p.id = oi.product_id
            GROUP BY p.id, p.name_am, c.name_am
            ORDER BY units_sold DESC LIMIT 10
        """)
        top_products = [dict(p) for p in cursor.fetchall()]

        return render_template('admin/reports/sales.html',
                               orders=orders_list, total_revenue=total_revenue,
                               total_orders=total_orders,
                               avg_order_value=round(avg_order_value, 2),
                               daily_sales=daily_sales, top_products=top_products,
                               chart_labels=chart_labels, chart_values=chart_values,
                               start_date=start_date, end_date=end_date, lang=lang)
    except Exception as e:
        print(f"Reports sales error: {e}")
        flash('Error loading sales report.', 'error')
        return redirect(url_for('admin.reports'))


@admin_bp.route('/reports/products')
@admin_required
def reports_products():
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.id, p.name_am, p.name, p.name_ar, p.price, p.compare_price,
                   p.stock_quantity, p.low_stock_threshold, p.is_featured,
                   p.thumbnail, p.created_at, c.name as category_name,
                   COALESCE(SUM(oi.quantity), 0) as total_sold,
                   COALESCE(SUM(oi.quantity * oi.price_at_time), 0) as total_revenue
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN order_items oi ON p.id = oi.product_id
            WHERE p.is_active = 1
            GROUP BY p.id, p.name_am, p.name, p.name_ar, p.price, p.compare_price,
                     p.stock_quantity, p.low_stock_threshold, p.is_featured,
                     p.thumbnail, p.created_at, c.name
            ORDER BY total_sold DESC, p.id DESC
        """)
        products_rows = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) as total_products,
                   SUM(stock_quantity) as total_stock,
                   SUM(CASE WHEN stock_quantity = 0 THEN 1 ELSE 0 END) as out_of_stock,
                   SUM(CASE WHEN stock_quantity <= low_stock_threshold AND stock_quantity > 0 THEN 1 ELSE 0 END) as low_stock,
                   AVG(price) as avg_price,
                   SUM(price * stock_quantity) as total_value
            FROM products WHERE is_active = 1
        """)
        stats_row = cursor.fetchone()
        stats_dict = dict(stats_row) if stats_row else {}

        cursor.execute("""
            SELECT c.id, c.name_am, c.name, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON p.category_id = c.id AND p.is_active = 1
            WHERE c.is_active = 1 GROUP BY c.id, c.name_am, c.name
            ORDER BY c.name_am ASC
        """)
        categories = [dict(c) for c in cursor.fetchall()]

        return render_template('admin/reports/products.html',
                               products=[dict(p) for p in products_rows] if products_rows else [],
                               stats=stats_dict, categories=categories,
                               total_products=stats_dict.get('total_products', 0),
                               total_value=stats_dict.get('total_value', 0),
                               lang=lang)
    except Exception as e:
        print(f"Reports products error: {e}")
        flash('Error loading products report.', 'error')
        return redirect(url_for('admin.reports'))


# ==================== SETTINGS ====================

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    lang = get_lang()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings_rows = cursor.fetchall()
    settings_data = {row[0]: row[1] for row in settings_rows}

    if request.method == 'POST':
        try:
            settings_to_save = [
                ('site_name', request.form.get('site_name', 'ኢትዮሳዳት ፈርኒቸር ወድ ሰሚራ')),
                ('site_description', request.form.get('site_description', '')),
                ('admin_email', request.form.get('admin_email', 'admin@ethiosadat.com')),
                ('whatsapp_number', request.form.get('whatsapp_number', '251987957957')),
                ('phone_number', request.form.get('phone_number', '+251987957957')),
                ('store_address', request.form.get('store_address', 'ወሎ ደሴ ኩታበር, Ethiopia')),
                ('free_shipping_threshold', request.form.get('free_shipping_threshold', '5000')),
                ('shipping_cost', request.form.get('shipping_cost', '200')),
                ('currency', request.form.get('currency', 'ETB')),
                ('default_language', request.form.get('default_language', 'am')),
                ('meta_keywords', request.form.get('meta_keywords', '')),
                ('google_analytics', request.form.get('google_analytics', '')),
            ]
            for key, value in settings_to_save:
                cursor.execute("""
                    INSERT INTO settings (key, value) VALUES (%s, %s)
                    ON CONFLICT(key) DO UPDATE SET value = %s
                """, (key, value, value))
            conn.commit()
            flash('Settings saved successfully!', 'success')
        except Exception as e:
            print(f"Settings save error: {e}")
            flash('Error saving settings.', 'error')
        return redirect(url_for('admin.settings'))

    return render_template('admin/settings.html', settings=settings_data, lang=lang)


@admin_bp.route('/settings/change-password', methods=['POST'])
@admin_required
def change_password():
    current_password = request.form.get('current_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()

    if not current_password or not new_password or not confirm_password:
        flash('All password fields are required.', 'error')
        return redirect(url_for('admin.settings') + '#change-password')

    if new_password != confirm_password:
        flash('New password and confirmation do not match.', 'error')
        return redirect(url_for('admin.settings') + '#change-password')

    if len(new_password) < 8:
        flash('New password must be at least 8 characters long.', 'error')
        return redirect(url_for('admin.settings') + '#change-password')

    try:
        conn = get_db()
        cursor = conn.cursor()
        admin_id = session.get('admin_id') or session.get('user_id')
        cursor.execute("SELECT id, password_hash FROM users WHERE id = %s AND is_admin = 1",
                       (admin_id,))
        admin = cursor.fetchone()

        if not admin or not check_password_hash(admin[1], current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('admin.settings') + '#change-password')

        new_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, admin[0]))
        conn.commit()
        flash('Password changed successfully!', 'success')
    except Exception as e:
        print(f"Admin change password error: {e}")
        flash('Error changing password. Please try again.', 'error')

    return redirect(url_for('admin.settings') + '#change-password')


@admin_bp.route('/clear-cache', methods=['GET', 'POST'])
@admin_required
def clear_cache():
    try:
        session.pop('cart', None)
        from flask import current_app
        current_app.jinja_env.cache = {}
        return jsonify({'success': True, 'message': 'Cache cleared successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/backup-database', methods=['GET', 'POST'])
@admin_required
def backup_database():
    try:
        return jsonify({
            'success': False,
            'error': 'This app uses PostgreSQL. Use pg_dump from the shell or Replit Database panel to back up.'
        }), 400
    except Exception as e:
        print(f"Backup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== NOTIFICATIONS ====================

@admin_bp.route('/send-notification', methods=['GET', 'POST'])
@admin_required
def send_notification():
    lang = get_lang()
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            body = request.form.get('body', '').strip()
            title_am = request.form.get('title_am', '').strip()
            title_ar = request.form.get('title_ar', '').strip()
            body_am = request.form.get('body_am', '').strip()
            body_ar = request.form.get('body_ar', '').strip()
            image_url = request.form.get('image_url', '').strip()
            link = request.form.get('link', '').strip()
            target = request.form.get('target', 'all')

            if not title or not body:
                flash('Please enter both title and message', 'error')
                return redirect(url_for('admin.send_notification'))

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO notifications (
                    title, title_am, title_ar, body, body_am, body_ar,
                    image, link, target_audience, sent_at, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
            """, (title, title_am, title_ar, body, body_am, body_ar,
                  image_url, link, target, session.get('admin_username', 'admin')))
            conn.commit()

            # Fan-out to user_notifications table so customers see it in dashboard
            try:
                cursor.execute("SELECT id FROM users WHERE is_admin = 0 AND is_active = 1")
                user_rows = cursor.fetchall()
                for ur in (user_rows or []):
                    uid = ur[0]
                    notify_user(uid, title, body, type='info', link=link or '')
            except Exception:
                pass

            flash('Notification sent to all customers!', 'success')
        except Exception as e:
            print(f"Send notification error: {e}")
            flash('Error sending notification.', 'error')
        return redirect(url_for('admin.send_notification'))

    return render_template('admin/send_notification.html', lang=lang)


@admin_bp.route('/alerts')
@admin_required
def admin_alerts_page():
    """Admin alerts inbox page."""
    lang = get_lang()
    alerts = get_admin_alerts(limit=100)
    unread = get_admin_unread_count()
    return render_template('admin/alerts.html', alerts=alerts, unread=unread, lang=lang)


@admin_bp.route('/alerts/mark-read', methods=['POST'])
@admin_required
def admin_mark_alerts_read():
    alert_id = request.json.get('id') if request.is_json else None
    mark_admin_alerts_read(alert_id)
    return jsonify({'success': True})


# ==================== REVIEWS ====================

@admin_bp.route('/reviews')
@admin_required
def admin_reviews():
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, p.name_am as product_name, u.full_name as user_name
            FROM reviews r
            JOIN products p ON r.product_id = p.id
            JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
        """)
        reviews_rows = cursor.fetchall()
        return render_template('admin/reviews/index.html',
                               reviews=[dict(r) for r in reviews_rows] if reviews_rows else [],
                               lang=lang)
    except Exception as e:
        print(f"Admin reviews error: {e}")
        flash('Error loading reviews', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/reviews/approve/<int:review_id>', methods=['POST'])
@admin_required
def approve_review(review_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE reviews SET is_approved = 1 WHERE id = %s", (review_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Review approved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/reviews/delete/<int:review_id>', methods=['DELETE', 'POST'])
@admin_required
def delete_review(review_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Review deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== TRANSLATIONS ====================

@admin_bp.route('/translations/status', methods=['GET'])
@admin_required
def translation_status():
    try:
        from utils.translation_cache import get_translation_stats, FALLBACK_TEXTS
        stats = get_translation_stats()
        return jsonify({
            'status': 'success',
            'cache': stats,
            'fallback_languages': list(FALLBACK_TEXTS.keys()),
            'supported_languages': ['am', 'en', 'ar']
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/translations/clear', methods=['POST'])
@admin_required
def clear_translations():
    try:
        from utils.translation_cache import clear_translation_cache
        clear_translation_cache()
        return jsonify({'status': 'success', 'message': 'Translation cache cleared successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== PASSWORD RESET TOKENS ====================

@admin_bp.route('/password-resets')
@admin_required
def password_resets():
    """View pending password reset tokens — useful when email is not configured."""
    lang = get_lang()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT prt.id, prt.email, prt.token, prt.expires_at, prt.created_at,
                   u.full_name
            FROM password_reset_tokens prt
            LEFT JOIN users u ON u.email = prt.email
            WHERE prt.used = 0
              AND prt.expires_at > NOW()
            ORDER BY prt.created_at DESC
        """)
        tokens = [dict(r) for r in (cursor.fetchall() or [])]

        import datetime as _dt
        from flask import request as _req
        base = _req.host_url.rstrip('/')
        for t in tokens:
            t['reset_url'] = f"{base}/reset-password/{t['token']}"
            if t['expires_at']:
                remaining = t['expires_at'] - _dt.datetime.now()
                mins = int(remaining.total_seconds() / 60)
                t['expires_in'] = f"{mins} min" if mins > 0 else "expired"

        return render_template('admin/password_resets/index.html',
                               tokens=tokens, lang=lang)
    except Exception as e:
        print(f"Password resets admin error: {e}")
        flash('Error loading reset tokens.', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/password-resets/invalidate/<int:token_id>', methods=['POST'])
@admin_required
def invalidate_reset_token(token_id):
    """Manually invalidate a reset token."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE password_reset_tokens SET used = 1 WHERE id = %s", (token_id,))
        conn.commit()
        flash('Reset token invalidated.', 'success')
    except Exception as e:
        print(f"Invalidate token error: {e}")
        flash('Error invalidating token.', 'error')
    return redirect(url_for('admin.password_resets'))
