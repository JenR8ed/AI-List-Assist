"""Local browser session and server-to-server authentication boundary."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

os.environ.setdefault('SECRET_KEY', 'local-auth-test-secret')

from app_enhanced import app  # noqa: E402


@pytest.fixture
def local_client(monkeypatch):
    monkeypatch.setitem(app.config, 'LOCAL_DRAFT_MODE', True)
    monkeypatch.delenv('API_KEY', raising=False)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def _csrf_from(response):
    match = re.search(rb'<meta name="csrf-token" content="([^"]+)">', response.data)
    assert match
    return match.group(1).decode()


@pytest.mark.parametrize('page', ['/', '/simple'])
def test_local_page_grants_session_without_browser_api_key(local_client, page):
    response = local_client.get(page, base_url='http://127.0.0.1:5000')
    assert response.status_code == 200
    assert b'/static/js/api_client.js' in response.data
    assert b'API_KEY' not in response.data

    token = _csrf_from(response)
    denied = local_client.post('/api/analyze', base_url='http://127.0.0.1:5000')
    assert denied.status_code == 403
    accepted = local_client.post('/api/analyze', headers={'X-CSRF-Token': token}, base_url='http://127.0.0.1:5000')
    assert accepted.status_code == 400  # Handler reached; no image or external service call.


def test_nonlocal_browser_cannot_grant_or_reuse_session(local_client):
    assert local_client.get('/', environ_overrides={'REMOTE_ADDR': '203.0.113.10'}).status_code == 403
    _csrf_from(local_client.get('/', base_url='http://127.0.0.1:5000'))
    remote = local_client.post('/api/analyze', environ_overrides={'REMOTE_ADDR': '203.0.113.10'})
    assert remote.status_code == 401
    assert local_client.get('/', base_url='http://example.test').status_code == 403


def test_server_key_remains_separate_from_local_ui_session(local_client, monkeypatch):
    monkeypatch.setenv('API_KEY', 'sentinel-for-test-only')
    response = app.test_client().post('/api/analyze', headers={'Authorization': 'Bearer sentinel-for-test-only'})
    assert response.status_code == 400
    assert app.test_client().post('/api/analyze').status_code == 401


@pytest.mark.parametrize('path', ['/api/ebay/submit-listing', '/api/ebay/token/refresh'])
def test_marketplace_routes_disabled_in_local_mode(local_client, path):
    response = local_client.post(path)
    assert response.status_code == 503
    assert response.json['error'] == 'Marketplace integration disabled in local draft mode'


def test_publish_requires_session_then_rejects_missing_id(local_client):
    assert local_client.post('/api/listing/publish').status_code == 401
    token = _csrf_from(local_client.get('/', base_url='http://127.0.0.1:5000'))
    response = local_client.post('/api/listing/publish', json={}, headers={'X-CSRF-Token': token},
                                 base_url='http://127.0.0.1:5000')
    assert response.status_code == 400


def test_fresh_checkout_import_needs_no_credentials_or_network(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = """
from unittest.mock import patch
with patch('socket.socket.connect', side_effect=AssertionError('network request')):
    from app_enhanced import app
    client = app.test_client()
    response = client.get('/', base_url='http://127.0.0.1:5000')
    assert response.status_code == 200
    assert app.config['SECRET_KEY']
"""
    result = subprocess.run(
        [sys.executable, '-c', script],
        cwd=tmp_path,
        env={'LOCAL_DRAFT_MODE': '1', 'PYTHONPATH': str(root), 'PYTHONDONTWRITEBYTECODE': '1'},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
