from tests.conftest import TestConfig
from app import app as flask_app
from database.db import init_db
import os

flask_app.config.from_object(TestConfig)
flask_app.config.update({'TESTING': True, 'SERVER_NAME': 'localhost.test'})

with flask_app.app_context():
    init_db()

client = flask_app.test_client()

with client.session_transaction() as sess:
    sess['_csrf_token'] = 'test-csrf-token'

resp = client.post('/admin/login', data={
    'username': 'admin',
    'password': 'test1234',
    'csrf_token': 'test-csrf-token',
}, follow_redirects=True)
print('login status', resp.status_code)
print(resp.request.path)
print(resp.data[:500].decode('utf-8', 'ignore'))

with client.session_transaction() as sess:
    print('session admin', sess.get('admin'))
    print('session username', sess.get('admin_username'))

resp2 = client.post('/admin/products/create', data={
    'name_am': 'ሙከራ ምርት',
    'name_en': 'Sample Product',
    'price': '120',
    'stock_quantity': '5',
    'category_id': '1',
    'csrf_token': 'test-csrf-token',
}, follow_redirects=True)
print('create status', resp2.status_code)
print('create path', resp2.request.path)
print(resp2.data[:1000].decode('utf-8', 'ignore'))

with flask_app.app_context():
    from database.db import get_db
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    print('products count', cur.fetchone()[0])
    cur.execute("SELECT name, name_en FROM products WHERE name_en = %s ORDER BY id DESC LIMIT 1", ('Sample Product',))
    print('row', cur.fetchone())
