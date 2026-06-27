"""
SEMIRA FASHION - Database Seeder (PostgreSQL)
Seeds products, advertisements, and settings using the app's PostgreSQL connection.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def seed_all(clear_existing=True):
    """Insert all sample data into PostgreSQL database."""
    try:
        from database.db import get_db
        conn = get_db()
        cursor = conn.cursor()

        print("\n" + "=" * 60)
        print("🌱 SEMIRA FASHION DATABASE SEEDER")
        print("=" * 60)

        # ==================== CATEGORIES ====================
        print("\n📁 Seeding categories...")

        category_defs = [
            ('ቀሚሶች',            'Dresses & Gowns',     'فساتين وعبايات'),
            ('ቶፖች እና ሸሚዞች',   'Tops & Shirts',        'قمصان وبلوزات'),
            ('ሱሪዎች እና ቁምጣዎች', 'Trousers & Shorts',    'بنطلونات'),
            ('ጃኬቶች እና ሹራቦች',  'Jackets & Knitwear',   'جاكيتات'),
            ('የውስጥ እና የሌሊት ልብሶች', 'Underwear & Nightwear', 'ملابس نوم'),
            ('የሕፃናት ሙሉ ልብሶች', 'Baby Suits & Rompers', 'ملابس أطفال'),
            ('ስፖርታዊ ልብሶች',    'Activewear',           'ملابس رياضية'),
            ('የባህል ልብሶች',      'Traditional Wear',     'ملابس تقليدية'),
            ('ሃይማኖታዊ አልባሳት',  'Religious Wear',       'ملابس دينية'),
        ]

        cat_ids = {}
        for name_am, name_en, name_ar in category_defs:
            # Try to find existing category first, then insert if not found
            cursor.execute("SELECT id FROM categories WHERE name = %s OR name_am = %s LIMIT 1", (name_en, name_am))
            existing = cursor.fetchone()
            if existing:
                cat_ids[name_am] = existing[0]
            else:
                cursor.execute("""
                    INSERT INTO categories (name, name_am, name_ar, is_active)
                    VALUES (%s, %s, %s, 1) RETURNING id
                """, (name_en, name_am, name_ar))
                row = cursor.fetchone()
                if row:
                    cat_ids[name_am] = row[0]

        conn.commit()
        print(f"   ✅ {len(cat_ids)} categories ready")

        # ==================== PRODUCTS ====================
        print("\n📦 Seeding products...")

        if clear_existing:
            cursor.execute("DELETE FROM order_items WHERE product_id IN (SELECT id FROM products)")
            cursor.execute("DELETE FROM cart_items WHERE product_id IN (SELECT id FROM products)")
            cursor.execute("DELETE FROM products")
            conn.commit()
            print("   ✓ Cleared existing products")

        def cid(name_am):
            return cat_ids.get(name_am, list(cat_ids.values())[0] if cat_ids else None)

        products = [
            # (name_am, name_en, price, compare_price, stock, category_am, is_featured)
            ('ሉክስ ቀሚስ',   'Luxury Dress',       2500, 3500, 20, 'ቀሚሶች',             True),
            ('ሞደርን ቀሚስ',  'Modern Dress',        1800, 2500, 25, 'ቀሚሶች',             True),
            ('ክላሲክ ቀሚስ',  'Classic Dress',       1500, 2200, 30, 'ቀሚሶች',             False),
            ('ሚኒ ቀሚስ',    'Mini Dress',          1200, 1800, 35, 'ቀሚሶች',             False),
            ('ማክሲ ቀሚስ',   'Maxi Dress',          2000, 2800, 15, 'ቀሚሶች',             True),
            ('ሴቶች ሸሚዝ',   "Women's Shirt",        800, 1200, 40, 'ሸሚዞች',             True),
            ('ብሉዝ',        'Blouse',               900, 1400, 30, 'ሸሚዞች',             False),
            ('ቲሸርት',       'T-Shirt',              500,  800, 60, 'ሸሚዞች',             False),
            ('ሴቶች ሱሪ',    "Women's Suit",         3500, 5000, 10, 'ሱሪዎች እና ቁምጣዎች',  True),
            ('ካዥዋል ሱሪ',   'Casual Trousers',      1200, 1800, 25, 'ሱሪዎች እና ቁምጣዎች',  False),
            ('ጂንስ',        'Jeans',               1500, 2200, 20, 'ሱሪዎች እና ቁምጣዎች',  True),
            ('ሕፃናት ቀሚስ',  "Girls' Dress",          600,  900, 30, 'ጀኬቶች እና ሹራቦች',   False),
            ('ሕፃናት ሸሚዝ',  "Boys' Shirt",           500,  750, 40, 'ጀኬቶች እና ሹራቦች',   False),
            ('ሕፃናት ሱሪ',   "Children's Trousers",   550,  800, 35, 'ጀኬቶች እና ሹራቦች',   False),
            ('የሌሊት ልብስ',  'Nightwear Set',         800, 1200, 15, 'የሌሊት እና የቤት ልብሶች', False),
            ('የቤት ልብስ',   'Housewear',             700, 1000, 20, 'የሌሊት እና የቤት ልብሶች', False),
            ('ስፖርት ልብስ',  'Sportswear Set',       1000, 1500, 20, 'ስፖርታዊ ልብሶች',     True),
            ('ዮጋ ልብስ',    'Yoga Wear',            1100, 1600, 15, 'ስፖርታዊ ልብሶች',     False),
            ('ሂጃብ',        'Hijab',                 400,  600, 50, 'የሃይማኖት ሙሉ ልብሶች',  True),
            ('ስካርፍ',       'Scarf',                 350,  550, 50, 'የሃይማኖት ሙሉ ልብሶች',  False),
        ]

        inserted = 0
        for name_am, name_en, price, compare_price, stock, cat_am, featured in products:
            try:
                cursor.execute("""
                    INSERT INTO products
                        (name_am, name, price, compare_price, stock_quantity,
                         category_id, is_active, is_featured, is_new, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 1, %s, 1, %s)
                """, (name_am, name_en, price, compare_price, stock,
                      cid(cat_am), 1 if featured else 0, datetime.now()))
                inserted += 1
            except Exception as e:
                print(f"   ⚠️  Could not insert '{name_am}': {e}")
                conn.rollback()

        conn.commit()
        print(f"   ✅ Inserted {inserted} products")

        # ==================== ADVERTISEMENTS ====================
        print("\n📢 Seeding advertisements...")

        if clear_existing:
            cursor.execute("DELETE FROM advertisements")
            conn.commit()
            print("   ✓ Cleared existing advertisements")

        ads = [
            ('🎉 ልዩ ቅናሽ! እስከ 30% ቅናሽ', 'Special Discount! Up to 30% off all clothing!', '/products', 1),
            ('🚚 ነጻ ማጓጓዝ ከ5000 ብር በላይ',  'Free shipping on orders over 5000 ETB!',        '/cart',     2),
            ('✨ አዲስ ልብሶች ደርሰዋል!',       'New arrivals! Modern design, top quality!',      '/products', 3),
            ('💝 የበዓል ልዩ ቅናሽ!',           'Holiday special! Best gifts from SEMIRA!',        '/products', 4),
            ('👗 ቀሚሶች ከ500 ብር ጀምሮ!',     "Women's dresses starting from 500 ETB!",         '/products', 5),
            ('📱 WhatsApp ትዕዛዝ 5% ቅናሽ',  'Order on WhatsApp and get 5% extra discount!',   '/contact',  6),
        ]

        inserted_ads = 0
        for title_am, title_en, link, sort_order in ads:
            try:
                cursor.execute("""
                    INSERT INTO advertisements
                        (title, title_am, link, sort_order, is_active, created_at)
                    VALUES (%s, %s, %s, %s, 1, %s)
                """, (title_en, title_am, link, sort_order, datetime.now()))
                inserted_ads += 1
            except Exception as e:
                print(f"   ⚠️  Could not insert ad: {e}")
                conn.rollback()

        conn.commit()
        print(f"   ✅ Inserted {inserted_ads} advertisements")

        # ==================== SETTINGS ====================
        print("\n⚙️  Adding default settings...")

        if clear_existing:
            cursor.execute("DELETE FROM settings")
            conn.commit()
            print("   ✓ Cleared existing settings")

        settings = [
            ('site_name',               'SEMIRA FASHION'),
            ('site_name_am',            'ሰሚራ ፋሽን'),
            ('site_email',              'info@semirafashion.com'),
            ('site_phone',              '+251987957957'),
            ('admin_email',             'admin@semirafashion.com'),
            ('whatsapp_number',         '251987957957'),
            ('free_shipping_threshold', '5000'),
            ('shipping_cost',           '200'),
            ('currency',                'ETB'),
            ('currency_symbol',         'ETB'),
            ('default_language',        'am'),
            ('products_per_page',       '12'),
            ('maintenance_mode',        'false'),
            ('store_address',           'ወሎ ደሴ ኩታበር, Ethiopia'),
            ('last_seeded',             datetime.now().isoformat()),
        ]

        for key, value in settings:
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                (key, value)
            )

        conn.commit()
        print(f"   ✅ Inserted/updated {len(settings)} settings")

        # ==================== UPLOAD DIRECTORIES ====================
        print("\n📁 Creating upload directories...")
        for directory in ['static/uploads', 'static/uploads/products', 'static/uploads/ads', 'logs']:
            os.makedirs(directory, exist_ok=True)
            print(f"   ✓ {directory}")

        # ==================== SUMMARY ====================
        cursor.execute("SELECT COUNT(*) FROM products")
        final_products = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM advertisements")
        final_ads = cursor.fetchone()[0]

        print("\n" + "=" * 60)
        print("📊 SEEDING SUMMARY")
        print("=" * 60)
        print(f"📦 Products:       {final_products}")
        print(f"📢 Advertisements: {final_ads}")
        print(f"⚙️  Settings:       {len(settings)}")
        print("=" * 60)
        print("\n✅ Database seeded successfully!")
        print("\n🔐 Admin Login: password set via ADMIN_PASSWORD env var")
        print("🌐 Website:     http://localhost:5000")
        print("=" * 60 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ Seeding error: {e}")
        import traceback
        traceback.print_exc()
        return False


def seed_products_only():
    """Seed only products (without clearing existing)."""
    return seed_all(clear_existing=False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Seed database for SEMIRA FASHION')
    parser.add_argument('--keep', action='store_true', help='Keep existing data')
    parser.add_argument('--products-only', action='store_true', help='Seed only products')
    args = parser.parse_args()

    from app import app
    with app.app_context():
        if args.products_only:
            seed_products_only()
        else:
            seed_all(clear_existing=not args.keep)
