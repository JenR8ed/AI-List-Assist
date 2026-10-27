import pytest
import os
import json
from unittest.mock import patch

# Setup environment before importing app
os.environ.setdefault('SECRET_KEY', 'test_secret')
os.environ.setdefault('API_KEY', 'test_api_key')
os.environ.setdefault('EBAY_CLIENT_ID', 'test')
os.environ.setdefault('EBAY_CLIENT_SECRET', 'test')
os.environ.setdefault('GEMINI_API_KEY', 'test_gemini')
os.environ.setdefault('PERPLEXITY_API_KEY', 'test_perplexity')

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
        os.remove('consignment.db')
    except OSError:
        pass

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_stats_success(client):
    """Test get_stats endpoint returns success and data."""
    api_key = os.environ.get('API_KEY', 'test_api_key')
    headers = {'Authorization': f'Bearer {api_key}'}

    mock_stats = {
        "total_valuations": 5,
        "worth_listing": 3,
        "avg_confidence": 0.85
    }

    with patch('app_enhanced.ValuationDatabase.get_valuation_stats', return_value=mock_stats):
        response = client.get('/api/stats', headers=headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == mock_stats

def test_get_stats_error(client):
    """Test get_stats endpoint handles errors appropriately."""
    api_key = os.environ.get('API_KEY', 'test_api_key')
    headers = {'Authorization': f'Bearer {api_key}'}

    with patch('app_enhanced.ValuationDatabase.get_valuation_stats', side_effect=Exception("Database error")):
        response = client.get('/api/stats', headers=headers)

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data.get('error') == "Database error"

def test_get_stats_unauthorized(client):
    """Test get_stats endpoint requires authorization."""
    response = client.get('/api/stats')
    assert response.status_code == 401
