#!/usr/bin/env python
"""Quick test to verify ad rendering fix."""

from app import app
from database.db import get_db

def test_translated_ads():
    """Test that translated ad titles and descriptions render on the home page."""
    with app.test_client() as client:
        with app.app_context():
            db = get_db()
            cur = db.cursor()
            
            # Clean up any existing test ad
            cur.execute("DELETE FROM advertisements WHERE title_am = %s", ('ለበጋ ቅናሽ',))
            
            # Insert test ad with Amharic title and description
            cur.execute("""
                INSERT INTO advertisements (
                    title, title_am, description, description_am, link, sort_order, is_active,
                    start_date, end_date, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW() + INTERVAL '7 days', NOW())
            """, ('', 'ለበጋ ቅናሽ', '', 'እስከ 30% ቅናሽ በምርቶች', '/products', 1, 1))
            db.commit()
            
            # Verify ad was inserted
            cur.execute("SELECT id, title, title_am, description, description_am FROM advertisements WHERE title_am = %s", ('ለበጋ ቅናሽ',))
            ads = cur.fetchall()
            print(f"✓ Inserted ad: {ads}")
        
        # Get home page
        response = client.get('/')
        assert response.status_code == 200, f"Home page returned {response.status_code}"
        print(f"✓ Home page status: {response.status_code}")
        
        html = response.get_data(as_text=True)
        
        # Check if ad title is in response
        if 'ለበጋ ቅናሽ' in html:
            print("✓ Ad title 'ለበጋ ቅናሽ' found in HTML")
        else:
            print("✗ Ad title 'ለበጋ ቅናሽ' NOT found in HTML")
            # Print a sample of the HTML near the ads section
            idx = html.find('ads')
            if idx > 0:
                print(f"HTML around 'ads': {html[max(0,idx-200):idx+500]}")
        
        # Check if ad description is in response
        if 'እስከ 30% ቅናሽ በምርቶች' in html:
            print("✓ Ad description 'እስከ 30% ቅናሽ በምርቶች' found in HTML")
        else:
            print("✗ Ad description 'እስከ 30% ቅናሽ በምርቶች' NOT found in HTML")
        
        assert 'ለበጋ ቅናሽ' in html, "Ad title not found in rendered HTML"
        assert 'እስከ 30% ቅናሽ በምርቶች' in html, "Ad description not found in rendered HTML"
        
        print("✓ All assertions passed!")

if __name__ == '__main__':
    test_translated_ads()
    print("\n✅ Test completed successfully!")
