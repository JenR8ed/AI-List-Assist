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

        def mock_get_side_effect(url, headers=None, params=None):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            if "offer" in url:
                call_counts['offer'] += 1
                if call_counts['offer'] == 1:
                    mock_resp.json.return_value = {
                        "offers": [
                            {
                                "offerId": "off1",
                                "listingId": "L1",
                                "status": "PUBLISHED",
                                "sku": "SKU1",
                                "listing": {"title": "Title 1"},
                                "pricingSummary": {"price": {"value": "10.00", "currency": "USD"}}
                            }
                        ],
                        "next": "https://api.sandbox.ebay.com/sell/inventory/v1/offer?offset=1&limit=1"
                    }
                else:
                    mock_resp.json.return_value = {
                        "offers": [
                            {
                                "offerId": "off2",
                                "listingId": "L2",
                                "status": "PUBLISHED",
                                "sku": "SKU2",
                                "listing": {"title": "Title 2"},
                                "pricingSummary": {"price": {"value": "20.00", "currency": "USD"}}
                            }
                        ]
                        # No 'next' key here
                    }
            elif "inventory_item" in url:
                call_counts['inventory'] += 1
                if call_counts['inventory'] == 1:
                    mock_resp.json.return_value = {
                        "total": 200,
                        "inventoryItems": [
                            {
                                "sku": "SKU1",
                                "product": {
                                    "title": "Inv Title 1",
                                    "imageUrls": ["img1.jpg"]
                                }
                            }
                        ]
                    }
                else:
                    mock_resp.json.return_value = {
                        "total": 200,
                        "inventoryItems": [
                            {
                                "sku": "SKU2",
                                "product": {
                                    "title": "Inv Title 2",
                                    "imageUrls": ["img2.jpg"]
                                }
                            }
                        ]
                    }
            return mock_resp

        mock_get.side_effect = mock_get_side_effect

        listings = self.ebay.get_active_listings()

        self.assertEqual(len(listings), 2)
        self.assertEqual(listings[0]['sku'], "SKU1")
        self.assertEqual(listings[1]['sku'], "SKU2")
        self.assertEqual(listings[0]['image_filename'], "img1.jpg")
        self.assertEqual(listings[1]['image_filename'], "img2.jpg")

        self.assertEqual(mock_get.call_count, 4)

if __name__ == '__main__':
    unittest.main()
