import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration

class TestEBayGetListings(unittest.TestCase):
    def setUp(self):
        os.environ['EBAY_CLIENT_ID'] = "test_app_id"
        os.environ['EBAY_CLIENT_SECRET'] = "test_cert_id"
        self.ebay = eBayIntegration(use_sandbox=True)
        self.ebay.token_manager.get_valid_token = MagicMock(return_value="valid_token")

    @patch('services.ebay_integration.requests.get')
    def test_get_active_listings_success(self, mock_get):
        # Mock successful eBay API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total": 2,
            "offers": [
                {
                    "offerId": "off1",
                    "listingId": "123456789",
                    "status": "PUBLISHED",
                    "sku": "SKU1",
                    "listing": {"title": "Test Listing 1"},
                    "pricingSummary": {"price": {"value": "249.99", "currency": "USD"}}
                },
                {
                    "offerId": "off2",
                    "listingId": "987654321",
                    "status": "PUBLISHED",
                    "sku": "SKU2",
                    "listing": {"title": "Test Listing 2"},
                    "pricingSummary": {"price": {"value": "899.99", "currency": "USD"}}
                },
                {
                    "offerId": "off3",
                    "listingId": "456",
                    "status": "DRAFT",
                    "sku": "SKU3"
                }
            ]
        }

        mock_inv_response = MagicMock()
        mock_inv_response.status_code = 200
        mock_inv_response.json.return_value = {"inventoryItems": []}

        mock_get.side_effect = [mock_response, mock_inv_response]

        listings = self.ebay.get_active_listings()

        self.assertEqual(len(listings), 2)
        self.assertEqual(listings[0]['ebay_listing_id'], "123456789")

    @patch('services.ebay_integration.requests.get')
    def test_get_active_listings_token_refresh(self, mock_get):
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "offers": [
                {
                    "listingId": "123",
                    "status": "PUBLISHED",
                    "listing": {"title": "Refreshed"},
                    "pricingSummary": {"price": {"value": "10.0", "currency": "USD"}}
                }
            ]
        }

        mock_inv_response = MagicMock()
        mock_inv_response.status_code = 200
        mock_inv_response.json.return_value = {"inventoryItems": []}

        mock_get.side_effect = [mock_response_401, mock_response_200, mock_inv_response]
        self.ebay.refresh_access_token = MagicMock(return_value=True)

        listings = self.ebay.get_active_listings()
        self.assertEqual(len(listings), 1)

if __name__ == '__main__':
    unittest.main()
