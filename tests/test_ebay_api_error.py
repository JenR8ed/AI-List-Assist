import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration

class TestEBayApiError(unittest.TestCase):
    @patch.dict(os.environ, {'EBAY_CLIENT_ID': 'test_app_id', 'EBAY_CLIENT_SECRET': 'test_cert_id'})
    def setUp(self):
        self.ebay = eBayIntegration(use_sandbox=True)

    def test_handle_api_error_with_details(self):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "errors": [
                {
                    "errorId": 1001,
                    "message": "Invalid input data"
                }
            ]
        }

        with self.assertRaises(RuntimeError) as context:
            self.ebay._handle_api_error(mock_response, "create_offer")

        self.assertIn("eBay API error in create_offer: 400 - Invalid input data (Error ID: 1001)", str(context.exception))

    def test_handle_api_error_without_details(self):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "errors": [
                {}
            ]
        }

        with self.assertRaises(RuntimeError) as context:
            self.ebay._handle_api_error(mock_response, "get_inventory")

        self.assertIn("eBay API error in get_inventory: 403 - Unknown error (Error ID: Unknown ID)", str(context.exception))

    def test_handle_api_error_empty_errors_array(self):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "errors": []
        }

        with self.assertRaises(RuntimeError) as context:
            self.ebay._handle_api_error(mock_response, "update_listing")

        self.assertIn("eBay API error in update_listing: 404 - [REDACTED]", str(context.exception))

    def test_handle_api_error_invalid_json(self):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with self.assertRaises(RuntimeError) as context:
            self.ebay._handle_api_error(mock_response, "publish_offer")

        self.assertIn("eBay API error in publish_offer: 500 - [REDACTED]", str(context.exception))


    def test_handle_api_error_key_error(self):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 400
        mock_response.json.side_effect = KeyError("missing key")

        with self.assertRaises(RuntimeError) as context:
            self.ebay._handle_api_error(mock_response, "update_inventory_item")

        self.assertIn("eBay API error in update_inventory_item: 400 - [REDACTED]", str(context.exception))

if __name__ == '__main__':
    unittest.main()
