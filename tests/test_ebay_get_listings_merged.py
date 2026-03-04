import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration

class TestEBayGetListingsMerged(unittest.TestCase):
    def setUp(self):
        self.app_id = "test_app_id"
        self.cert_id = "test_cert_id"
        os.environ['EBAY_CLIENT_ID'] = self.app_id
        os.environ['EBAY_CLIENT_SECRET'] = self.cert_id
        self.ebay = eBayIntegration(use_sandbox=True)
        self.ebay.access_token = "valid_token"

    @patch('services.ebay_token_manager.EBayTokenManager.get_valid_token')
    @patch('requests.get')
    def test_get_active_listings_success(self, mock_get, mock_token):
        mock_token.return_value = "valid_token"
        # 1. Mock Offer Response
        mock_offer_resp = MagicMock()
        mock_offer_resp.status_code = 200
        mock_offer_resp.json.return_value = {
            "offers": [
                {
                    "offerId": "off1",
                    "listingId": "123456789",
                    "status": "PUBLISHED",
                    "sku": "SKU1",
                    "listing": {"title": "Offer Title"},
                    "pricingSummary": {"price": {"value": "249.99", "currency": "USD"}}
                }
            ]
        }

        # 2. Mock Inventory Response
        mock_inventory_resp = MagicMock()
        mock_inventory_resp.status_code = 200
        mock_inventory_resp.json.return_value = {
            "inventoryItems": [
                {
                    "sku": "SKU1",
                    "product": {
                        "title": "Inventory Title",
                        "imageUrls": ["http://example.com/image.jpg"]
                    }
                }
            ]
        }

        mock_get.side_effect = [mock_offer_resp, mock_inventory_resp]

        listings = self.ebay.get_active_listings()

        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0]['ebay_listing_id'], "123456789")
        self.assertEqual(listings[0]['listing_title'], "Offer Title")
        self.assertEqual(listings[0]['image_filename'], "http://example.com/image.jpg")
        self.assertEqual(listings[0]['price'], 249.99)

        self.assertEqual(mock_get.call_count, 2)

    @patch('services.ebay_token_manager.EBayTokenManager.get_valid_token')
    @patch('requests.get')
    @patch('services.ebay_integration.eBayIntegration.refresh_access_token')
    def test_get_active_listings_token_refresh(self, mock_refresh, mock_get, mock_token):
        mock_token.return_value = "valid_token"
        # 401 for offer, then 200 for offer, then 200 for inventory
        mock_resp_401 = MagicMock()
        mock_resp_401.status_code = 401

        mock_offer_resp = MagicMock()
        mock_offer_resp.status_code = 200
        mock_offer_resp.json.return_value = {"offers": [{"sku": "S1", "status": "PUBLISHED", "listingId": "L1"}]}

        mock_inv_resp = MagicMock()
        mock_inv_resp.status_code = 200
        mock_inv_resp.json.return_value = {"inventoryItems": []}

        mock_get.side_effect = [mock_resp_401, mock_offer_resp, mock_inv_resp]
        mock_refresh.return_value = True

        listings = self.ebay.get_active_listings()

        self.assertEqual(len(listings), 1)
        self.assertEqual(mock_refresh.call_count, 1)
        self.assertEqual(mock_get.call_count, 3)

if __name__ == '__main__':
    unittest.main()
