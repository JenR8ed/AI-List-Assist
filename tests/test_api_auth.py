import pytest
import os
import io
import json

# Setup environment before importing app
os.environ['SECRET_KEY'] = 'test_secret'
os.environ['API_KEY'] = 'test_api_key_123'
os.environ['EBAY_CLIENT_ID'] = 'test'
os.environ['EBAY_CLIENT_SECRET'] = 'test'

from app_enhanced import app, init_db

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    with app.app_context():
        init_db()
    yield
    # Teardown (cleanup db files if needed)
    try:
        os.remove('listings.db')
        os.remove('valuations.db')
    except OSError:
        pass

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_unauthorized_without_key(client):
    """Test that API endpoints return 401 when API_KEY is missing."""
    # Test a simple GET endpoint
    response = client.get('/api/listings/drafts')
    assert response.status_code == 401
    assert json.loads(response.data).get('error') == 'Unauthorized'

def test_api_unauthorized_with_invalid_key(client):
    """Test that API endpoints return 401 when API_KEY is invalid."""
    headers = {'Authorization': 'Bearer wrong_key'}
    response = client.get('/api/listings/drafts', headers=headers)
    assert response.status_code == 401
    assert json.loads(response.data).get('error') == 'Unauthorized'

def test_api_authorized_with_valid_key(client):
    """Test that API endpoints return 200 when API_KEY is valid."""
    headers = {'Authorization': 'Bearer test_api_key_123'}
    response = client.get('/api/listings/drafts', headers=headers)

    assert response.status_code == 200

def test_api_authorized_without_bearer_prefix(client):
    """Test that API works even without 'Bearer ' prefix."""
    headers = {'Authorization': 'test_api_key_123'}
    response = client.get('/api/listings/drafts', headers=headers)

    assert response.status_code != 401

def test_public_routes_unaffected(client):
    """Test that non-API routes don't require authentication."""
    response = client.get('/')
    assert response.status_code == 200

def test_api_analyze_unauthorized(client):
    """Test POST to /api/analyze without auth."""
    data = {'image': (io.BytesIO(b"fake image data"), 'test.jpg')}
    response = client.post('/api/analyze', data=data, content_type='multipart/form-data')
    assert response.status_code == 401

def test_missing_api_key_env_var(client, monkeypatch):
    """Test when API_KEY is not set in environment."""
    monkeypatch.delenv('API_KEY', raising=False)

    response = client.get('/api/listings/drafts')
    assert response.status_code == 500
    assert "Server misconfiguration" in json.loads(response.data).get('error')
