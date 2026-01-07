import pytest
from app import app, db, User, Barangay, WasteItem, WasteTracking
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    import uuid
    with app.app_context():
        db.create_all()
        # create sample data (use UUIDs to avoid conflicts with existing DB state)
        unique = uuid.uuid4().hex[:8]
        barangay = Barangay(name=f'Test Barangay {unique}', code=f'TB_TEST_{unique}', municipality='Nabua', province='Camarines Sur')
        admin = User(username=f'test_admin_{unique}', email=f'test_admin_{unique}@example.com', role='admin', full_name='Admin')
        admin.set_password('admin123')
        collector = User(username=f'test_collector_{unique}', email=f'test_collector_{unique}@example.com', role='collector', full_name='Collector')
        collector.set_password('collector123')
        db.session.add_all([barangay, admin, collector])
        db.session.commit()
    with app.test_client() as client:
        yield client


def test_mark_collected_stores_coordinates(client):
    import uuid
    with app.app_context():
        barangay = Barangay.query.first()
        unique = uuid.uuid4().hex[:8]
        item = WasteItem(item_id=f'WM{unique}', item_name='Test Item', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='Test Address')
        db.session.add(item)
        db.session.commit()

        # login as admin (admin can act as collector)
        rv = client.post('/login', data={'username': 'test_admin', 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        rv2 = client.post(f'/mark_collected/{item.item_id}', data={'latitude': '13.1', 'longitude': '123.1'}, follow_redirects=True)
        # mark_collected redirects back on success
        assert rv2.status_code == 200

        t = WasteTracking.query.filter_by(waste_item_id=item.id).first()
        assert t is not None
        assert round(t.latitude, 4) == 13.1
        assert round(t.longitude, 4) == 123.1


def test_api_waste_locations_returns_items(client):
    with app.app_context():
        barangay = Barangay.query.first()
        # reuse any item created earlier in this test session if available
        item = WasteItem.query.first()
        if not item:
            unique = 'manual'
            item = WasteItem(item_id=f'WM{unique}', item_name='Test Item', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='Test Address')
            db.session.add(item)
            db.session.commit()

        tracking = WasteTracking(waste_item_id=item.id, status='collected', latitude=13.1, longitude=123.1, updated_by=None)
        db.session.add(tracking)
        db.session.commit()

        rv = client.post('/login', data={'username': 'test_admin', 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        resp = client.get('/api/waste/locations')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'items' in data
        assert any(it['item_id'] == item.item_id for it in data['items'])


def test_api_waste_locations_excludes_non_coverage_items(client):
    """Items from barangays outside Nabua, Camarines Sur should not appear in tracking responses."""
    with app.app_context():
        # Create an out-of-coverage barangay and an item in it
        import uuid as _uuid
        other_brgy = Barangay(name='Other', code=f'OTHER_{_uuid.uuid4().hex[:6].upper()}', municipality='OtherTown', province='OtherProvince')
        db.session.add(other_brgy)
        db.session.commit()

        import uuid as _uuid2
        unique = _uuid2.uuid4().hex[:8]
        out_item = WasteItem(item_id=f'WM{unique}', item_name='Outside Item', waste_type='recyclable', is_sorted=True, barangay_id=other_brgy.id, address='Far Away')
        db.session.add(out_item)
        db.session.commit()

        tracking = WasteTracking(waste_item_id=out_item.id, status='collected', latitude=1.0, longitude=2.0)
        db.session.add(tracking)
        db.session.commit()

        # login as admin
        rv = client.post('/login', data={'username': 'test_admin', 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        resp = client.get('/api/waste/locations')
        assert resp.status_code == 200
        data = resp.get_json()
        # The outside item should NOT be present
        assert not any(it['item_id'] == out_item.item_id for it in data['items'])


def test_swap_coords_on_mark_collected(client):
    """If coordinates are submitted swapped (lat > 90), auto-swap to correct them."""
    import uuid
    with app.app_context():
        barangay = Barangay.query.first()
        unique = uuid.uuid4().hex[:8]
        item = WasteItem(item_id=f'WM{unique}', item_name='Swap Test Item', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='Swap Address')
        db.session.add(item)
        db.session.commit()

        admin = User.query.filter_by(role='admin').first()
        rv = client.post('/login', data={'username': admin.username, 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        # Submit swapped coords (lat looks like longitude)
        rv2 = client.post(f'/mark_collected/{item.item_id}', data={'latitude': '123.1', 'longitude': '13.1'}, follow_redirects=False)
        assert rv2.status_code in (302, 303, 307)  # redirect on success

        t = WasteTracking.query.filter_by(waste_item_id=item.id).first()
        assert t is not None
        # Expect coordinates were swapped by the server
        assert round(t.latitude, 4) == 13.1
        assert round(t.longitude, 4) == 123.1


def test_invalid_coords_cleared(client):
    """If coordinates are clearly invalid, they should be dropped (stored as NULL)."""
    import uuid
    with app.app_context():
        barangay = Barangay.query.first()
        unique = uuid.uuid4().hex[:8]
        item = WasteItem(item_id=f'WM{unique}', item_name='Invalid Test Item', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='Nowhere')
        db.session.add(item)
        db.session.commit()

        admin = User.query.filter_by(role='admin').first()
        rv = client.post('/login', data={'username': admin.username, 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        # Submit clearly invalid coords
        rv2 = client.post(f'/mark_collected/{item.item_id}', data={'latitude': '999', 'longitude': '999'}, follow_redirects=False)
        assert rv2.status_code in (302, 303, 307)  # redirect on success

        t = WasteTracking.query.filter_by(waste_item_id=item.id).first()
        assert t is not None
        assert t.latitude is None
        assert t.longitude is None


def test_api_waste_track_normalizes(client):
    """API endpoint should normalize swapped coordinates as well."""
    import uuid
    with app.app_context():
        barangay = Barangay.query.first()
        unique = uuid.uuid4().hex[:8]
        item = WasteItem(item_id=f'WM{unique}', item_name='API Swap Test', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='API Address')
        db.session.add(item)
        db.session.commit()

        admin = User.query.filter_by(role='admin').first()
        rv = client.post('/login', data={'username': admin.username, 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        payload = {'item_id': item.item_id, 'status': 'collected', 'latitude': '123.1', 'longitude': '13.1'}
        resp = client.post('/api/waste/track', json=payload)
        assert resp.status_code == 200

        t = WasteTracking.query.filter_by(waste_item_id=item.id).first()
        assert t is not None
        assert round(t.latitude,4) == 13.1
        assert round(t.longitude,4) == 123.1


def test_api_waste_track_returns_warning_on_drop(client):
    """API should return a warning field when coords are invalid/dropped and tag the notes."""
    import uuid
    with app.app_context():
        barangay = Barangay.query.first()
        unique = uuid.uuid4().hex[:8]
        item = WasteItem(item_id=f'WM{unique}', item_name='API Drop Test', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='API Address')
        db.session.add(item)
        db.session.commit()

        admin = User.query.filter_by(role='admin').first()
        rv = client.post('/login', data={'username': admin.username, 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        payload = {'item_id': item.item_id, 'status': 'collected', 'latitude': '999', 'longitude': '999'}
        resp = client.post('/api/waste/track', json=payload)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'warning' in data

        t = WasteTracking.query.filter_by(waste_item_id=item.id).first()
        assert t is not None
        assert '[COORD_ISSUE: dropped]' in (t.notes or '')


def test_update_status_ajax_includes_warning_on_swap(client):
    """AJAX update_status should include a warning message when coords are swapped."""
    import uuid
    with app.app_context():
        barangay = Barangay.query.first()
        unique = uuid.uuid4().hex[:8]
        item = WasteItem(item_id=f'WM{unique}', item_name='AJAX Swap', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='AJAX Addr')
        db.session.add(item)
        db.session.commit()

        admin = User.query.filter_by(role='admin').first()
        rv = client.post('/login', data={'username': admin.username, 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        resp = client.post(f'/update_status/{item.item_id}', data={'status': 'in_transit', 'device_latitude': '123.0', 'device_longitude': '13.0'}, headers={'X-Requested-With': 'XMLHttpRequest'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'warning' in data

        t = WasteTracking.query.filter_by(waste_item_id=item.id).order_by(WasteTracking.timestamp.desc()).first()
        assert t is not None
        assert '[COORD_ISSUE: swapped]' in (t.notes or '')


def test_api_waste_track_includes_warning_on_swap(client):
    """API should include a warning when device coords are swapped and corrected."""
    import uuid
    with app.app_context():
        barangay = Barangay.query.first()
        unique = uuid.uuid4().hex[:8]
        item = WasteItem(item_id=f'WM{unique}', item_name='API Swap Warn', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='API Addr')
        db.session.add(item)
        db.session.commit()

        admin = User.query.filter_by(role='admin').first()
        rv = client.post('/login', data={'username': admin.username, 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        payload = {'item_id': item.item_id, 'status': 'collected', 'latitude': '123.4', 'longitude': '13.4'}
        resp = client.post('/api/waste/track', json=payload)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'warning' in data

        t = WasteTracking.query.filter_by(waste_item_id=item.id).first()
        assert t is not None
        assert '[COORD_ISSUE: swapped]' in (t.notes or '')


def test_tracking_map_is_restricted_to_nabua(client):
    """Tracking map HTML should include Nabua bounds to restrict view."""
    # login as admin to access the tracking view
    rv = client.post('/login', data={'username': 'test_admin', 'password': 'admin123'}, follow_redirects=True)
    assert rv.status_code == 200

    resp = client.get('/tracking')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'nabuaBounds' in html
    # ensure the numeric bounds appear in the template
    assert '13.15' in html and '123.45' in html


def test_scan_qr_video_has_playsinline(client):
    """Scan QR page's video element should include playsinline/muted to aid mobile autoplay"""
    rv = client.post('/login', data={'username': 'test_admin', 'password': 'admin123'}, follow_redirects=True)
    assert rv.status_code == 200

    resp = client.get('/scan_qr')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert '<video' in html
    assert 'playsinline' in html or 'muted' in html


def test_scan_qr_shows_camera_diagnostics_area(client):
    """Scan QR page should include a diagnostics container to help debug camera issues."""
    rv = client.post('/login', data={'username': 'test_admin', 'password': 'admin123'}, follow_redirects=True)
    assert rv.status_code == 200

    resp = client.get('/scan_qr')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'camera-diagnostics' in html
    assert 'video-device-select' in html


def test_collection_team_starts_location_pings(client):
    """Collection team page should contain a collector location status element and JS that posts to /collector_location"""
    import uuid
    with app.app_context():
        # create a collector user and login
        unique = uuid.uuid4().hex[:8]
        c = User(username=f'ping_collector_{unique}', email=f'ping_{unique}@example.com', role='collector', full_name='Ping Collector')
        c.set_password('pwdping')
        db.session.add(c)
        db.session.commit()

        rv = client.post('/login', data={'username': c.username, 'password': 'pwdping'}, follow_redirects=True)
        assert rv.status_code == 200

        resp = client.get('/collection_team')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'collector-location-status' in html
        assert '/collector_location' in html


def test_update_status_stores_device_coords(client):
    """When updating status via the collector interface, device coordinates should be stored if provided."""
    import uuid
    with app.app_context():
        barangay = Barangay.query.first()
        unique = uuid.uuid4().hex[:8]
        item = WasteItem(item_id=f'WM{unique}', item_name='UpdateCoords Item', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='Update Address')
        db.session.add(item)
        db.session.commit()

        admin = User.query.filter_by(role='admin').first()
        rv = client.post('/login', data={'username': admin.username, 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        # Post with explicit device coords
        rv2 = client.post(f'/update_status/{item.item_id}', data={'status': 'in_transit', 'device_latitude': '13.77', 'device_longitude': '123.88'})
        assert rv2.status_code in (200, 302, 303, 307)

        t = WasteTracking.query.filter_by(waste_item_id=item.id).order_by(WasteTracking.timestamp.desc()).first()
        assert t is not None
        assert round(t.latitude, 4) == 13.77
        assert round(t.longitude, 4) == 123.88


def test_mark_collected_shows_notification_on_swap(client):
    """When mark_collected auto-swaps coords, the user should see a warning and note should be tagged."""
    import uuid
    with app.app_context():
        barangay = Barangay.query.first()
        unique = uuid.uuid4().hex[:8]
        item = WasteItem(item_id=f'WM{unique}', item_name='Swap Notify', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='Swap Notif Addr')
        db.session.add(item)
        db.session.commit()

        admin = User.query.filter_by(role='admin').first()
        rv = client.post('/login', data={'username': admin.username, 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        resp = client.post(f'/mark_collected/{item.item_id}', data={'latitude': '123.0', 'longitude': '13.0'}, follow_redirects=True)
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'Device coordinates looked swapped' in html

        t = WasteTracking.query.filter_by(waste_item_id=item.id).first()
        assert t is not None
        assert '[COORD_ISSUE: swapped]' in (t.notes or '')


def test_mark_collected_shows_notification_on_drop(client):
    """When mark_collected drops invalid coords, the user should see a warning and note should be tagged."""
    import uuid
    with app.app_context():
        barangay = Barangay.query.first()
        unique = uuid.uuid4().hex[:8]
        item = WasteItem(item_id=f'WM{unique}', item_name='Drop Notify', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='Drop Addr')
        db.session.add(item)
        db.session.commit()

        admin = User.query.filter_by(role='admin').first()
        rv = client.post('/login', data={'username': admin.username, 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        resp = client.post(f'/mark_collected/{item.item_id}', data={'latitude': '999', 'longitude': '999'}, follow_redirects=True)
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'Device coordinates were invalid' in html

        t = WasteTracking.query.filter_by(waste_item_id=item.id).first()
        assert t is not None
        assert '[COORD_ISSUE: dropped]' in (t.notes or '')


def test_api_waste_track_prefers_device_coords(client):
    """API should prefer device_latitude/device_longitude if provided."""
    import uuid
    with app.app_context():
        barangay = Barangay.query.first()
        unique = uuid.uuid4().hex[:8]
        item = WasteItem(item_id=f'WM{unique}', item_name='API Device Pref', waste_type='recyclable', is_sorted=True, barangay_id=barangay.id, address='API DevAddr')
        db.session.add(item)
        db.session.commit()

        admin = User.query.filter_by(role='admin').first()
        rv = client.post('/login', data={'username': admin.username, 'password': 'admin123'}, follow_redirects=True)
        assert rv.status_code == 200

        # Send conflicting coords; device_* should be used
        payload = {
            'item_id': item.item_id,
            'status': 'collected',
            'latitude': '1.1',
            'longitude': '2.2',
            'device_latitude': '13.33',
            'device_longitude': '123.33'
        }
        resp = client.post('/api/waste/track', json=payload)
        assert resp.status_code == 200

        t = WasteTracking.query.filter_by(waste_item_id=item.id).first()
        assert t is not None
        assert round(t.latitude,4) == 13.33
        assert round(t.longitude,4) == 123.33


def test_barangay_tracking_map_is_restricted_to_nabua(client):
    """Barangay tracking map HTML should include Nabua bounds to restrict view."""
    # login as a barangay user (test_collector acts as collector/admin in tests)
    rv = client.post('/login', data={'username': 'test_admin', 'password': 'admin123'}, follow_redirects=True)
    assert rv.status_code == 200

    resp = client.get('/my_tracking')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'nabuaBounds' in html
    assert '13.15' in html and '123.45' in html


def test_collector_location_endpoint_stores_coords(client):
    """Collectors can POST their device location and it is stored on their user record."""
    with app.app_context():
        # Create a collector with known credentials for this test
        import uuid
        unique = uuid.uuid4().hex[:8]
        collector = User(username=f'test_collector_loc_{unique}', email=f'loc_{unique}@example.com', role='collector', full_name='Collector Loc')
        collector.set_password('pwd123')
        db.session.add(collector)
        db.session.commit()

        # login as the collector
        rv = client.post('/login', data={'username': collector.username, 'password': 'pwd123'}, follow_redirects=True)
        assert rv.status_code == 200

        resp = client.post('/collector_location', json={'device_latitude': '13.999', 'device_longitude': '123.999'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get('success') is True

        # reload user from DB
        c = User.query.get(collector.id)
        assert round(c.last_latitude, 3) == 13.999
        assert round(c.last_longitude, 3) == 123.999
        assert c.last_seen is not None


def test_api_collectors_returns_only_same_barangay(client):
    """API /api_collectors should only return collectors for the requested barangay and enforce access control."""
    import uuid
    with app.app_context():
        # Create two barangays and collectors
        unique = uuid.uuid4().hex[:8]
        b1 = Barangay(name=f'B1 {unique}', code=f'B1_{unique}', municipality='Nabua', province='Camarines Sur')
        b2 = Barangay(name=f'B2 {unique}', code=f'B2_{unique}', municipality='Nabua', province='Camarines Sur')
        db.session.add_all([b1, b2])
        db.session.commit()

        c1 = User(username=f'collector_b1_{unique}', email=f'c1_{unique}@example.com', role='collector', full_name='Collector B1', barangay_id=b1.id)
        c1.set_password('pwd123')
        c2 = User(username=f'collector_b2_{unique}', email=f'c2_{unique}@example.com', role='collector', full_name='Collector B2', barangay_id=b2.id)
        c2.set_password('pwd123')
        barangay_user = User(username=f'barangay_{unique}', email=f'brgy_{unique}@example.com', role='barangay', full_name='Barangay User', barangay_id=b1.id)
        barangay_user.set_password('pwd123')
        db.session.add_all([c1, c2, barangay_user])
        db.session.commit()

        # login as barangay_user (for b1)
        rv = client.post('/login', data={'username': barangay_user.username, 'password': 'pwd123'}, follow_redirects=True)
        assert rv.status_code == 200

        resp = client.get(f'/api_collectors?barangay_id={b1.id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get('success') is True
        collectors = data.get('collectors')
        assert any(c['username'] == c1.username for c in collectors)
        assert not any(c['username'] == c2.username for c in collectors)


def test_my_tracking_includes_api_collectors_fetch(client):
    """The barangay tracking template should include JS that fetches the collectors endpoint."""
    with app.app_context():
        # Create a barangay user with known credentials for this test
        import uuid
        unique = uuid.uuid4().hex[:8]
        barangay = Barangay(name=f'BRGY_{unique}', code=f'BR_{unique}', municipality='Nabua', province='Camarines Sur')
        db.session.add(barangay)
        db.session.commit()

        brgy_user = User(username=f'brgy_user_{unique}', email=f'brgy_{unique}@example.com', role='barangay', full_name='BRGY User', barangay_id=barangay.id)
        brgy_user.set_password('pwdbrgy')
        db.session.add(brgy_user)
        db.session.commit()

        rv = client.post('/login', data={'username': brgy_user.username, 'password': 'pwdbrgy'}, follow_redirects=True)
        assert rv.status_code == 200

        resp = client.get('/my_tracking')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'api_collectors' in html
        assert 'collector-' in html


def test_barangay_tracking_uses_recency_icons(client):
    """Ensure the barangay tracking template includes collector icon color logic for recency."""
    with app.app_context():
        import uuid
        unique = uuid.uuid4().hex[:8]
        barangay = Barangay(name=f'BRGY_ICONS_{unique}', code=f'BIC_{unique}', municipality='Nabua', province='Camarines Sur')
        db.session.add(barangay)
        db.session.commit()

        brgy_user = User(username=f'brgy_icons_{unique}', email=f'brgy_icons_{unique}@example.com', role='barangay', full_name='BRGY ICONS', barangay_id=barangay.id)
        brgy_user.set_password('pwdbrgy')
        db.session.add(brgy_user)
        db.session.commit()

        rv = client.post('/login', data={'username': brgy_user.username, 'password': 'pwdbrgy'}, follow_redirects=True)
        assert rv.status_code == 200

        resp = client.get('/my_tracking')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        # Template should include the collector icon helper and references to marker-icon
        assert 'getCollectorIcon' in html
        assert 'marker-icon-' in html


def test_barangay_tracking_sse_filters_collectors(client):
    """Ensure the barangay tracking SSE handler filters collector_location events by barangay."""
    with app.app_context():
        # Reuse a barangay user for testing
        import uuid
        unique = uuid.uuid4().hex[:8]
        barangay = Barangay(name=f'BRGY2_{unique}', code=f'BR2_{unique}', municipality='Nabua', province='Camarines Sur')
        db.session.add(barangay)
        db.session.commit()

        brgy_user = User(username=f'brgy_user2_{unique}', email=f'brgy2_{unique}@example.com', role='barangay', full_name='BRGY User 2', barangay_id=barangay.id)
        brgy_user.set_password('pwdbrgy')
        db.session.add(brgy_user)
        db.session.commit()

        rv = client.post('/login', data={'username': brgy_user.username, 'password': 'pwdbrgy'}, follow_redirects=True)
        assert rv.status_code == 200

        resp = client.get('/my_tracking')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        # The SSE handler should include a check that ignores events for other barangays
        assert 'if (myBarangay !== null && obj.barangay_id !== myBarangay) return;' in html
        assert 'collector_location' in html
