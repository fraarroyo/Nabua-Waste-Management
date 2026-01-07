import requests, re, sys
BASE='http://127.0.0.1:5000'
# create admin item
s=requests.Session()
print('Logging in admin')
res=s.post(BASE+'/login', data={'username':'admin','password':'admin123'})
print('login', res.status_code)
# add waste item
resp=s.post(BASE+'/add_waste', data={'waste_type':'recyclable','item_name':'SMOKE TEST ITEM','weight':'1.0','barangay_id':'1','address':'Test Address','contact_person':'Tester','contact_number':'09171234567','is_sorted':'true'})
print('add_waste', resp.status_code)
r=s.get(BASE+'/registered_items')
m=re.search(r'WM\d{14}', r.text)
if not m:
    print('No item found on registered_items, trying pending list')
    r2=s.get(BASE+'/collection_team')
    m=re.search(r'WM\d{14}', r2.text)
    if not m:
        print('No pending item found; cannot continue')
        sys.exit(1)
item_id=m.group(0)
print('Found item_id', item_id)
# mark collected using admin session (admin has collector privileges)
res3=s.post(f'{BASE}/mark_collected/{item_id}', data={'latitude':'13.4295','longitude':'123.2532'}, allow_redirects=False)
print('mark_collected', res3.status_code, res3.headers.get('Location'))
# query locations api and show items
s3=requests.Session()
s3.post(BASE+'/login', data={'username':'admin','password':'admin123'})
api=s3.get(BASE+'/api/waste/locations')
print('api_waste_locations', api.status_code, api.json())
