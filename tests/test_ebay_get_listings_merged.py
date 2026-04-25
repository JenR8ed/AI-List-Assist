import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration

class TestEBayGetListingsMerged(unittest.TestCase):
    def setUp(self):
        os.environ['EBAY_CLIENT_ID'] = "test_app_id"
        os.environ['EBAY_CLIENT_SECRET'] = "test_cert_id"
        self.ebay = eBayIntegration(use_sandbox=True)
        self.ebay.token_manager.get_valid_token = MagicMock(return_value="valid_token")

    @patch('services.ebay_integration.requests.get')
    def test_get_active_listings_success(self, mock_get):
        mock_offer_resp = MagicMock()
        mock_offer_resp.status_code = 200
        mock_offer_resp.json.return_value = {
            "total": 1,
            "offers": [
                {
                    "offerId": "off1",
                    "listingId": "123456789",
                    "status": "PUBLISHED",
                    "sku": "SKU1",
                    "listing": {"title": "Test Listing 1"},
                    "pricingSummary": {"price": {"value": "249.99", "currency": "USD"}}
                }
            ]
        }

        mock_inventory_resp = MagicMock()
        mock_inventory_resp.status_code = 200
        mock_inventory_resp.json.return_value = {
            "inventoryItems": [
                {
                    "sku": "SKU1",
                    "product": {
                        "title": "Inv Title",
                        "imageUrls": ["http://example.com/img.jpg"]
                    }
                }
            ]
        }

        mock_get.side_effect = [mock_offer_resp, mock_inventory_resp]

        listings = self.ebay.get_active_listings()

        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].get('image_filename', ''), "http://example.com/img.jpg")

    @patch('services.ebay_integration.requests.get')
    def test_get_active_listings_token_refresh(self, mock_get):
        mock_401 = MagicMock()
        mock_401.status_code = 401

        mock_offer_resp = MagicMock()
        mock_offer_resp.status_code = 200
        mock_offer_resp.json.return_value = {
            "offers": [
                {
                    "listingId": "123",
                    "status": "PUBLISHED",
                    "sku": "SKU_REFRESHED",
                    "listing": {"title": "Refreshed"},
                    "pricingSummary": {"price": {"value": "10.0", "currency": "USD"}}
                }
            ]
        }

        mock_inv_response = MagicMock()
        mock_inv_response.status_code = 200
        mock_inv_response.json.return_value = {"inventoryItems": []}

        mock_get.side_effect = [mock_401, mock_offer_resp, mock_inv_response]
        self.ebay.refresh_access_token = MagicMock(return_value=True)

        listings = self.ebay.get_active_listings()
        self.assertEqual(len(listings), 1)

if __name__ == '__main__':
    unittest.main()
