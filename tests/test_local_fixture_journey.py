"""The same fixture intake and review through JSON and browser form routes."""

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

import app_enhanced


BASE = 'http://127.0.0.1:5000'


@pytest.fixture
def local_client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(app_enhanced.app.config, 'LOCAL_DRAFT_MODE', True)
    monkeypatch.setitem(app_enhanced.app.config, 'TESTING', True)
    monkeypatch.delenv('API_KEY', raising=False)
    forbidden = Mock(side_effect=AssertionError('provider invoked'))
    monkeypatch.setattr(app_enhanced, 'vision_service', forbidden)
    monkeypatch.setattr(app_enhanced, 'valuation_service', Mock(evaluate_item=forbidden))
    monkeypatch.setattr(app_enhanced, 'listing_engine', Mock(create_listing_draft=forbidden))
    monkeypatch.setattr(app_enhanced, 'ebay_integration', Mock(create_listing=forbidden))
    app_enhanced.init_db()
    with app_enhanced.app.test_client() as client:
        page = client.get('/local', base_url=BASE)
        assert page.status_code == 200
        token = re.search(rb'name="csrf_token" value="([^"]+)"', page.data).group(1).decode()
        yield client, token, forbidden
    forbidden.assert_not_called()


def test_api_intake_item_edit_review_never_publishes(local_client):
    client, token, _ = local_client
    headers = {'X-CSRF-Token': token}
    response = client.post('/api/local/intake', json={'fixture_id': 'camera'}, headers=headers, base_url=BASE)
    assert response.status_code == 201
    item = response.json['item']
    assert item['source'] == 'fixture'
    assert item['valuation']['status'] == 'unavailable'
    assert client.get(f"/api/local/items/{item['item_id']}", base_url=BASE).json['item'] == item
    response = client.post('/api/local/drafts', json={'item_id': item['item_id']}, headers=headers, base_url=BASE)
    assert response.status_code == 201
    draft = response.json['listing']
    listing_id = draft['listing_id']
    assert draft['source'] == 'fixture' and draft['price'] is None
    assert client.get(f'/api/local/drafts/{listing_id}', base_url=BASE).json['status'] == 'draft'
    assert client.post(f'/api/listing/{listing_id}/approve', headers=headers, base_url=BASE).status_code == 422
    response = client.put(f'/api/listing/{listing_id}', json={'description': 'Checked by human', 'price': 42},
                          headers=headers, base_url=BASE)
    assert response.status_code == 200
    assert client.get(f'/api/listing/{listing_id}/validate', base_url=BASE).json['valid'] is True
    assert client.post(f'/api/listing/{listing_id}/approve', headers=headers, base_url=BASE).json['status'] == 'approved'
    with sqlite3.connect('listings.db') as conn:
        row = conn.execute('SELECT status, draft_data, ebay_listing_id FROM listings WHERE listing_id = ?',
                           (listing_id,)).fetchone()
    assert row[0] == 'approved' and json.loads(row[1])['price'] == 42 and row[2] is None
    response = client.post('/api/listing/publish', json={'listing_id': listing_id}, headers=headers, base_url=BASE)
    assert response.status_code == 503 and response.json['code'] == 'FEATURE_DISABLED'
    assert client.post('/api/ebay/submit-listing', base_url=BASE).status_code == 503


def test_browser_forms_complete_same_journey_and_revoke_approval(local_client):
    client, token, _ = local_client
    assert b'Open local fixture draft review' in client.get('/', base_url=BASE).data
    response = client.post('/local/intake', data={'fixture_id': 'camera', 'csrf_token': token}, base_url=BASE)
    assert response.status_code == 303
    item_page = client.get(response.headers['Location'], base_url=BASE)
    assert b'Structured item record' in item_page.data and b'Source</dt><dd>fixture' in item_page.data
    item_id = response.headers['Location'].split('/')[-1]
    response = client.post(f'/local/items/{item_id}/drafts', data={'csrf_token': token}, base_url=BASE)
    assert response.status_code == 303
    draft_url = response.headers['Location']
    listing_id = draft_url.split('/')[-1]
    page = client.get(draft_url, base_url=BASE)
    assert b'Draft status: <strong>draft</strong>' in page.data
    assert b'description is required' in page.data and b'price must be a positive number' in page.data
    assert b'Approve reviewed draft' not in page.data
    response = client.post(f'/local/drafts/{listing_id}/edit', data={
        'csrf_token': token, 'title': 'Reviewed example camera', 'description': 'Inspected local fixture',
        'category_id': '293', 'condition': 'Used', 'price': '50.00'
    }, base_url=BASE)
    assert response.status_code == 303
    assert b'Approve reviewed draft' in client.get(draft_url, base_url=BASE).data
    assert client.post(f'/local/drafts/{listing_id}/approve', data={'csrf_token': token}, base_url=BASE).status_code == 303
    assert b'Draft status: <strong>approved</strong>' in client.get(draft_url, base_url=BASE).data
    client.post(f'/local/drafts/{listing_id}/edit', data={
        'csrf_token': token, 'title': 'Changed after review', 'description': 'Inspected local fixture',
        'category_id': '293', 'condition': 'Used', 'price': '50.00'
    }, base_url=BASE)
    assert client.get(f'/api/local/drafts/{listing_id}', base_url=BASE).json['status'] == 'draft'
    assert client.post('/local/intake', data={'fixture_id': 'camera'}, base_url=BASE).status_code == 403
    assert app_enhanced.app.test_client().get(draft_url, base_url=BASE).status_code == 403


def test_fresh_checkout_runs_fixture_forms_without_keys_or_network(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = '''
import re
from unittest.mock import patch
with patch('socket.socket.connect', side_effect=AssertionError('network request')):
    from app_enhanced import app, init_db
    init_db()
    with app.test_client() as client:
        page = client.get('/local', base_url='http://127.0.0.1:5000')
        assert page.status_code == 200 and b'Fixture data only' in page.data
        token = re.search(rb'name="csrf_token" value="([^"]+)"', page.data).group(1).decode()
        headers = {'X-CSRF-Token': token}
        item = client.post('/api/local/intake', json={'fixture_id': 'camera'}, headers=headers,
                           base_url='http://127.0.0.1:5000').json['item']
        draft = client.post('/api/local/drafts', json={'item_id': item['item_id']}, headers=headers,
                            base_url='http://127.0.0.1:5000').json['listing']
        listing_id = draft['listing_id']
        client.put('/api/listing/' + listing_id, json={'description': 'Reviewed', 'price': 10},
                   headers=headers, base_url='http://127.0.0.1:5000')
        assert client.post('/api/listing/' + listing_id + '/approve', headers=headers,
                           base_url='http://127.0.0.1:5000').json['status'] == 'approved'
        assert client.post('/api/listing/publish', json={'listing_id': listing_id}, headers=headers,
                           base_url='http://127.0.0.1:5000').status_code == 503
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=tmp_path,
                            env={'LOCAL_DRAFT_MODE': '1', 'PYTHONPATH': str(root), 'PYTHONDONTWRITEBYTECODE': '1'},
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
