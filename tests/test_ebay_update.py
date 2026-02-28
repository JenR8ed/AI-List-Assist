
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Mocking modules that might fail on import
sys.modules['flask'] = MagicMock()
sys.modules['flask_sqlalchemy'] = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['httpx'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['PIL'] = MagicMock()

from services.ebay_integration import eBayIntegration

class TestEBayUpdate(unittest.TestCase):
    def setUp(self):
        self.ebay = eBayIntegration(
            app_id="test_app",
            cert_id="test_cert",
            use_sandbox=True
        )
        self.ebay.access_token = "test_token"

    @patch('requests.get')
    @patch('requests.put')
    def test_update_listing_success(self, mock_put, mock_get):
        # Mock responses
        # 1. Mock _get_inventory_item
        mock_get_item = MagicMock()
        mock_get_item.status_code = 200
        mock_get_item.json.return_value = {
            "product": {
                "title": "Old Title",
                "description": "Old Description",
                "aspects": {"Brand": ["Old Brand"]}
            },
            "condition": "USED_EXCELLENT"
        }

        # 2. Mock _get_offer_id_by_sku
        mock_get_offers = MagicMock()
        mock_get_offers.status_code = 200
        mock_get_offers.json.return_value = {
            "offers": [{"offerId": "test_offer_id"}]
        }

        # 3. Mock _get_offer
        mock_get_offer = MagicMock()
        mock_get_offer.status_code = 200
        mock_get_offer.json.return_value = {
            "offerId": "test_offer_id",
            "sku": "test_sku",
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "pricingSummary": {"price": {"value": "10.00", "currency": "USD"}},
            "listingPolicies": {"fulfillmentPolicyId": "old_policy"}
        }

        # 4. Mock _update_inventory_item and _update_offer
        mock_put_resp = MagicMock()
        mock_put_resp.status_code = 200
        mock_put_resp.json.return_value = {"warnings": []}
        mock_put_resp.content = b'{"warnings": []}'

        mock_get.side_effect = [mock_get_item, mock_get_offers, mock_get_offer]
        mock_put.return_value = mock_put_resp

        # Test data
        sku = "test_sku"
        update_data = {
            "title": "New Title",
            "price": 15.99,
            "fulfillmentPolicyId": "new_policy"
        }

        # Run update
        result = self.ebay.update_listing(sku, update_data)

        # Assertions
        self.assertTrue(result["success"])

        # Verify Inventory Item update
        inventory_call = mock_put.call_args_list[0]
        self.assertIn("inventory_item/test_sku", inventory_call[0][0])
        inventory_payload = inventory_call[1]['json']
        self.assertEqual(inventory_payload["product"]["title"], "New Title")

        # Verify Offer update
        offer_call = mock_put.call_args_list[1]
        self.assertIn("offer/test_offer_id", offer_call[0][0])
        offer_payload = offer_call[1]['json']
        self.assertEqual(offer_payload["pricingSummary"]["price"]["value"], "15.99")
        self.assertEqual(offer_payload["listingPolicies"]["fulfillmentPolicyId"], "new_policy")

    @patch('requests.get')
    def test_update_listing_no_offer(self, mock_get):
        # Mock _get_inventory_item
        mock_get_item = MagicMock()
        mock_get_item.status_code = 200
        mock_get_item.json.return_value = {"product": {"title": "Old"}, "condition": "USED"}

        # Mock _get_offer_id_by_sku (empty)
        mock_get_offers = MagicMock()
        mock_get_offers.status_code = 200
        mock_get_offers.json.return_value = {"offers": []}

        mock_get.side_effect = [mock_get_item, mock_get_offers]

        result = self.ebay.update_listing("test_sku", {"price": 20.0})

        self.assertFalse(result["success"])
        self.assertIn("Could not find offer", result["error"])

if __name__ == '__main__':
    unittest.main()
