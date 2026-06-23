"""
SEMIRA FASHION - Database Seeder (PostgreSQL)
Seeds products, ads, and settings using the app's PostgreSQL connection.
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

        # ==================== CHECK TABLE STRUCTURE ====================
        print("\n📋 Checking database structure...")

        def get_columns(table):
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s
            """, (table,))
            return [row[0] for row in cursor.fetchall()]

        product_columns  = get_columns('products')
        ad_columns       = get_columns('ads')
        settings_columns = get_columns('settings')

        # ==================== PRODUCTS ====================
        print("\n📦 Seeding products...")

        if clear_existing:
            cursor.execute("DELETE FROM order_items WHERE product_id IN (SELECT id FROM products)")
            cursor.execute("DELETE FROM cart_items WHERE product_id IN (SELECT id FROM products)")
            cursor.execute("DELETE FROM products")
            print("   ✓ Cleared existing products")

        products = [
            # Women's Dresses
            ('ሉክስ ቀሚስ', 'Luxury Dress', '2500', '3500', None, 'ቀሚሶች', 'High-end luxury dress with premium fabric', 5, True),
            ('ሞደርን ቀሚስ', 'Modern Dress', '1800', '2500', None, 'ቀሚሶች', 'Contemporary design dress', 4, True),
            ('ክላሲክ ቀሚስ', 'Classic Dress', '1500', '2200', None, 'ቀሚሶች', 'Elegant classic dress', 5, True),
            ('ሚኒ ቀሚስ', 'Mini Dress', '1200', '1800', None, 'ቀሚሶች', 'Stylish mini dress', 4, True),
            ('ማክሲ ቀሚስ', 'Maxi Dress', '2000', '2800', None, 'ቀሚሶች', 'Beautiful maxi dress', 5, True),

            # Tops & Shirts
            ('ሴቶች ሸሚዝ', "Women's Shirt", '800', '1200', None, 'ሸሚዞች', "Women's casual shirt", 4, True),
            ('ብሉዝ', 'Blouse', '900', '1400', None, 'ሸሚዞች', 'Elegant blouse for all occasions', 4, True),
            ('ቲሸርት', 'T-Shirt', '500', '800', None, 'ሸሚዞች', 'Comfortable cotton t-shirt', 3, True),

            # Suits & Formal
            ('ሴቶች ሱሪ', "Women's Suit", '3500', '5000', None, 'ሱሪዎች እና ቁምጣዎች', "Women's formal suit", 5, True),
            ('ካዥዋል ሱሪ', 'Casual Trousers', '1200', '1800', None, 'ሱሪዎች እና ቁምጣዎች', 'Comfortable casual trousers', 4, True),
            ('ጂንስ', 'Jeans', '1500', '2200', None, 'ሱሪዎች እና ቁምጣዎች', 'Stylish denim jeans', 4, True),

            # Children's Clothing
            ('ሕፃናት ቀሚስ', "Girls' Dress", '600', '900', None, 'ጀኬቶች እና ሹራቦች', "Beautiful dress for girls", 5, True),
            ('ሕፃናት ሸሚዝ', "Boys' Shirt", '500', '750', None, 'ጀኬቶች እና ሹራቦች', "Boys' casual shirt", 4, True),
            ('ሕፃናት ሱሪ', "Children's Trousers", '550', '800', None, 'ጀኬቶች እና ሹራቦች', "Children's trousers", 4, True),

            # Night & Home Wear
            ('የሌሊት ልብስ', 'Nightwear', '800', '1200', None, 'የሌሊት እና የቤት ልብሶች', 'Comfortable nightwear set', 4, True),
            ('የቤት ልብስ', 'Housewear', '700', '1000', None, 'የሌሊት እና የቤት ልብሶች', 'Comfortable home wear', 4, True),

            # Sports & Active
            ('ስፖርት ልብስ', 'Sportswear', '1000', '1500', None, 'ስፖርታዊ ልብሶች', "Women's sportswear set", 4, True),
            ('ዮጋ ልብስ', 'Yoga Wear', '1100', '1600', None, 'ስፖርታዊ ልብሶች', 'Flexible yoga wear', 5, True),

            # Scarves & Accessories
            ('ሂጃብ', 'Hijab', '400', '600', None, 'የሃይማኖት ሙሉ ልብሶች', 'Premium quality hijab', 5, True),
            ('ስካርፍ', 'Scarf', '350', '550', None, 'የሃይማኖት ሙሉ ልብሶች', 'Elegant fashion scarf', 4, True),
        ]

        inserted_products = 0
        for p in products:
            try:
                cols = ['name_am', 'name', 'price', 'original_price', 'thumbnail', 'category', 'description']
                vals = list(p[:7])
                if 'rating' in product_columns:
                    cols.append('rating'); vals.append(p[7])
                if 'is_active' in product_columns:
                    cols.append('is_active'); vals.append(p[8])
                if 'created_at' in product_columns:
                    cols.append('created_at'); vals.append(datetime.now())

                placeholders = ', '.join(['%s'] * len(cols))
                sql = f"INSERT INTO products ({', '.join(cols)}) VALUES ({placeholders})"
                cursor.execute(sql, tuple(vals))
                inserted_products += 1
            except Exception as e:
                print(f"   ⚠️  Could not insert product {p[0]}: {e}")
                conn.rollback()

        conn.commit()
        print(f"   ✅ Inserted {inserted_products} products")

        # ==================== ADS ====================
        print("\n📢 Seeding advertisements...")

        if clear_existing:
            cursor.execute("DELETE FROM ads")
            print("   ✓ Cleared existing ads")

        ads = [
            ('🎉 ልዩ ቅናሽ! እስከ 30% ቅናሽ በሁሉም ልብሶች ላይ! ውሱን ጊዜ ብቻ!', 'discount', '#ff4444', '/products', True, 1),
            ('🚚 ነጻ ማጓጓዝ ከ5000 ብር በላይ ግዢ ላይ! ዛሬውኑ ይግዙ!', 'shipping', '#4CAF50', '/cart', True, 2),
            ('✨ አዲስ ልብሶች ደርሰዋል! ዘመናዊ ዲዛይን፣ ምርጥ ጥራት!', 'new', '#2196F3', '/products', True, 3),
            ('💝 የበዓል ልዩ ቅናሽ! ለቤተሰብዎ ምርጥ ስጦታ ከSEMIRA FASHION ጋር!', 'holiday', '#9C27B0', '/products', True, 4),
            ('👗 የሴቶች ቀሚሶች ልዩ ቅናሽ! ምርጥ ቀሚሶች ዋጋ ከ500 ብር ጀምሮ!', 'product', '#FF9800', '/products', True, 5),
            ('📱 በዋትሳፕ በማዘዝ ተጨማሪ 5% ቅናሽ ያግኙ!', 'whatsapp', '#25D366', '/contact', True, 6),
            ('⭐ SEMIRA FASHION - ምርጥ የፋሽን እስቶር ወሎ ደሴ ኩታበር!', 'award', '#FFC107', '/about', True, 7),
            ('🔥 ፈጣን ሽያጭ! የተወሰኑ ልብሶች በ50% ቅናሽ! አያምልጥዎት!', 'flash_sale', '#FF4444', '/products', True, 8),
            ('🎁 ለእያንዳንዱ ግዢ ነጻ ስጦታ! ውሱን ብዛት ብቻ!', 'gift', '#E91E63', '/cart', True, 9),
            ('👶 የሕፃናት ልብሶች ልዩ ቅናሽ! አሁን ይግዙ!', 'bundle', '#009688', '/products', True, 10),
        ]

        inserted_ads = 0
        for ad in ads:
            try:
                cols = ['text']
                vals = [ad[0]]
                if 'type' in ad_columns:        cols.append('type');       vals.append(ad[1])
                if 'color' in ad_columns:       cols.append('color');      vals.append(ad[2])
                if 'link' in ad_columns:        cols.append('link');       vals.append(ad[3])
                if 'is_active' in ad_columns:   cols.append('is_active');  vals.append(ad[4])
                if 'sort_order' in ad_columns:  cols.append('sort_order'); vals.append(ad[5])
                if 'created_at' in ad_columns:  cols.append('created_at'); vals.append(datetime.now())

                placeholders = ', '.join(['%s'] * len(cols))
                sql = f"INSERT INTO ads ({', '.join(cols)}) VALUES ({placeholders})"
                cursor.execute(sql, tuple(vals))
                inserted_ads += 1
            except Exception as e:
                print(f"   ⚠️  Could not insert ad: {e}")
                conn.rollback()

        conn.commit()
        print(f"   ✅ Inserted {inserted_ads} advertisements")

        # ==================== SETTINGS ====================
        print("\n⚙️ Adding default settings...")

        if clear_existing:
            cursor.execute("DELETE FROM settings")
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
        cursor.execute("SELECT COUNT(*) FROM ads")
        final_ads = cursor.fetchone()[0]

        print("\n" + "=" * 60)
        print("📊 SEEDING SUMMARY")
        print("=" * 60)
        print(f"📦 Products:       {final_products}")
        print(f"📢 Advertisements: {final_ads}")
        print(f"⚙️ Settings:       {len(settings)}")
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
    """Seed only products."""
    return seed_all(clear_existing=False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Seed database for SEMIRA FASHION')
    parser.add_argument('--keep', action='store_true', help='Keep existing data')
    parser.add_argument('--products-only', action='store_true', help='Seed only products')
    args = parser.parse_args()

    # Need Flask app context for get_db()
    from app import app
    with app.app_context():
        if args.products_only:
            seed_products_only()
        else:
            seed_all(clear_existing=not args.keep)
