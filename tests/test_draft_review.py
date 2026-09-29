"""Persisted approval and both fail-closed publishing routes, without network."""

import json
import re
import sqlite3
from unittest.mock import Mock

import pytest

import app_enhanced


@pytest.fixture
def review_client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(app_enhanced.app.config, 'LOCAL_DRAFT_MODE', True)
    monkeypatch.setitem(app_enhanced.app.config, 'TESTING', True)
    monkeypatch.delenv('API_KEY', raising=False)
    blocked = Mock(side_effect=AssertionError('Marketplace call attempted'))
    monkeypatch.setattr(app_enhanced, 'ebay_integration', Mock(create_listing=blocked))
    app_enhanced.init_db()
    with sqlite3.connect('listings.db') as conn:
        conn.execute('INSERT INTO listings (listing_id, item_id, title, price, status, draft_data) '
                     'VALUES (?, ?, ?, ?, ?, ?)',
                     ('fixture-1', 'item-1', 'Camera', 45, 'draft', json.dumps({
                         'title': 'Camera', 'description': 'Working camera', 'category_id': '123',
                         'condition': 'Used', 'price': 45, 'missing_required_specifics': []
                     })))
    with app_enhanced.app.test_client() as client:
        page = client.get('/', base_url='http://127.0.0.1:5000')
        assert page.status_code == 200
        token = re.search(rb'<meta name="csrf-token" content="([^"]+)">', page.data).group(1).decode()
        yield client, {'X-CSRF-Token': token}, blocked


def test_draft_validation_approval_edit_revokes_approval(review_client):
    client, headers, blocked = review_client
    url = '/api/listing/fixture-1'
    base = 'http://127.0.0.1:5000'
    assert client.get(url + '/validate', base_url=base).json['valid'] is True
    assert client.post('/api/listing/publish', json={'listing_id': 'fixture-1'},
                       headers=headers, base_url=base).status_code == 409
    response = client.post(url + '/approve', headers=headers, base_url=base)
    assert response.status_code == 200
    assert response.json['status'] == 'approved'
    response = client.post('/api/listing/publish', json={'listing_id': 'fixture-1'},
                           headers=headers, base_url=base)
    assert response.status_code == 503
    assert response.json['code'] == 'FEATURE_DISABLED'
    response = client.put(url, json={'price': 0}, headers=headers, base_url=base)
    assert response.json['status'] == 'draft'
    assert client.get(url + '/validate', base_url=base).json['errors'] == ['price must be a positive number']
    assert client.post(url + '/approve', headers=headers, base_url=base).status_code == 422
    assert client.post('/api/listing/publish', json={'listing_id': 'fixture-1'},
                       headers=headers, base_url=base).status_code == 409
    blocked.assert_not_called()


def test_legacy_submit_disabled_even_with_server_key(review_client, monkeypatch):
    client, _, blocked = review_client
    monkeypatch.setitem(app_enhanced.app.config, 'LOCAL_DRAFT_MODE', False)
    monkeypatch.setenv('API_KEY', 'test-server-key')
    response = client.post('/api/ebay/submit-listing', json={'valuation_id': 'fixture-1'},
                           headers={'Authorization': 'Bearer test-server-key'})
    assert response.status_code == 503
    assert response.json['code'] == 'FEATURE_DISABLED'
    blocked.assert_not_called()
