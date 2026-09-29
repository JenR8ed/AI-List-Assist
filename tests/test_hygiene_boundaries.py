"""Uploaded images and token status never bypass the auth boundary."""

from pathlib import Path
from unittest.mock import patch

import pytest

from app_enhanced import app


@pytest.fixture
def uploaded_image(tmp_path, monkeypatch):
    (tmp_path / 'fixture.jpg').write_bytes(b'fixture-image')
    monkeypatch.setitem(app.config, 'UPLOAD_FOLDER', str(tmp_path))
    monkeypatch.setitem(app.config, 'TESTING', True)
    return '/uploads/fixture.jpg'


def test_local_browser_session_guards_uploaded_image(uploaded_image, monkeypatch):
    monkeypatch.setitem(app.config, 'LOCAL_DRAFT_MODE', True)
    monkeypatch.delenv('API_KEY', raising=False)
    with app.test_client() as client:
        assert client.get(uploaded_image, base_url='http://127.0.0.1:5000').status_code == 401
        assert client.get('/', base_url='http://127.0.0.1:5000').status_code == 200
        response = client.get(uploaded_image, base_url='http://127.0.0.1:5000')
        assert response.status_code == 200
        assert response.data == b'fixture-image'
        assert client.get(uploaded_image, environ_overrides={'REMOTE_ADDR': '203.0.113.10'}).status_code == 401


def test_server_key_guards_uploaded_image(uploaded_image, monkeypatch):
    monkeypatch.setitem(app.config, 'LOCAL_DRAFT_MODE', False)
    monkeypatch.setenv('API_KEY', 'sentinel-server-key')
    with app.test_client() as client:
        assert client.get(uploaded_image).status_code == 401
        response = client.get(uploaded_image, headers={'Authorization': 'Bearer sentinel-server-key'})
        assert response.status_code == 200
        assert response.data == b'fixture-image'


def test_token_status_returns_boolean_without_token_material(monkeypatch):
    monkeypatch.setitem(app.config, 'LOCAL_DRAFT_MODE', False)
    monkeypatch.setenv('API_KEY', 'sentinel-server-key')
    from services.ebay_token_manager import EBayTokenManager
    with patch.object(EBayTokenManager, '_load_token', return_value={
        'access_token': 'sentinel-never-expose-this', 'expires_at': '2999-01-01T00:00:00'
    }), patch.object(EBayTokenManager, 'get_valid_token', side_effect=AssertionError('refresh attempted')):
        with app.test_client() as client:
            response = client.get('/api/ebay/token/status',
                                  headers={'Authorization': 'Bearer sentinel-server-key'})
    assert response.status_code == 200
    assert response.json == {'success': True, 'has_token': True}
    assert b'sentinel-never-expose-this' not in response.data


def test_dockerfile_creates_user_before_switch_and_copies_application():
    dockerfile = (Path(__file__).resolve().parents[1] / 'Dockerfile').read_text()
    assert dockerfile.count('USER appuser') == 1
    assert dockerfile.index('useradd -u 1000') < dockerfile.index('USER appuser')
    assert dockerfile.index('mkdir -p /app/data /app/uploads') < dockerfile.index('USER appuser')
    assert 'COPY --chown=appuser:appuser app_enhanced.py ./' in dockerfile
