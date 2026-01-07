import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

with app.test_client() as c:
    # login as admin (admin user exists)
    res = c.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    print('login status', res.status_code)
    res2 = c.get('/collection_team')
    print('/collection_team status', res2.status_code)
    print('response length', len(res2.get_data(as_text=True)))
    if res2.status_code != 200:
        print(res2.get_data(as_text=True)[:2000])