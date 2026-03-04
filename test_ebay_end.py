import sys
from unittest.mock import MagicMock, patch

# mock dependencies
sys.modules['httpx'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.vision'] = MagicMock()

import pytest
from services.ebay_integration import eBayIntegration
import requests

def test_end_listing_success():
    integration = eBayIntegration(app_id="test", cert_id="test")
    integration.access_token = "test_token"

    with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
        # Mock get offers response
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            "offers": [
                {"offerId": "offer_1", "status": "UNPUBLISHED"},
                {"offerId": "offer_2", "status": "PUBLISHED"}
            ]
        }
        mock_get.return_value = mock_get_resp

        # Mock withdraw offer response
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {"listingId": "1234567890"}
        mock_post.return_value = mock_post_resp

        response = integration.end_listing("TEST_SKU")

        assert response.get("listingId") == "1234567890"
        mock_get.assert_called_once()
        mock_post.assert_called_once_with(
            "https://api.sandbox.ebay.com/sell/inventory/v1/offer/offer_2/withdraw",
            headers=integration._get_headers()
        )

def test_end_listing_no_published_offer():
    integration = eBayIntegration(app_id="test", cert_id="test")
    integration.access_token = "test_token"

    with patch('requests.get') as mock_get:
        # Mock get offers response
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            "offers": [
                {"offerId": "offer_1", "status": "UNPUBLISHED"}
            ]
        }
        mock_get.return_value = mock_get_resp

        with pytest.raises(RuntimeError) as excinfo:
            integration.end_listing("TEST_SKU")

        assert "No published offer found for SKU TEST_SKU" in str(excinfo.value)
