import unittest
from unittest.mock import patch
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.valuation_service import ValuationService
from models.agent_contracts import Profitability

class TestValuationService(unittest.TestCase):
    def setUp(self):
        # EBayTokenManager is imported inside __init__
        with patch('services.ebay_token_manager.EBayTokenManager') as MockTokenManager:
            self.mock_token_manager = MockTokenManager.return_value
            self.mock_token_manager.get_valid_token.return_value = "mock_token"
            self.service = ValuationService(use_sandbox=True)

    @patch('services.valuation_service.requests.Session.get')
    def test_evaluate_item_requests_exception(self, mock_get):
        """Test that ValuationService handles exceptions raised by requests.get correctly."""
        # Setup the mock to raise an exception
        mock_get.side_effect = Exception("Mock network error")

        # Call evaluate_item with dummy data
        item_data = {
            "item_id": "test_id_123",
            "item_name": "Test Item",
            "brand": "TestBrand"
        }

        # The service should catch the exception and return a valid ItemValuation
        # using the base fallback estimated_value (19.99).
        result = self.service.evaluate_item(
            image_base64="dummy_base64",
            content_type="image/jpeg",
            item_data=item_data
        )

        # Assertions
        self.assertEqual(mock_get.call_count, 0)
        self.assertEqual(result.item_id, "test_id_123")
        self.assertEqual(result.estimated_value, 19.99)
        self.assertEqual(result.profitability, Profitability.MEDIUM)

if __name__ == '__main__':
    unittest.main()
