import requests, re

s = requests.Session()
p = s.get('http://127.0.0.1:5001/admin/login/')
m = re.search(r'name=["\']csrf_guard["\']\s+value=["\']([^"\']+)["\']', p.text)
login_resp = s.post('http://127.0.0.1:5001/admin/login/?next=', data={'email': 'admin@gmail.com', 'password': 'admin123', 'csrf_guard': m.group(1)})
print('Login URL:', login_resp.url)
print('Cookies:', s.cookies.get_dict())
r_dash = s.get('http://127.0.0.1:5001/admin/dashboard/')
print('Dashboard status:', r_dash.status_code)
r_part = s.get('http://127.0.0.1:5001/admin/manage/partners/', allow_redirects=False)
print('Partners status:', r_part.status_code)
print('Partners headers:', dict(r_part.headers))
if r_part.status_code != 200:
    print('Content:', r_part.text[:500])
