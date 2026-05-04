import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration

class TestEBayGetListingsPagination(unittest.TestCase):
    def setUp(self):
        self.app_id = "test_app_id"
        self.cert_id = "test_cert_id"
        os.environ['EBAY_CLIENT_ID'] = self.app_id
        os.environ['EBAY_CLIENT_SECRET'] = self.cert_id
        self.ebay = eBayIntegration(use_sandbox=True)
        self.ebay.access_token = "valid_token"

    @patch('requests.get')
    def test_get_active_listings_pagination_success(self, mock_get):
        call_counts = {'offer': 0, 'inventory': 0}

        def mock_get_effect(url, *args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200

            if 'offer' in url:
                call_counts['offer'] += 1
                if call_counts['offer'] == 1:
                    mock_response.json.return_value = {
                        "total": 3,
                        "next": "https://api.sandbox.ebay.com/sell/inventory/v1/offer?offset=2&limit=2",
                        "offers": [
                            {"listingId": "1", "status": "PUBLISHED", "sku": "SKU1", "listing": {"title": "L1"}, "pricingSummary": {"price": {"value": "10.0", "currency": "USD"}}},
                            {"listingId": "2", "status": "PUBLISHED", "sku": "SKU2", "listing": {"title": "L2"}, "pricingSummary": {"price": {"value": "20.0", "currency": "USD"}}}
                        ]
                    }
                else:
                    mock_response.json.return_value = {
                        "total": 3,
                        "next": None,
                        "offers": [
                            {"listingId": "3", "status": "PUBLISHED", "sku": "SKU3", "listing": {"title": "L3"}, "pricingSummary": {"price": {"value": "30.0", "currency": "USD"}}}
                        ]
                    }
            elif 'inventory' in url:
                call_counts['inventory'] += 1
                if call_counts['inventory'] == 1:
                    mock_response.json.return_value = {
                        "total": 3,
                        "next": "https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item?offset=2&limit=2",
                        "inventoryItems": [
                            {"sku": "SKU1", "product": {"title": "L1", "imageUrls": ["img1.jpg"]}},
                            {"sku": "SKU2", "product": {"title": "L2", "imageUrls": ["img2.jpg"]}}
                        ]
                    }
                else:
                    mock_response.json.return_value = {
                        "total": 3,
                        "next": None,
                        "inventoryItems": [
                            {"sku": "SKU3", "product": {"title": "L3", "imageUrls": ["img3.jpg"]}}
                        ]
                    }
            return mock_response

        mock_get.side_effect = mock_get_effect

        listings = self.ebay.get_active_listings()

        self.assertEqual(len(listings), 3)
        self.assertEqual(listings[0]['ebay_listing_id'], "1")
        self.assertEqual(listings[1]['ebay_listing_id'], "2")
        self.assertEqual(listings[2]['ebay_listing_id'], "3")

        self.assertEqual(listings[0]['image_filename'], "img1.jpg")
        self.assertEqual(listings[1]['image_filename'], "img2.jpg")
        self.assertEqual(listings[2]['image_filename'], "img3.jpg")


if __name__ == '__main__':
    unittest.main()
