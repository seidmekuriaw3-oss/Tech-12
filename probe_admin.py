import requests

base = 'http://127.0.0.1:5000'
for path in ['/admin/login','/admin/dashboard','/admin/products','/admin/ads','/admin/orders','/admin/users','/admin/reviews']:
    try:
        r = requests.get(base + path, timeout=8)
        print(path, r.status_code)
        print(r.text[:400].replace('\n',' ')[:400])
    except Exception as e:
        print(path, 'ERR', e)
