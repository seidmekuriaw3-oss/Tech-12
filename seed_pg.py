from database.db import get_db
from datetime import datetime

db = get_db()
cur = db.cursor()

products = [
    # (name, name_am, name_ar, name_en, desc, desc_am, desc_ar, desc_en, price, compare_price, cost, is_featured, stock_qty, cat_id)
    ('Evening Gown','የምሽት ቀሚስ','فستان سهرة','Evening Gown',
     'Elegant floor-length evening gown perfect for weddings and formal events.',
     'ለሠርግና ዝግጅቶች ተስማሚ የምሽት ቀሚስ','فستان سهرة فاخر للأعراس والمناسبات',
     'Elegant floor-length evening gown',1890,2500,950,1,30,1),

    ('Floral Maxi Dress','አበባ ማክሲ ቀሚስ','فستان ماكسي بالأزهار','Floral Maxi Dress',
     'Light and flowy floral maxi dress for casual and semi-formal wear.',
     'ቀላልና ውብ አበባ ማክሲ ቀሚስ','فستان ماكسي زهري خفيف وأنيق',
     'Light and flowy floral maxi dress',890,1200,420,0,25,1),

    ('Habesha Kemis','ሐበሻ ቀሚስ','قميص حبشي تقليدي','Habesha Kemis',
     'Authentic Habesha kemis with traditional embroidery, hand-woven cotton.',
     'ባህላዊ ጥልፍ ያለው ሐበሻ ቀሚስ','قميص حبشي أصيل بتطريز تقليدي وقطن منسوج يدوياً',
     'Authentic hand-woven Habesha kemis',1200,1600,600,1,40,8),

    ('Mini Party Dress','ሚኒ ፓርቲ ቀሚስ','فستان حفلات قصير','Mini Party Dress',
     'Stylish mini dress perfect for parties and casual outings.',
     'ለፓርቲና ወደ ውጭ ለመሄድ ምቹ ሚኒ ቀሚስ','فستان قصير أنيق للحفلات والنزهات',
     'Stylish mini dress for parties',750,1000,350,0,30,1),

    ('Silk Blouse','ሐር ብሎውዝ','بلوزة حريرية','Silk Blouse',
     'Smooth silk blouse suitable for office and evening wear.',
     'ለቢሮና ምሽት ምቹ ሐር ብሎውዝ','بلوزة حرير ناعمة مناسبة للمكتب والسهرات',
     'Smooth silk blouse for office and evening',650,900,300,1,30,2),

    ('Linen Summer Top','ሊነን ሰመር ቶፕ','توب صيفي كتاني','Linen Summer Top',
     'Breathable linen top ideal for hot Ethiopian summers.',
     'ለኢትዮጵያ ሙቀት ተስማሚ ሊነን ቶፕ','توب كتاني مثالي للصيف الإثيوبي الحار',
     'Breathable linen top for hot summers',480,700,220,0,40,2),

    ('Printed Crop Top','ፕሪንትድ ክሮፕ ቶፕ','توب قصير مطبوع','Printed Crop Top',
     'Trendy printed crop top for casual and street style.',
     'ፋሽን ፕሪንትድ ክሮፕ ቶፕ','توب قصير مطبوع عصري للأزياء الكاجوال',
     'Trendy printed crop top',390,580,180,0,35,2),

    ('Formal Button Shirt','ፎርማል ሸሚዝ','قميص رسمي بأزرار','Formal Button Shirt',
     'Classic formal shirt for professional settings, available in multiple colors.',
     'ለቢሮ ምቹ ክላሲክ ፎርማል ሸሚዝ','قميص رسمي كلاسيكي للبيئات المهنية',
     'Classic formal shirt for professionals',560,800,260,1,25,2),

    ('High-Waist Jeans','ሃይ ዌስት ጂንስ','جينز عالي الخصر','High-Waist Jeans',
     'Comfortable high-waist stretch jeans in multiple washes.',
     'ምቹ ሃይ ዌስት ስትሬች ጂንስ','جينز ممتد عالي الخصر بعدة أساليب',
     'Comfortable high-waist stretch jeans',720,1000,340,1,20,3),

    ('Palazzo Trousers','ፓላዞ ሱሪ','بنطال بالازو','Palazzo Trousers',
     'Wide-leg palazzo trousers for a chic and comfortable look.',
     'ሰፊ እግር ፓላዞ ሱሪ','بنطال بالازو واسع الأرجل',
     'Wide-leg palazzo trousers',580,820,270,0,30,3),

    ('Denim Shorts','ዴኒም ሾርትስ','شورت جينز','Denim Shorts',
     'Classic denim shorts perfect for casual warm-weather outings.',
     'ቀላል ዴኒም ሾርትስ','شورت جينز كلاسيكي مثالي للطقس الدافئ',
     'Classic denim shorts',420,620,190,0,35,3),

    ('Denim Jacket','ዴኒም ጃኬት','جاكيت جينز','Denim Jacket',
     'Classic denim jacket that pairs with any outfit.',
     'ለማንኛውም አልባሳት ተስማሚ ዴኒም ጃኬት','جاكيت جينز كلاسيكي يناسب أي لباس',
     'Classic denim jacket',950,1400,450,1,20,4),

    ('Knit Cardigan','ኒት ካርዲጋን','كارديجان محبوك','Knit Cardigan',
     'Cozy knit cardigan perfect for cool evenings and air-conditioned spaces.',
     'ለቀዝቃዛ ምሽቶች ምቹ ኒት ካርዲጋን','كارديجان محبوك مريح للأمسيات الباردة',
     'Cozy knit cardigan',780,1100,360,0,25,4),

    ('Satin Nightgown','ሳቲን ናይትጋውን','قميص نوم ساتان','Satin Nightgown',
     'Luxuriously soft satin nightgown for comfortable sleep.',
     'ምቹ ሳቲን ናይትጋውን','قميص نوم من الساتان الناعم الفاخر',
     'Luxuriously soft satin nightgown',620,900,290,0,30,5),

    ('Cotton Lounge Set','ኮቶን ላውንጅ ሴት','طقم استرخاء قطني','Cotton Lounge Set',
     'Breathable cotton lounge set for relaxing at home.',
     'ቤት ውስጥ ለመዝናናት ምቹ ኮቶን ሴት','طقم قطني مريح للاسترخاء في المنزل',
     'Breathable cotton lounge set',530,780,245,1,40,5),

    ('Baby Girl Romper Set','ሕፃን ሮምፐር ሴት','طقم رومبر للبنات','Baby Girl Romper Set',
     'Adorable cotton romper set for baby girls 0-12 months.',
     'ከ0-12 ወር ለሕፃናት ሮምፐር ሴት','طقم رومبر قطني رائع للرضيعات 0-12 شهراً',
     'Adorable cotton romper set 0-12 months',380,550,170,1,50,6),

    ('Baby Boy Suit','ሕፃን ወንድ ሱት','بدلة الأولاد الصغار','Baby Boy Suit',
     'Smart 3-piece baby boy suit for special occasions.',
     'ልዩ ዝግጅቶች ሕፃን ሱት ሶስት ክፍል','بدلة 3 قطع للأطفال الذكور للمناسبات الخاصة',
     'Smart 3-piece baby boy suit',450,680,210,0,35,6),

    ('Sports Leggings','ስፖርት ሌጊንስ','ليغنز رياضي','Sports Leggings',
     'High-performance moisture-wicking sports leggings.',
     'ከፍተኛ አፈጻጸም ስፖርት ሌጊንስ','ليغنز رياضي عالي الأداء يمتص الرطوبة',
     'High-performance sports leggings',680,950,315,1,30,7),

    ('Zip-Up Hoodie','ዚፕ ሁዲ','هودي بسحاب','Zip-Up Hoodie',
     'Comfortable zip-up hoodie for gym sessions and casual wear.',
     'ለጂም እና ቀልጣፋ አለባበስ ምቹ ዚፕ ሁዲ','هودي مريح بسحاب للجيم والارتداء اليومي',
     'Comfortable zip-up hoodie',820,1150,380,0,25,7),

    ('Netela Shawl','ነጠላ','نيتيلا','Netela Shawl',
     'Traditional Ethiopian netela shawl with hand-woven border, pure cotton.',
     'ባህላዊ የኢትዮጵያ ነጠላ፣ ፍጹም ጥጥ','شال نيتيلا الإثيوبي التقليدي مع حدود منسوج يدوياً',
     'Traditional Ethiopian netela shawl',350,520,160,1,60,8),
]

