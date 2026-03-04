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
        # 1. Mock Offer Responses (2 pages)
        mock_offer_resp_p1 = MagicMock()
        mock_offer_resp_p1.status_code = 200
        mock_offer_resp_p1.json.return_value = {
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

        mock_offer_resp_p2 = MagicMock()
        mock_offer_resp_p2.status_code = 200
        mock_offer_resp_p2.json.return_value = {
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

        # 2. Mock Inventory Responses (2 pages)
        mock_inventory_resp_p1 = MagicMock()
        mock_inventory_resp_p1.status_code = 200
        mock_inventory_resp_p1.json.return_value = {
            "inventoryItems": [
                {
                    "sku": "SKU1",
                    "product": {
                        "title": "Inv Title 1",
                        "imageUrls": ["img1.jpg"]
                    }
                }
            ],
            "next": "https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item?offset=1&limit=1"
        }

        mock_inventory_resp_p2 = MagicMock()
        mock_inventory_resp_p2.status_code = 200
        mock_inventory_resp_p2.json.return_value = {
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

        mock_get.side_effect = [
            mock_offer_resp_p1, mock_offer_resp_p2,
            mock_inventory_resp_p1, mock_inventory_resp_p2
        ]

        listings = self.ebay.get_active_listings()

        self.assertEqual(len(listings), 2)
        self.assertEqual(listings[0]['sku'], "SKU1")
        self.assertEqual(listings[1]['sku'], "SKU2")
        self.assertEqual(listings[0]['image_filename'], "img1.jpg")
        self.assertEqual(listings[1]['image_filename'], "img2.jpg")

        self.assertEqual(mock_get.call_count, 4)

if __name__ == '__main__':
    unittest.main()
