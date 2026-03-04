import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration

class TestEBayCreateInventoryItem(unittest.TestCase):
    def setUp(self):
        self.app_id = "test_app_id"
        self.cert_id = "test_cert_id"
        os.environ['EBAY_CLIENT_ID'] = self.app_id
        os.environ['EBAY_CLIENT_SECRET'] = self.cert_id
        self.ebay = eBayIntegration(use_sandbox=True)
        self.ebay.access_token = "valid_token"

    @patch('requests.put')
    @patch('services.ebay_token_manager.EBayTokenManager.get_valid_token')
    def test_create_inventory_item_success(self, mock_get_token, mock_put):
        mock_get_token.return_value = "valid_token"
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        inventory_item = {
            "sku": "TEST-SKU-123",
            "product": {"title": "Test Product"}
        }

        result = self.ebay._create_inventory_item(inventory_item)

        self.assertEqual(result["sku"], "TEST-SKU-123")
        self.assertEqual(result["status"], "created")

        # Verify call
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        self.assertIn('/sell/inventory/v1/inventory_item/TEST-SKU-123', args[0])
        self.assertEqual(kwargs['headers']['Authorization'], "Bearer valid_token")
        self.assertEqual(kwargs['json'], inventory_item)

    @patch('requests.put')
    @patch('services.ebay_token_manager.EBayTokenManager.get_valid_token')
    def test_create_inventory_item_error(self, mock_get_token, mock_put):
        mock_get_token.return_value = "valid_token"
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "errors": [
                {
                    "errorId": 25709,
                    "domain": "API_INVENTORY",
                    "category": "REQUEST",
                    "message": "Invalid SKU"
                }
            ]
        }
        mock_put.return_value = mock_response

        inventory_item = {"sku": "INVALID-SKU"}

        with self.assertRaises(RuntimeError) as cm:
            self.ebay._create_inventory_item(inventory_item)

        self.assertIn("Invalid SKU", str(cm.exception))
        self.assertIn("25709", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
