
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure the root directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules before importing CategoryDetailGenerator
with patch.dict(sys.modules, {
    'services.ebay_category_service': MagicMock(),
    'services.gemini_rest_client': MagicMock(),
    'requests': MagicMock(),
    'httpx': MagicMock(),
    'PIL': MagicMock(),
    'google': MagicMock(),
    'google.generativeai': MagicMock(),
    'dotenv': MagicMock(),
    'flask': MagicMock()
}):
    from services.category_detail_generator import CategoryDetailGenerator

class TestCategoryDetailGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = CategoryDetailGenerator()
        # Mock the category service behavior
        self.generator.category_service.get_category_aspects = MagicMock()

    def test_generate_questions_missing_fields(self):
        # Setup mock aspects
        self.generator.category_service.get_category_aspects.return_value = {
            "required": [
                {"name": "Brand", "mode": "FREETEXT", "values": []},
                {"name": "Color", "mode": "FREETEXT", "values": []}
            ]
        }

        # Scenario: Brand is known, Color is missing
        known_data = {"Brand": "Sony", "item_name": "Headphones"}
        questions = self.generator.generate_questions("293", known_data)

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["field"], "Color")
        self.assertIn("color", questions[0]["question"].lower())

    def test_generate_questions_case_insensitivity(self):
        # Setup mock aspects with mixed case
        self.generator.category_service.get_category_aspects.return_value = {
            "required": [
                {"name": "BRAND", "mode": "FREETEXT", "values": []}
            ]
        }

        # Known data with different case
        known_data = {"brand": "Apple"}
        questions = self.generator.generate_questions("293", known_data)

        # BRAND should be considered known despite case difference
        self.assertEqual(len(questions), 0)

    def test_validate_data(self):
        self.generator.category_service.get_category_aspects.return_value = {
            "required": [
                {"name": "Brand", "mode": "FREETEXT", "values": []},
                {"name": "Type", "mode": "SELECT", "values": ["Phone", "Laptop"]}
            ]
        }

        # Valid data
        valid_data = {"Brand": "Samsung", "Type": "Phone"}
        result = self.generator.validate_data("293", valid_data)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["missing"]), 0)
        self.assertEqual(len(result["invalid"]), 0)

        # Missing data
        missing_data = {"Brand": "Samsung"}
        result = self.generator.validate_data("293", missing_data)
        self.assertFalse(result["valid"])
        self.assertIn("Type", result["missing"])

        # Invalid SELECT value
        invalid_data = {"Brand": "Samsung", "Type": "Toaster"}
        result = self.generator.validate_data("293", invalid_data)
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["invalid"]), 1)
        self.assertEqual(result["invalid"][0]["field"], "Type")

    def test_suggest_category_from_data(self):
        # Test electronics
        item = {"item_name": "iPhone 13"}
        suggestions = self.generator.suggest_category_from_data(item)
        self.assertEqual(suggestions[0]["category_id"], "293")

        # Test clothing
        item = {"item_name": "Blue Denim Pants"}
        suggestions = self.generator.suggest_category_from_data(item)
        self.assertEqual(suggestions[0]["category_id"], "1059")

if __name__ == '__main__':
    unittest.main()
