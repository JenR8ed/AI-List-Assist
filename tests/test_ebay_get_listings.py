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

    @patch('requests.get')
    def test_get_active_listings_success(self, mock_get):
        # Mock successful eBay API response for both offers and inventory
        def mock_get_effect(url, *args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            if 'offer' in url:
                mock_response.json.return_value = {
                    "total": 3,
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
            elif 'inventory' in url:
                mock_response.json.return_value = {
                    "total": 3,
                    "inventoryItems": [
                        {
                            "sku": "SKU1",
                            "product": {"title": "Test Listing 1"}
                        },
                        {
                            "sku": "SKU2",
                            "product": {"title": "Test Listing 2"}
                        },
                        {
                            "sku": "SKU3",
                            "product": {"title": "Test Listing 3"}
                        }
                    ]
                }
            return mock_response

        mock_get.side_effect = mock_get_effect

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


    @patch('requests.get')
    @patch('services.ebay_integration.eBayIntegration.refresh_access_token')
    def test_get_active_listings_token_refresh(self, mock_refresh, mock_get):
        # Mock 401 Unauthorized then 200 Success
        call_counts = {'offer': 0, 'inventory': 0}

        def mock_get_effect(url, *args, **kwargs):
            mock_response = MagicMock()
            if 'offer' in url:
                call_counts['offer'] += 1
                if call_counts['offer'] == 1:
                    mock_response.status_code = 401
                else:
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "total": 1,
                        "offers": [
                            {
                                "listingId": "123",
                                "status": "PUBLISHED",
                                "sku": "SKU1",
                                "listing": {"title": "Refreshed"},
                                "pricingSummary": {"price": {"value": "10.0", "currency": "USD"}}
                            }
                        ]
                    }
            elif 'inventory' in url:
                call_counts['inventory'] += 1
                if call_counts['inventory'] == 1:
                    mock_response.status_code = 401
                else:
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "total": 1,
                        "inventoryItems": [
                            {
                                "sku": "SKU1",
                                "product": {"title": "Refreshed"}
                            }
                        ]
                    }
            return mock_response

        mock_get.side_effect = mock_get_effect
        mock_refresh.return_value = True
        self.ebay.access_token = "expired_token"

        listings = self.ebay.get_active_listings()

        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0]['listing_title'], "Refreshed")

        # Verify refresh was called
        mock_refresh.assert_called()


    @patch('requests.get')
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
