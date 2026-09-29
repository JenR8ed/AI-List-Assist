"""Fixture provenance survives category, valuation, and draft API boundaries."""

import re
from unittest.mock import patch

import pytest

import app_enhanced
from services.ebay_category_service import EBayCategoryService
from services.mock_valuation_service import MockValuationService
from services.valuation_service import ValuationService


@pytest.fixture
def browser(monkeypatch):
    monkeypatch.setitem(app_enhanced.app.config, 'LOCAL_DRAFT_MODE', True)
    monkeypatch.setitem(app_enhanced.app.config, 'TESTING', True)
    monkeypatch.delenv('API_KEY', raising=False)
    with app_enhanced.app.test_client() as client:
        page = client.get('/', base_url='http://127.0.0.1:5000')
        token = re.search(rb'<meta name="csrf-token" content="([^"]+)">', page.data).group(1).decode()
        yield client, {'X-CSRF-Token': token}, page


def test_category_fallback_is_labeled_and_visible(browser, monkeypatch):
    client, headers, page = browser
    with patch('services.ebay_category_service.EBayTokenManager') as manager:
        manager.return_value.get_valid_token.return_value = None
        monkeypatch.setattr(app_enhanced, 'category_service', EBayCategoryService())
    response = client.get('/api/category/293/aspects', base_url='http://127.0.0.1:5000')
    assert response.status_code == 200
    assert response.json['source'] == response.json['aspects']['source'] == 'fixture'
    response = client.post('/api/category/suggest', json={'item_name': 'Camera'}, headers=headers,
                           base_url='http://127.0.0.1:5000')
    assert response.json['source'] == response.json['suggestions'][0]['source'] == 'simulated'
    assert b'Source:' in page.data


def test_mock_valuation_provenance():
    valuation = MockValuationService().evaluate_item('fixture-image', 'image/jpeg', {'brand': 'Sony'})
    assert valuation.to_dict()['source'] == 'fixture'
    assert valuation.to_dict()['status'] == 'available'


def test_local_mode_never_requests_marketplace_metadata(monkeypatch):
    monkeypatch.setenv('LOCAL_DRAFT_MODE', '1')
    with patch('services.ebay_token_manager.EBayTokenManager') as manager:
        category = EBayCategoryService()
        valuation_service = ValuationService()
        manager.return_value.get_valid_token.assert_not_called()
    with patch('requests.get', side_effect=AssertionError('external request')) as fetch:
        assert category.get_category_aspects('293')['source'] == 'fixture'
        assert valuation_service.evaluate_item('', 'image/jpeg', {'item_name': 'Camera'}).status == 'unavailable'
        fetch.assert_not_called()
