import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration
from models.agent_contracts import ListingDraft, ItemCondition
from datetime import datetime

class TestEBayCreateInventoryItem(unittest.TestCase):
    def setUp(self):
        os.environ['EBAY_CLIENT_ID'] = "test_app_id"
        os.environ['EBAY_CLIENT_SECRET'] = "test_cert_id"
        self.ebay = eBayIntegration(use_sandbox=True)
        self.ebay.token_manager.get_valid_token = MagicMock(return_value="valid_token")

    @patch('services.ebay_integration.requests.put')
    def test_create_inventory_item_success(self, mock_put):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        draft = ListingDraft(
            listing_id="test_listing_id",
            item_id="test_item_id",
            title="Test Title",
            description="Test Description",
            category_id="1234",
            condition=ItemCondition.NEW,
            price=10.0,
            images=["image_url"]
        )

        success = self.ebay._create_inventory_item({"sku": "SKU123"})

        self.assertEqual(success['status'], 'created')
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        self.assertIn('SKU123', args[0])
        self.assertEqual(kwargs['headers']['Authorization'], "Bearer valid_token")

    @patch('services.ebay_integration.requests.put')
    def test_create_inventory_item_error(self, mock_put):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"errors": [{"message": "Invalid SKU"}]}
        mock_put.return_value = mock_response

        draft = ListingDraft(
            listing_id="test_listing_id",
            item_id="test_item_id",
            title="Test Title",
            description="Test Description",
            category_id="1234",
            condition=ItemCondition.NEW,
            price=10.0
        )

        with self.assertRaises(RuntimeError):
            self.ebay._create_inventory_item({"sku": "SKU123"})

if __name__ == '__main__':
    unittest.main()
