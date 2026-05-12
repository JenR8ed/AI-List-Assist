"""Minimal smoke tests — verify the app boots and core imports resolve.

Designed to run without external services (eBay, Gemini, Redis, etc.).
Sets required env vars before importing app_enhanced to avoid missing-key errors.
"""
import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Set required env vars BEFORE importing the app so Flask/services initialise
# ---------------------------------------------------------------------------
os.environ.setdefault('SECRET_KEY', 'smoke-test-secret')
os.environ.setdefault('API_KEY', 'smoke-test-api-key')
os.environ.setdefault('EBAY_CLIENT_ID', 'smoke-test-client-id')
os.environ.setdefault('EBAY_CLIENT_SECRET', 'smoke-test-client-secret')
os.environ.setdefault('GEMINI_API_KEY', 'smoke-test-gemini-key')
os.environ.setdefault('PERPLEXITY_API_KEY', 'smoke-test-perplexity-key')

# Ensure the project root is on sys.path when running from /tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app_enhanced import app, init_db  # noqa: E402


@pytest.fixture(autouse=True)
def setup_teardown():
    """Initialise DB in app context; clean up temp db files after."""
    with app.app_context():
        init_db()
    yield
    for db_file in ('listings.db', 'valuations.db', 'consignment.db'):
        try:
            os.remove(db_file)
        except OSError:
            pass


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------

def test_app_exists():
    """Flask application object should be present."""
    assert app is not None


def test_app_is_testing(client):
    """TESTING config flag should be set in fixture."""
    assert app.config['TESTING'] is True


def test_health_endpoint(client):
    """GET /health returns 200 with status ok."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data.get('status') == 'ok'


def test_unauthorized_without_key(client):
    """API endpoints require an Authorization header — 401 without one."""
    response = client.get('/api/listings/drafts')
    assert response.status_code == 401


def test_unauthorized_with_bad_key(client):
    """Invalid API key returns 401."""
    response = client.get(
        '/api/listings/drafts',
        headers={'Authorization': 'Bearer bad-key-xyz'}
    )
    assert response.status_code == 401
