import unittest
from unittest.mock import patch
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.valuation_service import ValuationService
from shared.models import Profitability

class TestValuationService(unittest.TestCase):
    def setUp(self):
        # EBayTokenManager is imported inside __init__
        with patch('services.ebay_token_manager.EBayTokenManager') as MockTokenManager:
            self.mock_token_manager = MockTokenManager.return_value
            self.mock_token_manager.get_valid_token.return_value = "mock_token"
            self.service = ValuationService(use_sandbox=True)

    @patch('services.ebay_integration.requests.Session.get')
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

        # A failed lookup must not fabricate a price or confidence.
        result = self.service.evaluate_item(
            image_base64="dummy_base64",
            content_type="image/jpeg",
            item_data=item_data
        )

        # Assertions
        mock_get.assert_called_once()
        self.assertEqual(result.item_id, "test_id_123")
        self.assertIsNone(result.estimated_value)
        self.assertEqual(result.status, 'unavailable')
        self.assertEqual(result.source, 'live')
        self.assertEqual(result.value_range, {})
        self.assertEqual(result.confidence, 0.0)
        self.assertEqual(result.profitability, Profitability.NOT_RECOMMENDED)
        self.assertFalse(result.worth_listing)

    def test_no_token_marks_price_unavailable_without_request(self):
        self.mock_token_manager.get_valid_token.return_value = None
        with patch.object(self.service.session, 'get') as mock_get:
            result = self.service.evaluate_item('', 'image/jpeg', {'item_name': 'Camera'})
        mock_get.assert_not_called()
        self.assertIsNone(result.estimated_value)
        self.assertEqual(result.status, 'unavailable')
        self.assertEqual(result.source, 'simulated')

    def test_browse_results_are_labeled_as_current_asking_prices(self):
        with patch.object(self.service.session, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {'itemSummaries': [
                {'price': {'value': '20.00'}}, {'price': {'value': '40.00'}}]}
            result = self.service.evaluate_item('', 'image/jpeg', {'item_name': 'Camera'})
        self.assertEqual(result.estimated_value, 30.0)
        self.assertEqual(result.source, 'live')
        self.assertEqual(result.status, 'available')
        self.assertEqual(result.confidence, 0.0)
        self.assertIn('asking prices', result.key_factors[0])

if __name__ == '__main__':
    unittest.main()
