import os
import sys
from pathlib import Path
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from app import app
from config import Config
from database.db import init_db, get_db

class TestConfig(Config):
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False
    DEBUG = False
    ADMIN_PASSWORD = 'test1234'

app.config.from_object(TestConfig)
app.config.update({'TESTING': True, 'SERVER_NAME': 'localhost.test'})

with app.app_context():
    init_db()

client = app.test_client()

with client.session_transaction() as sess:
    sess['_csrf_token'] = 'test-csrf-token'

login_resp = client.post('/admin/login', data={
    'username': 'admin',
    'password': 'test1234',
    'csrf_token': 'test-csrf-token',
}, follow_redirects=True)

resp = client.post('/admin/products/create', data={
    'name_am': 'ሙከራ ምርት',
    'name_en': 'Sample Product',
    'price': '120',
    'stock_quantity': '5',
    'category_id': '1',
    'csrf_token': 'test-csrf-token',
}, follow_redirects=True)

with app.app_context():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    product_count = cur.fetchone()[0]
    cur.execute("SELECT name, name_en FROM products WHERE name_en = %s ORDER BY id DESC LIMIT 1", ('Sample Product',))
    row = cur.fetchone()

report = []
report.append(f"login_status={login_resp.status_code}")
report.append(f"create_status={resp.status_code}")
report.append(f"product_count={product_count}")
report.append(f"row={row}")
report.append('--- login body snippet ---')
report.append(login_resp.get_data(as_text=True)[:2000])
report.append('--- create body snippet ---')
report.append(resp.get_data(as_text=True)[:4000])
Path('debug_admin_create_report.txt').write_text('\n'.join(report), encoding='utf-8')
print('wrote debug_admin_create_report.txt')
