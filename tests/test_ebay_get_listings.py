import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration

class TestEBayGetListings(unittest.TestCase):
    def setUp(self):
        self.app_id = "test_app_id"
        self.cert_id = "test_cert_id"
        os.environ['EBAY_CLIENT_ID'] = self.app_id
        os.environ['EBAY_CLIENT_SECRET'] = self.cert_id
        self.ebay = eBayIntegration(use_sandbox=True)
        self.ebay.access_token = "valid_token"
        self.ebay.token_manager = MagicMock()
        self.ebay.token_manager.get_valid_token.return_value = "valid_token"

    @patch('services.ebay_integration.requests.get')
    def test_get_active_listings_success(self, mock_get):
        # Mock successful eBay API responses via side_effect to distinguish URL paths
        def mock_get_side_effect(url, headers=None, params=None):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            if "offer" in url:
                mock_resp.json.return_value = {
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
                    ],
                    "next": None
                }
            elif "inventory_item" in url:
                mock_resp.json.return_value = {
                    "total": 2,
                    "inventoryItems": [
                        {
                            "sku": "SKU1",
                            "product": {"title": "Test Listing 1"}
                        },
                        {
                            "sku": "SKU2",
                            "product": {"title": "Test Listing 2"}
                        }
                    ]
                }
            return mock_resp

        mock_get.side_effect = mock_get_side_effect

        listings = self.ebay.get_active_listings()

        # Should only return the 2 PUBLISHED listings
        self.assertEqual(len(listings), 2)
        self.assertEqual(listings[0]['ebay_listing_id'], "123456789")
        self.assertEqual(listings[0]['title'], "Test Listing 1")
        self.assertEqual(listings[0]['listing_title'], "Test Listing 1")
        self.assertEqual(listings[0]['price'], 249.99)
        self.assertEqual(listings[0]['listing_price'], 249.99)
        self.assertEqual(listings[0]['listing_status'], "active")

        # Verify API calls
        self.assertEqual(mock_get.call_count, 2)
        args_offer, kwargs_offer = mock_get.call_args_list[0]
        self.assertIn('/sell/inventory/v1/offer', args_offer[0])
        self.assertEqual(kwargs_offer['headers']['Authorization'], "Bearer valid_token")
        self.assertEqual(kwargs_offer['params']['marketplace_id'], "EBAY_US")

        args_inv, kwargs_inv = mock_get.call_args_list[1]
        self.assertIn('/sell/inventory/v1/inventory_item', args_inv[0])
        self.assertEqual(kwargs_inv['headers']['Authorization'], "Bearer valid_token")
        self.assertEqual(kwargs_inv['params']['limit'], 100)
        self.assertEqual(kwargs_inv['params']['offset'], 0)

    @patch('services.ebay_integration.requests.get')
    @patch('services.ebay_integration.eBayIntegration.refresh_access_token')
    def test_get_active_listings_token_refresh(self, mock_refresh, mock_get):
        # Mock 401 Unauthorized then 200 Success
        call_count = [0]
        def mock_get_side_effect(url, headers=None, params=None):
            mock_resp = MagicMock()
            if "offer" in url:
                call_count[0] += 1
                if call_count[0] == 1:
                    mock_resp.status_code = 401
                    return mock_resp

                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "offers": [
                        {
                            "listingId": "123",
                            "status": "PUBLISHED",
                            "listing": {"title": "Refreshed"},
                            "pricingSummary": {"price": {"value": "10.0", "currency": "USD"}},
                            "sku": "SKU_REFRESHED"
                        }
                    ],
                    "next": None
                }
            elif "inventory_item" in url:
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "total": 1,
                    "inventoryItems": [
                        {
                            "sku": "SKU_REFRESHED",
                            "product": {"title": "Refreshed Inventory"}
                        }
                    ]
                }
            else:
                 mock_resp.status_code = 500

            return mock_resp

        mock_get.side_effect = mock_get_side_effect
        mock_refresh.return_value = True
        self.ebay.access_token = "expired_token"

        listings = self.ebay.get_active_listings()

        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0]['listing_title'], "Refreshed")

        # Verify refresh was called and then retry happened
        self.assertEqual(mock_get.call_count, 3) # 401 offer, 200 offer, 200 inventory
        mock_refresh.assert_called_once()

    @patch('services.ebay_integration.requests.get')
    def test_get_active_listings_error_response(self, mock_get):
        # Mock API error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        listings = self.ebay.get_active_listings()

        self.assertEqual(listings, [])

if __name__ == '__main__':
    unittest.main()
