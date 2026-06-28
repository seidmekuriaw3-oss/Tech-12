import os
from pathlib import Path
from dotenv import load_dotenv

os.chdir(r'C:\Users\USER\Downloads\Tech-12\Tech-12')
load_dotenv(Path('.env'), override=True)

from app import app
from database.db import get_db

with app.app_context():
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM advertisements')
    ads = [
        ('Summer Sale', 'የበጋ ቅናሽ', 'Up to 30% off selected fashion items.', 'እስከ 30% ቅናሽ በተመረጡ ልብሶች', 'ads/sale.jpg', '', '/products', 1, 1),
        ('Free Shipping', 'ነጻ ማጓጓዝ', 'Free delivery on orders above 5000 ETB.', 'ከ 5000 ብር በላይ ትዕዛዝ ነጻ ማጓጓዝ', 'ads/shipping.jpg', '', '/cart', 2, 1),
        ('New Arrivals', 'አዲስ መግቢያ', 'Discover our latest fashion collection.', 'የቅርብ ጊዜ የፋሽን ስብስብ ይመልከቱ', 'ads/new.jpg', '', '/products', 3, 1),
    ]
    for title, title_am, description, description_am, image, media_url, link, sort_order, is_active in ads:
        cur.execute(
            """
            INSERT INTO advertisements (
                title, title_am, description, description_am, image, media_url, link,
                sort_order, is_active, start_date, end_date, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW() + INTERVAL '30 days', NOW())
            """,
            (title, title_am, description, description_am, image, media_url, link, sort_order, is_active),
        )
    db.commit()
    cur.execute('SELECT COUNT(*) FROM advertisements')
    print('AD_COUNT', cur.fetchone()[0])
    cur.execute('SELECT title, title_am, link FROM advertisements ORDER BY sort_order')
    print('ADS', cur.fetchall())
