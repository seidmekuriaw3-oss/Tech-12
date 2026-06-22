"""
Database Module for Ethiosadat Furniture
PostgreSQL backend using psycopg2 with a sqlite3-compatible adapter layer.
"""

import os
import psycopg2
import psycopg2.extras
from flask import g

DATABASE_URL = os.environ.get('DATABASE_URL')


class _PsycopgCursor:
    """Wraps a psycopg2 DictCursor to provide a sqlite3-compatible cursor API.

    Key compatibilities provided:
    - Translates ``?`` placeholders to ``%s`` automatically.
    - ``row[0]`` and ``row['column']`` both work (DictCursor behaviour).
    - ``cursor.lastrowid`` is populated after INSERT … RETURNING id.
    """

    def __init__(self, real_cursor):
        self._c = real_cursor
        self._lastrowid = None

    def execute(self, query, params=None):
        q = query.replace('?', '%s').strip()
        if params is not None:
            self._c.execute(q, params)
        else:
            self._c.execute(q)
        return self

    def executemany(self, query, params_list):
        q = query.replace('?', '%s').strip()
        self._c.executemany(q, params_list)
        return self

    def fetchall(self):
        return self._c.fetchall()

    def fetchone(self):
        return self._c.fetchone()

    def __iter__(self):
        return iter(self._c)

    @property
    def lastrowid(self):
        return self._lastrowid

    @lastrowid.setter
    def lastrowid(self, value):
        self._lastrowid = value

    @property
    def rowcount(self):
        return self._c.rowcount

    @property
    def description(self):
        return self._c.description


class _PsycopgConn:
    """Wraps a psycopg2 connection to provide a sqlite3-compatible connection API.

    - ``conn.execute(query, params)`` works like sqlite3's shortcut.
    - ``conn.row_factory = sqlite3.Row`` is silently ignored (DictCursor
      already provides dict-like row access).
    - ``conn.cursor()`` returns a _PsycopgCursor.
    """

    def __init__(self, raw_conn):
        self._conn = raw_conn

    def execute(self, query, params=None):
        cur = _PsycopgCursor(self._conn.cursor())
        return cur.execute(query, params)

    def cursor(self):
        return _PsycopgCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, value):
        pass


def _raw_connect():
    """Open a raw psycopg2 connection with DictCursor as the default factory."""
    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.DictCursor
    )
    # Set session timezone to Ethiopia (UTC+3) so NOW() matches dates
    # entered by admins in the Ethiopian timezone.
    with conn.cursor() as cur:
        cur.execute("SET timezone = 'Africa/Addis_Ababa'")
    conn.commit()
    return conn


def get_db():
    """Return the per-request wrapped database connection (cached on ``g``)."""
    try:
        if 'db' not in g:
            g.db = _PsycopgConn(_raw_connect())
        return g.db
    except RuntimeError:
        return _PsycopgConn(_raw_connect())


def close_db(e=None):
    """Close the database connection at the end of the request."""
    wrapped = g.pop('db', None)
    if wrapped is not None:
        try:
            wrapped.close()
        except Exception:
            pass


