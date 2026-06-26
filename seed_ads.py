import sqlite3
import os
import random
from datetime import datetime
from config import Config

def seed_ads(with_media=False):
    """Insert sample advertisements into database with improved features"""
    
    # Get database path from config
    if hasattr(Config, 'DATABASE_PATH'):
        db_path = Config.DATABASE_PATH
    else:
        db_path = os.environ.get('DATABASE_PATH', 'database/semirafashion.db')
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("Please run the application first to initialize the database.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if ads table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ads'")
        if not cursor.fetchone():
            print("❌ Ads table does not exist!")
            print("Please run the application to create tables first.")
            conn.close()
            return False
        
        # Check table structure
        cursor.execute("PRAGMA table_info(ads)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Sample ads data with categories and links
        ads_data = [
            {
                'text': '🎉 ልዩ ቅናሽ! እስከ 30% ቅናሽ በሁሉም ምርቶች ላይ! ውሱን ጊዜ ብቻ!',
                'type': 'discount',
                'color': 'red',
                'link': '/category/all'
            },
            {
                'text': '🚚 ነጻ ማጓጓዝ ከ5000 ብር በላይ ግዢ ላይ! ዛሬውኑ ይግዙ!',
                'type': 'shipping',
                'color': 'blue',
                'link': '/cart'
            },
            {
                'text': '✨ አዲስ የቤት እቃዎች ደርሰዋል! ዘመናዊ ዲዛይን፣ ምርጥ ጥራት!',
                'type': 'new',
                'color': 'green',
                'link': '/category/all'
            },
            {
                'text': '💝 የበዓል ልዩ ቅናሽ! ለቤተሰብዎ ምርጥ ስጦታ ከኤትዮሳዳት ጋር!',
                'type': 'holiday',
                'color': 'purple',
                'link': '/category/all'
            },
            {
                'text': '🛋️ ሶፋ ልዩ ቅናሽ! የምርጥ ሶፋዎች ዋጋ ከ20,000 ብር ጀምሮ!',
                'type': 'product',
                'color': 'orange',
                'link': '/category/ሶፋ'
            },
            {
                'text': '🛏️ አልጋ ሽያጭ! ኪንግ ሳይዝ አልጋ ከ35,000 ብር ጀምሮ!',
                'type': 'product',
                'color': 'brown',
                'link': '/category/አልጋ'
            },
            {
                'text': '🎊 አዲስ ዓመት ልዩ ቅናሽ! እስከ 40% ቅናሽ በሁሉም ምርቶች!',
                'type': 'holiday',
                'color': 'gold',
                'link': '/category/all'
            },
            {
                'text': '🏠 ሙሉ የቤት እቃ ስብስብ በልዩ ቅናሽ! አሁን ይግዙ!',
                'type': 'bundle',
                'color': 'teal',
                'link': '/category/all'
            },
            {
                'text': '📱 በዋትሳፕ በማዘዝ ተጨማሪ 5% ቅናሽ ያግኙ!',
                'type': 'whatsapp',
                'color': 'green',
                'link': '/contact'
            },
            {
                'text': '⭐ የደንበኞች ምርጫ 2024! ኤትዮሳዳት ምርጥ የቤት እቃ አቅራቢ ተመርጧል!',
                'type': 'award',
                'color': 'yellow',
                'link': '/about'
            },
            {
                'text': '🔥 ፈጣን ሽያጭ! የተወሰኑ ምርቶች በ50% ቅናሽ! አያምልጥዎት!',
                'type': 'flash_sale',
                'color': 'red',
                'link': '/category/all'
            },
            {
                'text': '🎁 ለእያንዳንዱ ግዢ ነጻ ስጦታ! ውሱን ብዛት ብቻ!',
                'type': 'gift',
                'color': 'pink',
                'link': '/cart'
            }
        ]
        
        # Optional: Sample media files if they exist
        media_files = []
        if with_media:
            media_dir = 'static/uploads/ads'
            if os.path.exists(media_dir):
                media_files = [f for f in os.listdir(media_dir) 
                              if f.endswith(('.jpg', '.png', '.gif', '.webp', '.mp4'))]
        
        # Clear existing ads
        cursor.execute("DELETE FROM ads")
        print("✅ Cleared existing ads")
        
        # Build insert query based on available columns
        insert_query = "INSERT INTO ads (text"
        placeholders = "%s"
        values = []
        
        if 'media' in columns:
            insert_query += ", media"
            placeholders += ", %s"
        if 'type' in columns:
            insert_query += ", type"
            placeholders += ", %s"
        if 'color' in columns:
            insert_query += ", color"
            placeholders += ", %s"
        if 'link' in columns:
            insert_query += ", link"
            placeholders += ", %s"
        if 'is_active' in columns:
            insert_query += ", is_active"
            placeholders += ", %s"
        if 'sort_order' in columns:
            insert_query += ", sort_order"
            placeholders += ", %s"
        if 'created_at' in columns:
            insert_query += ", created_at"
            placeholders += ", %s"
        
        insert_query += f") VALUES ({placeholders})"
        
        # Insert ads
        inserted_count = 0
        for i, ad in enumerate(ads_data):
            values_list = [ad['text']]
            
            # Add media (randomly assign existing media if available)
            if 'media' in columns:
                media_value = ''
                if with_media and media_files:
                    media_value = random.choice(media_files)
                values_list.append(media_value)
            
            # Add type
            if 'type' in columns:
                values_list.append(ad['type'])
            
            # Add color
            if 'color' in columns:
                values_list.append(ad['color'])
            
            # Add link
            if 'link' in columns:
                values_list.append(ad['link'])
            
            # Add is_active
            if 'is_active' in columns:
                values_list.append(1)
            
            # Add sort_order
            if 'sort_order' in columns:
                values_list.append(i + 1)
            
            # Add created_at
            if 'created_at' in columns:
                values_list.append(datetime.now().isoformat())
            
            try:
                cursor.execute(insert_query, tuple(values_list))
                inserted_count += 1
            except sqlite3.Error as e:
                print(f"⚠️  Error inserting ad {i+1}: {e}")
        
        conn.commit()
        print(f"✅ Inserted {inserted_count} sample advertisements")
        
        # Show ad count
        cursor.execute("SELECT COUNT(*) FROM ads")
        count = cursor.fetchone()[0]
        print(f"📊 Total ads in database: {count}")
        
        # Show all ads with details
        cursor.execute("SELECT id, text, type, is_active FROM ads")
        all_ads = cursor.fetchall()
        print("\n📢 Advertisements:")
        print("-" * 80)
        for ad_id, ad_text, ad_type, is_active in all_ads:
            status = "✓ Active" if is_active else "✗ Inactive"
            text_preview = ad_text[:55] + "..." if len(ad_text) > 55 else ad_text
            print(f"   [{ad_id}] {ad_type.upper():12} | {status:10} | {text_preview}")
        
        print("-" * 80)
        print(f"\n📊 Summary:")
        print(f"   Total: {count} ads")
        
        # Group by type
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM ads 
            GROUP BY type 
            ORDER BY count DESC
        """)
        type_counts = cursor.fetchall()
        if type_counts:
            print("\n   By type:")
            for ad_type, count in type_counts:
                print(f"      - {ad_type}: {count}")
        
        conn.close()
        print("\n✅ Seed completed successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def seed_single_ad(text, ad_type='general', media=None, link=None):
    """Insert a single advertisement"""
    
    db_path = Config.DATABASE_PATH if hasattr(Config, 'DATABASE_PATH') else 'database/semirafashion.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(ads)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Build insert query
        insert_query = "INSERT INTO ads (text"
        placeholders = "%s"
        values = [text]
        
        if media and 'media' in columns:
            insert_query += ", media"
            placeholders += ", %s"
            values.append(media)
        
        if 'type' in columns:
            insert_query += ", type"
            placeholders += ", %s"
            values.append(ad_type)
        
        if link and 'link' in columns:
            insert_query += ", link"
            placeholders += ", %s"
            values.append(link)
        
        if 'is_active' in columns:
            insert_query += ", is_active"
            placeholders += ", %s"
            values.append(1)
        
        if 'created_at' in columns:
            insert_query += ", created_at"
            placeholders += ", %s"
            values.append(datetime.now().isoformat())
        
        insert_query += f") VALUES ({placeholders})"
        
        cursor.execute(insert_query, tuple(values))
        conn.commit()
        
        ad_id = cursor.lastrowid
        conn.close()
        
        print(f"✅ Advertisement added successfully! (ID: {ad_id})")
        return True
        
    except Exception as e:
        print(f"❌ Error adding ad: {e}")
        return False

def show_ads():
    """Display all advertisements in the database"""
    
    db_path = Config.DATABASE_PATH if hasattr(Config, 'DATABASE_PATH') else 'database/semirafashion.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(ads)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Select available columns
        select_columns = ['id', 'text']
        if 'type' in columns:
            select_columns.append('type')
        if 'is_active' in columns:
            select_columns.append('is_active')
        if 'media' in columns:
            select_columns.append('media')
        
        query = f"SELECT {', '.join(select_columns)} FROM ads ORDER BY id"
        cursor.execute(query)
        ads = cursor.fetchall()
        
        if not ads:
            print("📭 No advertisements found.")
            conn.close()
            return
        
        print("\n" + "=" * 80)
        print("📢 ADVERTISEMENTS")
        print("=" * 80)
        
        for ad in ads:
            print(f"\nID: {ad[0]}")
            print(f"Text: {ad[1]}")
            
            if 'type' in columns and len(ad) > 2:
                print(f"Type: {ad[2]}")
            
            if 'is_active' in columns and len(ad) > 3:
                status = "✓ Active" if ad[3] else "✗ Inactive"
                print(f"Status: {status}")
            
            if 'media' in columns and len(ad) > 4 and ad[4]:
                print(f"Media: {ad[4]}")
        
        print("\n" + "=" * 80)
        print(f"Total: {len(ads)} ads")
        print("=" * 80)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import argparse
    
    # Command line argument parsing
    parser = argparse.ArgumentParser(description='Seed advertisements for SEMIRA FASHION')
    parser.add_argument('--media', action='store_true', help='Try to assign existing media files')
    parser.add_argument('--show', action='store_true', help='Show existing ads')
    parser.add_argument('--clear', action='store_true', help='Clear all ads before seeding')
    parser.add_argument('--count', type=int, default=10, help='Number of ads to seed (default: 10)')
    
    args = parser.parse_args()
    
    if args.show:
        show_ads()
    else:
        print("\n" + "=" * 60)
        print("🌱 ETHIOSADAT ADVERTISEMENT SEEDER")
        print("=" * 60)
        
        if args.clear:
            response = input("⚠️  Clear all existing ads before seeding? (yes/no): ")
            if response.lower() == 'yes':
                db_path = Config.DATABASE_PATH if hasattr(Config, 'DATABASE_PATH') else 'database/semirafashion.db'
                conn = sqlite3.connect(db_path)
                conn.execute("DELETE FROM ads")
                conn.commit()
                conn.close()
                print("✅ Cleared existing ads")
            else:
                print("Keeping existing ads")
        
        seed_ads(with_media=args.media)
        
        print("\n💡 To view ads, run: python seed_ads.py --show")