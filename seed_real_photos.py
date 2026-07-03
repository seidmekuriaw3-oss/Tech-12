"""
SEMIRA FASHION - Real Photo Seeder
Seeds 20 products with real downloaded photos and 5 ads.
"""
import os, sys, json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def seed_real():
    from database.db import get_db
    conn = get_db()
    cur = conn.cursor()

    print("\n" + "=" * 60)
    print("📸 SEMIRA FASHION — REAL PHOTO SEEDER")
    print("=" * 60)

    # ── Categories ────────────────────────────────────────────────
    cat_defs = [
        ('ቀሚሶች',                   'Dresses & Gowns',       'فساتين وعبايات'),
        ('ቶፖች እና ሸሚዞች',            'Tops & Shirts',         'قمصان وبلوزات'),
        ('ሱሪዎች እና ቁምጣዎች',          'Trousers & Shorts',     'بنطلونات'),
        ('ጃኬቶች እና ሹራቦች',           'Jackets & Knitwear',    'جاكيتات'),
        ('የውስጥ እና የሌሊት ልብሶች',     'Underwear & Nightwear', 'ملابس نوم'),
        ('የሕፃናት ሙሉ ልብሶች',          'Baby Suits & Rompers',  'ملابس أطفال'),
        ('ስፖርታዊ ልብሶች',             'Activewear',            'ملابس رياضية'),
        ('የባህል ልብሶች',              'Traditional Wear',      'ملابس تقليدية'),
        ('ሃይማኖታዊ አልባሳት',           'Religious Wear',        'ملابس دينية'),
    ]
    cat_ids = {}
    for name_am, name_en, name_ar in cat_defs:
        cur.execute("SELECT id FROM categories WHERE name=%s OR name_am=%s LIMIT 1", (name_en, name_am))
        row = cur.fetchone()
        if row:
            cat_ids[name_am] = row[0]
        else:
            cur.execute(
                "INSERT INTO categories (name, name_am, name_ar, is_active) VALUES (%s,%s,%s,1) RETURNING id",
                (name_en, name_am, name_ar)
            )
            r = cur.fetchone()
            if r:
                cat_ids[name_am] = r[0]
    conn.commit()
    print(f"   ✅ {len(cat_ids)} categories ready")

    def cid(name_am):
        return cat_ids.get(name_am, list(cat_ids.values())[0])

    # ── Clear old products & ads ───────────────────────────────────
    cur.execute("DELETE FROM order_items WHERE product_id IN (SELECT id FROM products)")
    cur.execute("DELETE FROM cart_items  WHERE product_id IN (SELECT id FROM products)")
    cur.execute("DELETE FROM products")
    cur.execute("DELETE FROM advertisements")
    conn.commit()
    print("   ✓ Cleared existing products & advertisements")

    # ── 20 Products ───────────────────────────────────────────────
    # (name_en, name_am, desc_en, desc_am, price, compare, stock, cat_am, featured, new, thumb, color, material, sizes)
    products = [
        (
            'Luxury Evening Dress', 'ሉክስ ምሽት ቀሚስ',
            'Elegant luxury evening dress crafted with premium fabric. Perfect for weddings, galas and special occasions.',
            'ለሰርጎች፣ ልዩ ዝግጅቶች የሚስማማ ሉክሳዊ ምሽት ቀሚስ። ከፕሪሚየም ጨርቅ የተሰራ።',
            3200, 4500, 15, 'ቀሚሶች', 1, 1,
            'uploads/products/luxury_dress.jpg', 'Red', 'Satin', 'S,M,L,XL'
        ),
        (
            'Habesha Traditional Dress', 'ሀበሻ ቀሚስ',
            'Authentic Ethiopian Habesha Kemis with beautiful traditional embroidery. Made from 100% cotton.',
            'የሀበሻ ባህላዊ ቀሚስ - 100% ጥጥ - ባህላዊ ጥልፍ ያለው።',
            2800, 3800, 20, 'ቀሚሶች', 1, 1,
            'uploads/products/habesha_dress.jpg', 'White', 'Cotton', 'S,M,L,XL,XXL'
        ),
        (
            'Floral Maxi Dress', 'ፍሎራል ማክሲ ቀሚስ',
            'Flowing floral maxi dress ideal for summer outings and casual events. Light and breathable fabric.',
            'ለበጋ ወቅት እና ለቀን ቤት ውጭ ፕሮግራሞች ተስማሚ የሆነ ማክሲ ቀሚስ።',
            1900, 2600, 25, 'ቀሚሶች', 1, 1,
            'uploads/products/maxi_dress.jpg', 'Multicolor', 'Chiffon', 'S,M,L,XL'
        ),
        (
            'Stylish Mini Dress', 'ስታይሊሽ ሚኒ ቀሚስ',
            'Trendy mini dress for modern women. Great for dates, parties and casual outings.',
            'ለፓርቲ፣ ለቀን ውጭ ፕሮግራሞች ተስማሚ ሚኒ ቀሚስ።',
            1400, 1900, 30, 'ቀሚሶች', 0, 1,
            'uploads/products/mini_dress.jpg', 'Black', 'Polyester', 'XS,S,M,L'
        ),
        (
            'Formal Evening Gown', 'ፎርማል ምሽት ጋውን',
            'Sophisticated halter-neck evening gown for formal events and celebrations. Tassel hem design.',
            'ለፎርማል ፕሮግራሞች እና ሰርጎች ተስማሚ የምሽት ጋውን።',
            4200, 5500, 10, 'ቀሚሶች', 1, 0,
            'uploads/products/evening_gown.jpg', 'Navy Blue', 'Stretch Fabric', 'S,M,L,XL'
        ),
        (
            "Women's Elegant Blouse", 'ሴቶች ኤሌጋንት ብሉዝ',
            'Classic elegant blouse for work and everyday wear. Comfortable fit with a polished look.',
            'ለስራ እና ለዕለት ተዕለት ለሚስማማ ኤሌጋንት ብሉዝ።',
            950, 1400, 40, 'ቶፖች እና ሸሚዞች', 1, 0,
            'uploads/products/blouse.jpg', 'White', 'Cotton Blend', 'S,M,L,XL,XXL'
        ),
        (
            'Printed Colorful Blouse', 'ያጌጠ ብሉዝ',
            'Vibrant printed blouse with unique patterns. Perfect for casual and semi-formal wear.',
            'ልዩ ንድፍ ያለው ያጌጠ ብሉዝ። ለቀን ፕሮግራሞች ተስማሚ።',
            850, 1200, 35, 'ቶፖች እና ሸሚዞች', 0, 1,
            'uploads/products/printed_blouse.jpg', 'Multicolor', 'Rayon', 'S,M,L,XL'
        ),
        (
            'Basic Cotton T-Shirt', 'ቤዚክ ቲሸርት',
            'Soft and comfortable 100% cotton t-shirt. Available in multiple colors. Perfect for layering.',
            '100% ጥጥ - ለምቾት እና ለዕለት ተዕለት ለሚስማማ ቲሸርት።',
            480, 700, 80, 'ቶፖች እና ሸሚዞች', 0, 0,
            'uploads/products/tshirt.jpg', 'Beige', 'Cotton', 'XS,S,M,L,XL,XXL'
        ),
        (
            "Women's Formal Shirt", 'ሴቶች ፎርማል ሸሚዝ',
            'Crisp formal white shirt for professional settings. Tailored fit for a sharp look.',
            'ለፕሮፌሽናል ሥራ ተስማሚ ፎርማል ሸሚዝ።',
            1100, 1600, 30, 'ቶፖች እና ሸሚዞች', 0, 1,
            'uploads/products/ladies_shirt.jpg', 'White', 'Cotton', 'S,M,L,XL'
        ),
        (
            'Skinny Jeans', 'ስኪኒ ጂንስ',
            'Classic skinny-fit denim jeans. Comfortable stretch fabric with 5-pocket design.',
            'ክላሲክ ስኪኒ ጂንስ። ስትሬች ዲኒም ጨርቅ - 5 ኪስ።',
            1600, 2200, 25, 'ሱሪዎች እና ቁምጣዎች', 1, 0,
            'uploads/products/jeans.jpg', 'Blue', 'Denim', '28,30,32,34,36'
        ),
        (
            'Casual Trousers', 'ካዥዋል ሱሪ',
            'Relaxed-fit casual trousers for everyday comfort. Lightweight and easy to style.',
            'ለዕለት ተዕለት የሚስማማ ካዥዋል ሱሪ። ቀላል ጨርቅ።',
            1100, 1600, 30, 'ሱሪዎች እና ቁምጣዎች', 0, 0,
            'uploads/products/casual_trousers.jpg', 'Beige', 'Cotton Blend', 'S,M,L,XL'
        ),
        (
            'Wide Leg Linen Pants', 'ዋይድ ሌግ ሊነን ሱሪ',
            'Breezy wide-leg linen pants perfect for summer. Drawstring waist for adjustable fit.',
            'ለበጋ ወቅት ተስማሚ ዋይድ ሌግ ሊነን ሱሪ። ቀላልና ሰፊ ዲዛይን።',
            1350, 1900, 20, 'ሱሪዎች እና ቁምጣዎች', 0, 1,
            'uploads/products/linen_pants.jpg', 'Khaki', 'Linen', 'S,M,L,XL,XXL'
        ),
        (
            'Classic Denim Jacket', 'ክላሲክ ዲኒም ጃኬት',
            'Timeless denim jacket that goes with everything. Durable quality with button-front closure.',
            'ሁሉን ነገር የሚስማማ ክላሲክ ዲኒም ጃኬት። ጠንካራ ጥራት።',
            2200, 3000, 18, 'ጃኬቶች እና ሹራቦች', 1, 0,
            'uploads/products/denim_jacket.jpg', 'Blue', 'Denim', 'XS,S,M,L,XL'
        ),
        (
            'Knit Cardigan', 'ኒት ካርዲጋን',
            'Cozy knit cardigan for cooler days. Long-length design with soft, warm fabric.',
            'ለቀዝቃዛ ቀናት ተስማሚ ለስላሳ ኒት ካርዲጋን።',
            1500, 2100, 22, 'ጃኬቶች እና ሹራቦች', 0, 1,
            'uploads/products/cardigan.jpg', 'Cream', 'Knit', 'S,M,L,XL'
        ),
        (
            'Fashion Hijab', 'ፋሽን ሂጃብ',
            'Premium quality fashion hijab in multiple colors. Soft, breathable chiffon fabric.',
            'ፕሪሚየም ጥራት ያለው ፋሽን ሂጃብ። ለስላሳ ሺፎን ጨርቅ።',
            450, 650, 60, 'ሃይማኖታዊ አልባሳት', 1, 0,
            'uploads/products/hijab.jpg', 'Various', 'Chiffon', 'One Size'
        ),
        (
            'Modest Prayer Dress', 'ሙሉ ሽፋን ልብስ',
            'Full-coverage modest dress perfect for daily wear and prayer. Comfortable and elegant.',
            'ለዕለት ተዕለት እና ለጸሎት ተስማሚ ሙሉ ሽፋን ልብስ።',
            1800, 2500, 15, 'ሃይማኖታዊ አልባሳት', 0, 1,
            'uploads/products/prayer_dress.jpg', 'Black', 'Polyester Crepe', 'S,M,L,XL,XXL'
        ),
        (
            '2-Piece Sportswear Set', '2 ፒስ ስፖርት ልብስ',
            'High-performance 2-piece activewear set. Moisture-wicking fabric for intense workouts.',
            'ለስፖርት ተስማሚ 2 ፒስ ሴት። ላብ የሚያወጣ ጨርቅ።',
            1100, 1600, 20, 'ስፖርታዊ ልብሶች', 1, 1,
            'uploads/products/sportswear.jpg', 'Black/Pink', 'Spandex Blend', 'XS,S,M,L,XL'
        ),
        (
            'High-Waist Yoga Pants', 'ሃይ-ዌስት ዮጋ ሱሪ',
            'Stretchy high-waist yoga pants for yoga, pilates and gym. 4-way stretch fabric.',
            'ለዮጋ፣ ፒላቴስ እና ጂም ተስማሚ ሃይ-ዌስት ዮጋ ሱሪ።',
            980, 1400, 25, 'ስፖርታዊ ልብሶች', 0, 1,
            'uploads/products/yoga_pants.jpg', 'Black', 'Spandex', 'XS,S,M,L,XL'
        ),
        (
            "Baby Girl's Dress", 'ሕፃናት ቀሚስ',
            'Adorable baby girl dress with cute print. Soft cotton fabric safe for delicate skin.',
            'ሕፃናት ቆዳ ላይ ደህና የሆነ ለስላሳ ጥጥ። ቆንጆ ዲዛይን።',
            620, 900, 35, 'የሕፃናት ሙሉ ልብሶች', 0, 1,
            'uploads/products/baby_dress.jpg', 'Pink', 'Cotton', '0-3M,3-6M,6-12M,1-2Y'
        ),
        (
            "Girls' Party Dress", 'ልጃገረዶች ፓርቲ ቀሚስ',
            'Beautiful party dress for girls. Tulle skirt with embroidered bodice. Great for celebrations.',
            'ለፓርቲ ተስማሚ ቆንጆ ልጃገረዶች ቀሚስ። ልዩ ጥልፍ ዲዛይን።',
            850, 1200, 25, 'የሕፃናት ሙሉ ልብሶች', 1, 0,
            'uploads/products/girls_dress.jpg', 'Pink', 'Tulle/Cotton', '3-4Y,5-6Y,7-8Y,9-10Y'
        ),
    ]

    inserted = 0
    for (name_en, name_am, desc_en, desc_am, price, compare, stock, cat_am,
         featured, is_new, thumb, color, material, sizes) in products:
        try:
            images_json = json.dumps([thumb])
            cur.execute("""
                INSERT INTO products
                    (name, name_am, description, description_am,
                     price, compare_price, stock_quantity, category_id,
                     is_active, is_featured, is_new,
                     thumbnail, images, color, material, sizes,
                     gender, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s,%s,%s,%s,%s,%s,'female',%s,%s)
            """, (name_en, name_am, desc_en, desc_am,
                  price, compare, stock, cid(cat_am),
                  featured, is_new,
                  thumb, images_json, color, material, sizes,
                  datetime.now(), datetime.now()))
            inserted += 1
        except Exception as e:
            print(f"   ⚠️  {name_en}: {e}")
            conn.rollback()

    conn.commit()
    print(f"   ✅ Inserted {inserted} products")

    # ── 5 Advertisements ──────────────────────────────────────────
    ads = [
        ('🎉 ልዩ ቅናሽ - እስከ 40% ቅናሽ!', 'Special Sale — Up to 40% off!',
         'ሁሉም ቀሚሶች እና ብሉዞች ላይ ታላቅ ቅናሽ። ዛሬ ብቻ!',
         'Huge discount on all dresses and blouses. Today only!',
         'uploads/products/habesha_dress.jpg', '/products', 1),

        ('✨ አዲስ ልብሶች ደርሰዋል!', 'New Arrivals Are Here!',
         'የወቅቱ ሞደርን ልብሶች አሁን ገቡ። ለመጀመሪያ ብታዝዙ 10% ቅናሽ ያገኛሉ።',
         'Season\'s hottest new styles just arrived. 10% off your first order.',
         'uploads/ads/ad_new_arrivals.jpg', '/products?filter=new', 2),

        ('🚚 ከ5,000 ብር በላይ ነጻ ማጓጓዝ!', 'Free Shipping Over 5,000 ETB!',
         'ከ5,000 ብር በላይ ሲገዙ ወጭ ሳይከፍሉ ቤትዎ ድረስ እናደርሳለን።',
         'Order over 5,000 ETB and we deliver to your door for free.',
         'uploads/ads/ad_summer.jpg', '/cart', 3),

        ('🪭 የባህል ልብሶች - ልዩ ምርጫ!', 'Traditional Wear — Exclusive Collection!',
         'ሀበሻ ቀሚስ፣ ጥልፍ ልብሶች። ለሰርግ እና ለበዓል።',
         'Habesha kemis and embroidered garments for weddings and celebrations.',
         'uploads/ads/ad_traditional.jpg', '/products?category=traditional', 4),

        ('💝 የበዓል ልዩ ቅናሽ!', 'Holiday Special Offer!',
         'ለቤተሰብዎ ምርጥ ስጦታ ይምረጡ። ሁሉም ሕፃናት ልብሶች 15% ቅናሽ።',
         'Choose the best gift for your family. 15% off all kids clothing.',
         'uploads/ads/ad_holiday.jpg', '/products', 5),
    ]

    inserted_ads = 0
    for (title_am, title_en, desc_am, desc_en, image, link, sort_order) in ads:
        try:
            cur.execute("""
                INSERT INTO advertisements
                    (title, title_am, description, description_am,
                     image, link, sort_order, is_active, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,1,%s)
            """, (title_en, title_am, desc_en, desc_am,
                  image, link, sort_order, datetime.now()))
            inserted_ads += 1
        except Exception as e:
            print(f"   ⚠️  Ad error: {e}")
            conn.rollback()

    conn.commit()
    print(f"   ✅ Inserted {inserted_ads} advertisements")

    print("\n" + "=" * 60)
    print(f"✅ Done! {inserted} products + {inserted_ads} ads seeded with real photos.")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    from app import app
    with app.app_context():
        seed_real()
