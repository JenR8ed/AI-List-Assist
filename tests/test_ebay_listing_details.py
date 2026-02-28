import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import time

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration

class TestEBayGetListingDetails(unittest.TestCase):
    def setUp(self):
        self.app_id = "test_app_id"
        self.cert_id = "test_cert_id"
        self.ebay = eBayIntegration(app_id=self.app_id, cert_id=self.cert_id, use_sandbox=True)
        self.ebay.access_token = "valid_token"
        # Reset cache for each test
        self.ebay.listing_cache = {}

    @patch('requests.get')
    @patch('services.ebay_token_manager.EBayTokenManager.get_valid_token')
    def test_get_inventory_item(self, mock_token, mock_get):
        mock_token.return_value = "valid_token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"sku": "SKU1", "product": {"title": "Test Title"}}
        mock_get.return_value = mock_response

        result = self.ebay.get_inventory_item("SKU1")
        self.assertEqual(result["sku"], "SKU1")
        self.assertEqual(result["product"]["title"], "Test Title")

    @patch('requests.get')
    @patch('services.ebay_token_manager.EBayTokenManager.get_valid_token')
    def test_get_offers_by_sku(self, mock_token, mock_get):
        mock_token.return_value = "valid_token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"offers": [{"offerId": "OFF1", "sku": "SKU1"}]}
        mock_get.return_value = mock_response

        result = self.ebay.get_offers_by_sku("SKU1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["offerId"], "OFF1")

    @patch('services.ebay_integration.eBayIntegration.get_inventory_item')
    @patch('services.ebay_integration.eBayIntegration.get_offers_by_sku')
    @patch('services.ebay_token_manager.EBayTokenManager.get_valid_token')
    def test_get_listing_details_success(self, mock_token, mock_get_offers, mock_get_inventory):
        mock_token.return_value = "valid_token"
        mock_get_inventory.return_value = {
            "sku": "SKU1",
            "product": {
                "title": "Full Title",
                "description": "Full Description",
                "aspects": {"Brand": ["Sony"]},
                "imageUrls": ["http://image1.jpg"]
            },
            "condition": "USED_EXCELLENT",
            "availability": {"shipToLocationAvailability": {"quantity": 5}}
        }
        mock_get_offers.return_value = [
            {
                "offerId": "OFF1",
                "listingId": "EBAY123",
                "status": "PUBLISHED",
                "categoryId": "293",
                "pricingSummary": {"price": {"value": "150.0", "currency": "USD"}},
                "listingPolicies": {"fulfillmentPolicyId": "fp1"}
            }
        ]

        details = self.ebay.get_listing_details("SKU1")

        self.assertEqual(details["title"], "Full Title")
        self.assertEqual(details["price"], 150.0)
        self.assertEqual(details["listing_id"], "EBAY123")
        self.assertEqual(details["quantity"], 5)
        self.assertEqual(details["status"], "PUBLISHED")

        # Verify caching
        self.assertIn("SKU1", self.ebay.listing_cache)

        # Second call should use cache
        with patch('services.ebay_integration.eBayIntegration.get_inventory_item') as mock_inv_2:
            details_2 = self.ebay.get_listing_details("SKU1")
            self.assertEqual(details_2["title"], "Full Title")
            mock_inv_2.assert_not_called()

    @patch('services.ebay_integration.eBayIntegration.get_inventory_item')
    @patch('services.ebay_integration.eBayIntegration.get_offers_by_sku')
    @patch('services.ebay_token_manager.EBayTokenManager.get_valid_token')
    def test_get_listing_details_force_refresh(self, mock_token, mock_get_offers, mock_get_inventory):
        mock_token.return_value = "valid_token"
        self.ebay.listing_cache["SKU1"] = ({"title": "Old"}, time.time() + 100)

        mock_get_inventory.return_value = {"product": {"title": "New"}}
        mock_get_offers.return_value = []

        details = self.ebay.get_listing_details("SKU1", force_refresh=True)
        self.assertEqual(details["title"], "New")

if __name__ == '__main__':
    unittest.main()