def init_db():
    """Create all tables and seed default data (PostgreSQL DDL)."""
    conn = _raw_connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            is_admin SMALLINT DEFAULT 0,
            is_active SMALLINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            last_login TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            name_am TEXT,
            name_ar TEXT,
            description TEXT,
            icon TEXT,
            image TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active SMALLINT DEFAULT 1,
            parent_id INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            name_am TEXT,
            name_ar TEXT,
            name_en TEXT,
            description TEXT,
            description_am TEXT,
            description_ar TEXT,
            description_en TEXT,
            price DOUBLE PRECISION NOT NULL,
            compare_price DOUBLE PRECISION,
            cost DOUBLE PRECISION,
            sku TEXT UNIQUE,
            barcode TEXT,
            stock_quantity INTEGER DEFAULT 0,
            low_stock_threshold INTEGER DEFAULT 5,
            images TEXT,
            thumbnail TEXT,
            is_active SMALLINT DEFAULT 1,
            is_featured SMALLINT DEFAULT 0,
            is_new SMALLINT DEFAULT 0,
            weight DOUBLE PRECISION,
            dimensions TEXT,
            material TEXT,
            color TEXT,
            views INTEGER DEFAULT 0,
            sales_count INTEGER DEFAULT 0,
            category_id INTEGER NOT NULL,
            meta_title TEXT,
            meta_description TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            added_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            order_number TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            customer_name TEXT,
            customer_email TEXT,
            status TEXT DEFAULT 'pending',
            payment_status TEXT DEFAULT 'pending',
            payment_method TEXT,
            subtotal DOUBLE PRECISION NOT NULL,
            discount DOUBLE PRECISION DEFAULT 0,
            shipping_fee DOUBLE PRECISION DEFAULT 0,
            total DOUBLE PRECISION NOT NULL,
            shipping_address TEXT NOT NULL,
            shipping_city TEXT,
            shipping_phone TEXT,
            notes TEXT,
            tracking_number TEXT,
            estimated_delivery DATE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price_at_time DOUBLE PRECISION NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS advertisements (
            id SERIAL PRIMARY KEY,
            title TEXT,
            title_am TEXT,
            title_ar TEXT,
            description TEXT,
            description_am TEXT,
            description_ar TEXT,
            image TEXT NOT NULL,
            media_url TEXT,
            link TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active SMALLINT DEFAULT 1,
            start_date TIMESTAMP DEFAULT NOW(),
            end_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            name_am TEXT,
            name_ar TEXT,
            address TEXT NOT NULL,
            address_am TEXT,
            address_ar TEXT,
            phone TEXT,
            email TEXT,
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            working_hours TEXT,
            image TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active SMALLINT DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            title_am TEXT,
            title_ar TEXT,
            body TEXT NOT NULL,
            body_am TEXT,
            body_ar TEXT,
            image TEXT,
            link TEXT,
            target_audience TEXT DEFAULT 'all',
            sent_count INTEGER DEFAULT 0,
            sent_at TIMESTAMP DEFAULT NOW(),
            created_by INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS contact_messages (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            message TEXT NOT NULL,
            is_read SMALLINT DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used SMALLINT DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS media_url TEXT")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_name TEXT")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_email TEXT")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS loyalty_points INTEGER DEFAULT 0")
    cur.execute("ALTER TABLE contact_messages ADD COLUMN IF NOT EXISTS admin_notes TEXT")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS newsletter (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            subscribed_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment TEXT,
            is_approved SMALLINT DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (product_id, user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (user_id, product_id)
        )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_wishlist_user ON wishlist(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_newsletter_email ON newsletter(email)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS loyalty_transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            order_id INTEGER,
            points INTEGER NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            link TEXT DEFAULT '',
            is_read SMALLINT DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_alerts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            link TEXT DEFAULT '',
            ref_order_id INTEGER,
            ref_user_id INTEGER,
            is_read SMALLINT DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_user_notif_user ON user_notifications(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_user_notif_read ON user_notifications(is_read)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_admin_alerts_read ON admin_alerts(is_read)")

    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_featured ON products(is_featured)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_number ON orders(order_number)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cart_user ON cart_items(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_contact_messages_created ON contact_messages(created_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_token ON password_reset_tokens(token)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_password_reset_email ON password_reset_tokens(email)")

    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        defaults = [
            ('ቀሚሶች',                'Dresses & Gowns',       'فساتين وعباءات',    '👗', 1),
            ('ቶፖች እና ሸሚዞች',        'Tops & Shirts',         'بلوزات وقمصان',     '👚', 2),
            ('ሱሪዎች እና ቁምጣዎች',      'Trousers & Shorts',     'بناطيل وشورتات',    '👖', 3),
            ('ጃኬቶች እና ሹራቦች',       'Jackets & Knitwear',    'جاكيتات وملابس صوف','🧥', 4),
            ('የውስጥ እና የሌሊት ልብሶች', 'Underwear & Nightwear', 'ملابس داخلية وليلية','🌙', 5),
            ('የሕፃናት ሙሉ ልብሶች',      'Baby Suits & Rompers',  'ملابس أطفال كاملة', '👶', 6),
            ('ስፖርታዊ ልብሶች',         'Activewear',            'ملابس رياضية',      '🏃', 7),
            ('የባህል ልብሶች',          'Traditional Wear',      'الملابس التقليدية', '🪭', 8),
        ]
        cur.executemany(
            "INSERT INTO categories (name_am, name, name_ar, icon, sort_order, is_active) VALUES (%s, %s, %s, %s, %s, 1)",
            defaults
        )
        print(f"✅ Seeded {len(defaults)} default categories")

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        from werkzeug.security import generate_password_hash
        admin_hash = generate_password_hash('admin123456', method='pbkdf2:sha256')
        cur.execute(
            "INSERT INTO users (username, email, password_hash, full_name, is_admin, is_active) VALUES (%s, %s, %s, %s, %s, %s)",
            ('admin', 'admin@ethiosadat.com', admin_hash, 'Administrator', 1, 1)
        )
        print("✅ Default admin user created")

    cur.execute("SELECT COUNT(*) FROM settings")
    if cur.fetchone()[0] == 0:
        default_settings = [
            ('site_name', 'ኢትዮሳዳት ፋሽን ወድ ሰሚራ'),
            ('site_name_am', 'ኢትዮሳዳት ፋሽን ወድ ሰሚራ - የሴቶች እና የልጆች ልብስ እስቶር'),
            ('site_name_ar', 'إثيوصادات فاشن ووده سميرة'),
            ('site_description', 'የሴቶች እና የልጆች ልብስ በተመጣጣኝ ዋጋ - Women\'s & Children\'s Fashion'),
            ('site_email', 'info@ethiosadat.com'),
            ('site_phone', '+251987957957'),
            ('admin_email', 'admin@ethiosadat.com'),
            ('phone_number', '+251987957957'),
            ('store_address', 'ወሎ ደሴ ኩታበር, Ethiopia'),
            ('whatsapp_number', '251987957957'),
            ('free_shipping_threshold', '5000'),
            ('shipping_cost', '200'),
            ('currency', 'ETB'),
            ('default_language', 'am'),
            ('meta_keywords', 'fashion, clothing, ልብስ, ethiosadat, ወሎ ደሴ ኩታበር, የሴቶች ልብስ, የልጆች ልብስ'),
            ('google_analytics', ''),
        ]
        cur.executemany(
            "INSERT INTO settings (key, value) VALUES (%s, %s)",
            default_settings
        )
    else:
        extra_settings = [
            ('site_description', 'የሴቶች እና የልጆች ልብስ በተመጣጣኝ ዋጋ - Women\'s & Children\'s Fashion'),
            ('admin_email', 'admin@ethiosadat.com'),
            ('phone_number', '+251987957957'),
            ('store_address', 'ወሎ ደሴ ኩታበር, Ethiopia'),
            ('meta_keywords', 'fashion, clothing, ልብስ, ethiosadat, ወሎ ደሴ ኩታበር, የሴቶች ልብስ, የልጆች ልብስ'),
            ('google_analytics', ''),
        ]
        for key, value in extra_settings:
            cur.execute(
                "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING",
                (key, value)
            )

    cur.execute("SELECT COUNT(*) FROM branches")
    if cur.fetchone()[0] == 0:
        branches = [
            ('ወሎ ደሴ ኩታበር', 'ወሎ ደሴ ኩታበር', 11.1333, 39.6333, '+251987957957', 1),
        ]
        for b in branches:
            cur.execute(
                "INSERT INTO branches (name, address, latitude, longitude, phone, sort_order, is_active) VALUES (%s, %s, %s, %s, %s, %s, 1)",
                b
            )
        print(f"✅ Seeded {len(branches)} branches")

    conn.commit()
    cur.close()
    conn.close()
    print("✅ PostgreSQL database initialized successfully!")


def init_db_app(app):
    """Initialize database within a Flask app context."""
    with app.app_context():
        init_db()


def get_db_stats():
    """Return aggregate statistics for the admin dashboard."""
    try:
        db = get_db()
        cursor = db.cursor()
        stats = {}
        for table, key in [
            ('products', 'products'),
            ('advertisements', 'ads'),
            ('orders', 'orders'),
            ('categories', 'categories'),
            ('users', 'users'),
        ]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[key] = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
        stats['pending_orders'] = cursor.fetchone()[0] or 0
        return stats
    except Exception as e:
        print(f"Error getting DB stats: {e}")
        return {'products': 0, 'ads': 0, 'orders': 0, 'categories': 0, 'users': 0, 'pending_orders': 0}


def commit_or_rollback(db=None):
    """Commit the current transaction or roll back on failure."""
    if db is None:
        db = get_db()
    try:
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Transaction rolled back: {e}")
        return False


def test_connection():
    """Return True if the database is reachable."""
    try:
        conn = _raw_connect()
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
