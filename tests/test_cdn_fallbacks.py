import re
import pytest
from bs4 import BeautifulSoup
from app import app, db, Barangay, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    import uuid
    with app.app_context():
        db.create_all()
        # create minimal data to satisfy templates that expect barangays/users
        unique = uuid.uuid4().hex[:8]
        br = Barangay(name=f'Test {unique}', code=f'TEST_{unique}', municipality='Nabua', province='Camarines Sur')
        admin = User(username=f'test_admin_{unique}', email=f'test_admin_{unique}@example.com', role='admin', full_name='Admin')
        admin.set_password('admin123')
        db.session.add_all([br, admin])
        db.session.commit()
    with app.test_client() as client:
        yield client



def test_scan_qr_includes_jsqr_fallback(client):
    # login as admin (admin has access to collector pages in this app)
    rv = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert rv.status_code == 200

    res = client.get('/scan_qr')
    assert res.status_code == 200
    soup = BeautifulSoup(res.data, 'html.parser')
    scripts = soup.find_all('script')
    srcs = [s.get('src') for s in scripts if s.get('src')]
    # Check that the CDN script is present and that local fallback is referenced in inline onerror
    assert any('jsqr' in (src or '') for src in srcs)
    # find inline script tag where the CDN <script> contains onerror referencing the local fallback
    assert any('/static/vendor/js/jsQR.js' in (s.get('onerror') or '') for s in scripts)


def test_base_includes_bootstrap_local_fallback(client):
    # login so '/' returns the dashboard
    rv = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert rv.status_code == 200

    res = client.get('/')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert '/static/vendor/css/bootstrap.min.css' in html
    assert 'bootstrap.bundle.min.js' in html
