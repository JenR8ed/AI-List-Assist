import sys
import unittest
import os
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import directly since dependencies are available in this isolated pytest runner
from services.mock_valuation_service import MockValuationService
from shared.models import Profitability, ItemValuation

class TestMockValuationService(unittest.TestCase):
    def setUp(self):
        self.service = MockValuationService()

    def test_evaluate_item_returns_valid_item_valuation(self):
        # We test that the mock valuation service, which has deterministic fallback output based on hash,
        # returns a valid ItemValuation object when we call evaluate_item.

        # Test case 1: Fallback (hash base_64)
        result1 = self.service.evaluate_item("dummy_base64_1", "image/jpeg", None)
        self.assertIsInstance(result1, ItemValuation)

        # Test case 2: Detected brand matching
        detected_item_apple = {"brand": "Apple", "item_id": "apple_id_123"}
        result2 = self.service.evaluate_item("dummy_base64_2", "image/jpeg", detected_item_apple)
        self.assertIsInstance(result2, ItemValuation)

        # Test case 3: Detected category matching
        detected_item_mug = {"probable_category": "mug", "item_id": "mug_1"}
        result3 = self.service.evaluate_item("dummy_base64_3", "image/jpeg", detected_item_mug)
        self.assertIsInstance(result3, ItemValuation)

if __name__ == '__main__':
    unittest.main()
