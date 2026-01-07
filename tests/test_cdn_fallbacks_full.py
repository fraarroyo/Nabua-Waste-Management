from bs4 import BeautifulSoup
import pytest
from app import app, db, Barangay, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    import uuid
    with app.app_context():
        db.create_all()
        unique = uuid.uuid4().hex[:8]
        br = Barangay(name=f'Test {unique}', code=f'TEST_{unique}', municipality='Nabua', province='Camarines Sur')
        admin = User(username=f'test_admin_{unique}', email=f'test_admin_{unique}@example.com', role='admin', full_name='Admin')
        admin.set_password('admin123')
        db.session.add_all([br, admin])
        db.session.commit()
    with app.test_client() as client:
        yield client



def test_cdn_warning_banner_present(client):
    # ensure app has minimal data
    rv = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert rv.status_code == 200

    res = client.get('/')
    assert res.status_code == 200
    soup = BeautifulSoup(res.data, 'html.parser')
    banner = soup.find(id='cdn-warning')
    assert banner is not None
    assert 'Copy diagnostics' in banner.text


def test_scan_qr_uses_full_jsqr_fallback(client):
    rv = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert rv.status_code == 200

    res = client.get('/scan_qr')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    # Confirm the onerror loads the full local copy
    assert '/static/vendor/js/jsQR.full.js' in html
