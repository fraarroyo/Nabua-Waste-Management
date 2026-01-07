import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, db, User, Barangay, WasteItem, WasteTracking
import uuid

with app.app_context():
    db.create_all()
    unique = uuid.uuid4().hex[:8]
    barangay = Barangay(name=f'Debug Barangay {unique}', code=f'DB_{unique}', municipality='Nabua', province='Camarines Sur')
    admin = User(username=f'debug_admin_{unique}', email=f'debug_admin_{unique}@example.com', role='admin', full_name='Admin')
    admin.set_password('admin123')
    db.session.add_all([barangay, admin])
    db.session.commit()
    admin_username = admin.username
    barangay_id = barangay.id

with app.test_client() as client:
    # login admin
    rv = client.post('/login', data={'username': admin_username, 'password': 'admin123'}, follow_redirects=True)
    print('login status', rv.status_code)
    # create item
    item = WasteItem(item_id=f'WM{unique}', item_name='Debug Item', waste_type='recyclable', is_sorted=True, barangay_id=barangay_id, address='Debug Addr')
    with app.app_context():
        db.session.add(item)
        db.session.commit()
    # mark collected
    rv2 = client.post(f'/mark_collected/{item.item_id}', data={'latitude': '13.1', 'longitude': '123.1'}, follow_redirects=True)
    print('mark status', rv2.status_code)
    print('mark response length', len(rv2.data))
    print('recent tracking entries:', [(t.id, t.latitude, t.longitude) for t in WasteTracking.query.filter_by(waste_item_id=item.id).all()])
