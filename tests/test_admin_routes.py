from database.db import get_db


def test_admin_product_create_uses_name_en_for_display_name(client, auth):
    auth.login()

    response = client.post('/admin/products/create', data={
        'name_am': 'ሙከራ ምርት',
        'name_en': 'Sample Product',
        'price': '120',
        'stock_quantity': '5',
        'category_id': '1',
        'csrf_token': auth.csrf_token(),
    }, follow_redirects=True)

    assert response.status_code == 200

    with client.application.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name, name_en FROM products WHERE name_en = %s ORDER BY id DESC LIMIT 1", ('Sample Product',))
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == 'Sample Product'
    assert row[1] == 'Sample Product'


def test_admin_ad_create_uses_ad_text_for_description(client, auth):
    auth.login()

    response = client.post('/admin/ads/create', data={
        'ad_text': 'Spring offer for customers',
        'title': 'Spring Sale',
        'link': 'https://example.com',
        'csrf_token': auth.csrf_token(),
    }, follow_redirects=True)

    assert response.status_code == 200

    with client.application.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT title, description FROM advertisements WHERE title = %s ORDER BY id DESC LIMIT 1", ('Spring Sale',))
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == 'Spring Sale'
    assert row[1] == 'Spring offer for customers'


def test_admin_settings_page_renders_for_authenticated_admin(client):
    with client.session_transaction() as sess:
        sess['admin'] = True

    response = client.get('/admin/settings')

    assert response.status_code == 200
    assert b'Admin Settings' in response.data
