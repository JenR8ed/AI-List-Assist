import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Mock missing dependencies to avoid ImportErrors from services/__init__.py


# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.category_detail_generator import CategoryDetailGenerator

class TestCategoryDetailGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = CategoryDetailGenerator()

    def test_suggest_category_from_data_electronics(self):
        # Test various electronics keywords
        keywords = ['phone', 'headphone', 'electronic', 'computer', 'laptop']
        for word in keywords:
            item_data = {'item_name': f'My {word}'}
            suggestions = self.generator.suggest_category_from_data(item_data)
            self.assertEqual(suggestions[0]['category_id'], '293', f"Failed for keyword: {word}")
            self.assertEqual(suggestions[0]['confidence'], 0.8, f"Failed for keyword: {word}")

    def test_suggest_category_from_data_clothing(self):
        # Test various clothing keywords
        keywords = ['shirt', 'pants', 'clothing', 'jacket']
        for word in keywords:
            item_data = {'item_name': f'Cool {word}'}
            suggestions = self.generator.suggest_category_from_data(item_data)
            self.assertEqual(suggestions[0]['category_id'], '1059', f"Failed for keyword: {word}")
            self.assertEqual(suggestions[0]['confidence'], 0.7, f"Failed for keyword: {word}")

    def test_suggest_category_from_data_collectibles(self):
        # Test various collectibles keywords
        keywords = ['vintage', 'collectible', 'antique']
        for word in keywords:
            item_data = {'item_name': f'{word} item'}
            suggestions = self.generator.suggest_category_from_data(item_data)
            self.assertEqual(suggestions[0]['category_id'], '20081', f"Failed for keyword: {word}")
            self.assertEqual(suggestions[0]['confidence'], 0.6, f"Failed for keyword: {word}")

    def test_suggest_category_from_data_automotive(self):
        # Test various automotive keywords
        keywords = ['car', 'auto', 'vehicle', 'engine']
        for word in keywords:
            item_data = {'item_name': f'{word} part'}
            suggestions = self.generator.suggest_category_from_data(item_data)
            self.assertEqual(suggestions[0]['category_id'], '6024', f"Failed for keyword: {word}")
            self.assertEqual(suggestions[0]['confidence'], 0.7, f"Failed for keyword: {word}")

    def test_suggest_category_from_data_default(self):
        # Test unrecognized item
        item_data = {'item_name': 'unrecognized item'}
        suggestions = self.generator.suggest_category_from_data(item_data)
        self.assertEqual(suggestions[0]['category_id'], '293')
        self.assertEqual(suggestions[0]['confidence'], 0.3)

    def test_suggest_category_from_data_case_insensitive(self):
        # Test case insensitivity
        item_data = {'item_name': 'PHONE'}
        suggestions = self.generator.suggest_category_from_data(item_data)
        self.assertEqual(suggestions[0]['category_id'], '293')
        self.assertEqual(suggestions[0]['confidence'], 0.8)

    def test_suggest_category_from_data_empty_name(self):
        # Test empty item name
        item_data = {'item_name': ''}
        suggestions = self.generator.suggest_category_from_data(item_data)
        self.assertEqual(suggestions[0]['category_id'], '293')
        self.assertEqual(suggestions[0]['confidence'], 0.3)

    def test_suggest_category_from_data_missing_name(self):
        # Test missing item name
        item_data = {}
        suggestions = self.generator.suggest_category_from_data(item_data)
        self.assertEqual(suggestions[0]['category_id'], '293')
        self.assertEqual(suggestions[0]['confidence'], 0.3)

    @patch('services.category_detail_generator.GeminiRestClient')
    def test_init_exception_handling(self, mock_gemini_client):
        # Test exception block during initialization
        mock_gemini_client.side_effect = Exception("Mocked initialization error")
        generator_with_error = CategoryDetailGenerator()
        self.assertIsNone(generator_with_error.gemini_client)



    @patch.object(CategoryDetailGenerator, 'get_required_fields')
    def test_validate_data_all_valid(self, mock_get_required):
        mock_get_required.return_value = [
            {"name": "Brand", "input_mode": "FREETEXT", "allowed_values": []},
            {"name": "Condition", "input_mode": "SELECT", "allowed_values": ["New", "Used"]}
        ]

        data = {
            "Brand": "Apple",
            "Condition": "New"
        }

        result = self.generator.validate_data("293", data)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["missing"]), 0)
        self.assertEqual(len(result["invalid"]), 0)

    @patch.object(CategoryDetailGenerator, 'get_required_fields')
    def test_validate_data_missing_field(self, mock_get_required):
        mock_get_required.return_value = [
            {"name": "Brand", "input_mode": "FREETEXT", "allowed_values": []},
            {"name": "Model", "input_mode": "FREETEXT", "allowed_values": []}
        ]

        # Missing Model entirely, Brand is empty string
        data = {
            "Brand": ""
        }

        result = self.generator.validate_data("293", data)
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["missing"]), 2)
        self.assertIn("Brand", result["missing"])
        self.assertIn("Model", result["missing"])
        self.assertEqual(len(result["invalid"]), 0)

    @patch.object(CategoryDetailGenerator, 'get_required_fields')
    def test_validate_data_invalid_select(self, mock_get_required):
        mock_get_required.return_value = [
            {"name": "Condition", "input_mode": "SELECT", "allowed_values": ["New", "Used", "Refurbished"]}
        ]

        data = {
            "Condition": "Broken"
        }

        result = self.generator.validate_data("293", data)
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["missing"]), 0)
        self.assertEqual(len(result["invalid"]), 1)
        self.assertEqual(result["invalid"][0]["field"], "Condition")
        self.assertEqual(result["invalid"][0]["value"], "Broken")
        self.assertEqual(result["invalid"][0]["allowed"], ["New", "Used", "Refurbished"])

if __name__ == '__main__':
    unittest.main()