sql = """INSERT INTO products
  (name, name_am, name_ar, name_en,
   description, description_am, description_ar, description_en,
   price, compare_price, cost,
   is_featured, stock_quantity, low_stock_threshold,
   is_active, is_new, views, sales_count, created_at, updated_at, category_id)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,5,1,1,0,0,NOW(),NOW(),%s)"""

for p in products:
    cur.execute(sql, p)

db.commit()
cur.execute("SELECT COUNT(*) FROM products")
print(f"Products inserted: {cur.fetchone()[0]}")

# ── 5 ADS ─────────────────────────────────────────────────────
ads = [
    ('Summer Sale — Up to 40% Off',
     'የበጋ ቅናሽ — እስከ 40% ቅናሽ',
     'تخفيضات الصيف — خصم يصل إلى 40٪',
     'Shop our biggest summer sale. All dresses, tops & activewear discounted!',
     'ትልቁ የበጋ ቅናሽ። ሁሉም ቀሚሶች፣ ቶፖችና አክቲቭዌር ቅናሽ አለ!',
     'تسوق في أكبر تخفيضات الصيف. خصومات على الفساتين والقمصان والملابس الرياضية!',
     '/products', 1),

    ('New Arrivals — Traditional Collection',
     'አዲስ ምርቶች — ባህላዊ ስብስብ',
     'وصل حديثاً — المجموعة التقليدية',
     'Discover our new Habesha kemis and Netela shawl collection.',
     'የሐበሻ ቀሚስና ነጠላ አዲስ ስብስብ ያግኙ።',
     'اكتشف مجموعتنا الجديدة من قمصان الحبشة وأوشحة نيتيلا.',
     '/products', 2),

    ('Free Shipping Over 5,000 ETB',
     'ነጻ ማጓጓዝ ከ5,000 ብር በላይ',
     'شحن مجاني لما يزيد عن 5000 بر',
     'Order above 5,000 ETB and enjoy free delivery right to your door!',
     'ከ5,000 ብር በላይ ግዢ ሲያደርጉ ነጻ ዴሊቨሪ ያግኙ!',
     'اطلب فوق 5000 بر واستمتع بالتوصيل المجاني إلى بابك!',
     '/cart', 3),

    ('Baby Collection — Soft & Safe',
     'ሕፃናት ስብስብ — ለስላሳ እና ደህና',
     'مجموعة الأطفال — ناعمة وآمنة',
     'Pure cotton rompers and suits for your little ones. Gentle on delicate skin.',
     'ፍጹም ጥጥ ሮምፐር እና ሱቶች ለህፃናትዎ። ስስ ቆዳ ላይ ለስላሳ።',
     'رومبرات وبدل قطنية خالصة لأطفالك. لطيفة على البشرة الحساسة.',
     '/products', 4),

    ('Exclusive Members Discount — 10% Off',
     'የልዩ አባላት ቅናሽ — 10% ቅናሽ',
     'خصم الأعضاء الحصري — خصم 10٪',
     'Register today and get an exclusive 10% discount on your first order!',
     'ዛሬ ይመዝገቡ እና በመጀመሪያ ግዢዎ 10% ቅናሽ ያግኙ!',
     'سجل اليوم واحصل على خصم حصري 10٪ على طلبك الأول!',
     '/register', 5),
]

ad_sql = """INSERT INTO advertisements
  (title, title_am, title_ar, description, description_am, description_ar,
   link, sort_order, is_active, created_at)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,NOW())"""

for a in ads:
    cur.execute(ad_sql, a)

db.commit()
cur.execute("SELECT COUNT(*) FROM advertisements")
print(f"Ads inserted: {cur.fetchone()[0]}")
