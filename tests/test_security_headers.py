import pytest
from app_enhanced import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Ensure there's no interference from other tests if we run the full suite
    with app.test_client() as client:
        yield client

def test_security_headers(client):
    """Verify that the add_security_headers function appends the expected headers to the response."""
    # We can hit any endpoint, e.g., the root healthcheck endpoint
    response = client.get('/')

    assert response.status_code == 200
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'DENY'
    assert response.headers.get('X-XSS-Protection') == '1; mode=block'

    csp = response.headers.get('Content-Security-Policy', '')
    assert "default-src 'self'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "script-src 'self' 'unsafe-inline'" in csp
    assert "img-src 'self' data:;" in csp

def test_security_headers_on_error(client):
    """Verify that security headers are also added on error responses (e.g. 404)."""
    response = client.get('/nonexistent_endpoint')

    assert response.status_code == 404
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'DENY'
    assert response.headers.get('X-XSS-Protection') == '1; mode=block'

    csp = response.headers.get('Content-Security-Policy', '')
    assert "default-src 'self'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "script-src 'self' 'unsafe-inline'" in csp
    assert "img-src 'self' data:;" in csp
