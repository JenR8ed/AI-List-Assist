import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock EBayTokenManager so it doesn't fail on import if dependencies are missing
sys.modules["services.ebay_token_manager"] = MagicMock()

from services.valuation_service import ValuationService
from shared.models import Profitability

class TestValuationService(unittest.TestCase):
    def setUp(self):
        # We need to mock the token_manager that is instantiated in __init__
        self.patcher = patch('services.valuation_service.EBayTokenManager', create=True)
        self.mock_manager_class = self.patcher.start()
        self.mock_token_manager_instance = self.mock_manager_class.return_value

        self.service = ValuationService(use_sandbox=True)

        self.item_data = {
            "item_id": "test-item-123",
            "item_name": "Test Item",
            "brand": "Test Brand"
        }

    def tearDown(self):
        self.patcher.stop()

    def test_initialization(self):
        # Sandbox
        service_sandbox = ValuationService(use_sandbox=True)
        self.assertEqual(service_sandbox.base_url, "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search")

        # Production
        service_prod = ValuationService(use_sandbox=False)
        self.assertEqual(service_prod.base_url, "https://api.ebay.com/buy/browse/v1/item_summary/search")

    @patch('requests.get')
    def test_evaluate_item_success(self, mock_get):
        self.service.token_manager.get_valid_token.return_value = "valid_token"

        # Mock successful eBay API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "itemSummaries": [
                {"price": {"value": "20.00"}},
                {"price": {"value": "30.00"}},
                {"price": {"value": "40.00"}}
            ]
        }
        mock_get.return_value = mock_response

        valuation = self.service.evaluate_item("mock_image", "image/jpeg", self.item_data)

        # 20 + 30 + 40 = 90 / 3 = 30.0
        self.assertEqual(valuation.estimated_value, 30.0)
        self.assertEqual(valuation.profitability, Profitability.MEDIUM)
        self.assertTrue(valuation.worth_listing)
        self.assertEqual(valuation.item_id, "test-item-123")
        self.assertEqual(valuation.item_name, "Test Item")
        self.assertEqual(valuation.brand, "Test Brand")

        # Verify API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], self.service.base_url)
        self.assertEqual(kwargs['headers']['Authorization'], "Bearer valid_token")
        self.assertEqual(kwargs['params']['q'], "Test Brand Test Item")
        self.assertEqual(kwargs['params']['filter'], "buyingOptions:{FIXED_PRICE}")

    @patch('requests.get')
    def test_evaluate_item_no_token(self, mock_get):
        self.service.token_manager.get_valid_token.return_value = None

        valuation = self.service.evaluate_item("mock_image", "image/jpeg", self.item_data)

        # Should use base fallback
        self.assertEqual(valuation.estimated_value, 19.99)
        self.assertEqual(valuation.profitability, Profitability.MEDIUM)

        # Should not call API
        mock_get.assert_not_called()

    @patch('requests.get')
    def test_evaluate_item_empty_keywords(self, mock_get):
        self.service.token_manager.get_valid_token.return_value = "valid_token"

        empty_data = {
            "item_name": "",
            "brand": ""
        }
        valuation = self.service.evaluate_item("mock_image", "image/jpeg", empty_data)

        # Should use base fallback
        self.assertEqual(valuation.estimated_value, 19.99)

        # Should not call API
        mock_get.assert_not_called()

    @patch('requests.get')
    def test_evaluate_item_api_error(self, mock_get):
        self.service.token_manager.get_valid_token.return_value = "valid_token"

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        valuation = self.service.evaluate_item("mock_image", "image/jpeg", self.item_data)

        # Should use base fallback
        self.assertEqual(valuation.estimated_value, 19.99)

    @patch('requests.get')
    def test_evaluate_item_exception(self, mock_get):
        self.service.token_manager.get_valid_token.return_value = "valid_token"
        mock_get.side_effect = Exception("Connection Error")

        valuation = self.service.evaluate_item("mock_image", "image/jpeg", self.item_data)

        # Should use base fallback
        self.assertEqual(valuation.estimated_value, 19.99)

    def test_determine_profitability(self):
        self.assertEqual(self.service._determine_profitability(10.0), Profitability.LOW)
        self.assertEqual(self.service._determine_profitability(14.99), Profitability.LOW)

        self.assertEqual(self.service._determine_profitability(15.0), Profitability.MEDIUM)
        self.assertEqual(self.service._determine_profitability(30.0), Profitability.MEDIUM)
        self.assertEqual(self.service._determine_profitability(49.99), Profitability.MEDIUM)

        self.assertEqual(self.service._determine_profitability(50.0), Profitability.HIGH)
        self.assertEqual(self.service._determine_profitability(100.0), Profitability.HIGH)

if __name__ == '__main__':
    unittest.main()
