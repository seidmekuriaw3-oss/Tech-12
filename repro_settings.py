import os
from app import app
from database.db import init_db

os.environ['ADMIN_USERNAME'] = 'admin'
os.environ['ADMIN_PASSWORD'] = '1234'
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['SESSION_SECRET'] = 'test-secret'

with app.app_context():
    init_db()

client = app.test_client()
resp = client.post('/login', data={'username': 'admin', 'password': '1234'}, follow_redirects=True)
print('login_status', resp.status_code)
resp2 = client.get('/admin/settings')
print('settings_status', resp2.status_code)
print(resp2.get_data(as_text=True)[:2000])
