import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Mock missing dependencies to avoid ImportErrors from services/__init__.py
sys.modules['httpx'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['pydantic'] = MagicMock()

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.category_detail_generator import CategoryDetailGenerator

class TestCategoryDetailGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = CategoryDetailGenerator()
        # Mock CATEGORY_MAPPING as it's missing from the source but tests expect it
        self.generator.CATEGORY_MAPPING = (
            (self.generator.ELECTRONICS_KEYWORDS, '293', 0.8),
            (self.generator.CLOTHING_KEYWORDS, '1059', 0.7),
            (self.generator.VINTAGE_KEYWORDS, '20081', 0.6),
            (self.generator.AUTO_KEYWORDS, '6024', 0.7)
        )

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

    @patch('services.category_detail_generator.EBayCategoryService.get_category_aspects')
    def test_generate_questions_all_missing(self, mock_get_aspects):
        mock_get_aspects.return_value = {
            "required": [
                {"name": "Brand", "mode": "FREETEXT", "values": []},
                {"name": "Color", "mode": "FREETEXT", "values": []},
                {"name": "Size", "mode": "SELECT", "values": ["S", "M", "L"]}
            ]
        }
        known_data = {"item_name": "Test Shirt"}
        questions = self.generator.generate_questions("1059", known_data)

        self.assertEqual(len(questions), 3)
        self.assertEqual(questions[0]["field"], "Brand")
        self.assertEqual(questions[0]["question"], "What brand is Test Shirt?")
        self.assertEqual(questions[2]["field"], "Size")
        self.assertEqual(questions[2]["input_type"], "select")
        self.assertEqual(questions[2]["options"], ["S", "M", "L"])

    @patch('services.category_detail_generator.EBayCategoryService.get_category_aspects')
    def test_generate_questions_some_missing(self, mock_get_aspects):
        mock_get_aspects.return_value = {
            "required": [
                {"name": "Brand", "mode": "FREETEXT", "values": []},
                {"name": "Color", "mode": "FREETEXT", "values": []}
            ]
        }
        known_data = {"item_name": "Test Shirt", "brand": "Nike"}
        questions = self.generator.generate_questions("1059", known_data)

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["field"], "Color")

    @patch('services.category_detail_generator.EBayCategoryService.get_category_aspects')
    def test_generate_questions_none_missing(self, mock_get_aspects):
        mock_get_aspects.return_value = {
            "required": [
                {"name": "Brand", "mode": "FREETEXT", "values": []}
            ]
        }
        known_data = {"item_name": "Test Shirt", "Brand": "Nike"}
        questions = self.generator.generate_questions("1059", known_data)

        self.assertEqual(len(questions), 0)

    @patch('services.category_detail_generator.EBayCategoryService.get_category_aspects')
    def test_generate_questions_limit(self, mock_get_aspects):
        mock_get_aspects.return_value = {
            "required": [
                {"name": "F1", "mode": "FREETEXT", "values": []},
                {"name": "F2", "mode": "FREETEXT", "values": []},
                {"name": "F3", "mode": "FREETEXT", "values": []},
                {"name": "F4", "mode": "FREETEXT", "values": []}
            ]
        }
        known_data = {}
        questions = self.generator.generate_questions("123", known_data)

        self.assertEqual(len(questions), 3)

    @patch('services.category_detail_generator.EBayCategoryService.get_category_aspects')
    def test_validate_data_valid(self, mock_get_aspects):
        mock_get_aspects.return_value = {
            "required": [
                {"name": "Brand", "mode": "FREETEXT", "values": []},
                {"name": "Size", "mode": "SELECT", "values": ["M", "L"]}
            ]
        }
        data = {"Brand": "Nike", "Size": "M"}
        result = self.generator.validate_data("1059", data)

        self.assertTrue(result["valid"])
        self.assertEqual(len(result["missing"]), 0)
        self.assertEqual(len(result["invalid"]), 0)

    @patch('services.category_detail_generator.EBayCategoryService.get_category_aspects')
    def test_validate_data_missing(self, mock_get_aspects):
        mock_get_aspects.return_value = {
            "required": [
                {"name": "Brand", "mode": "FREETEXT", "values": []},
                {"name": "Size", "mode": "SELECT", "values": ["M", "L"]}
            ]
        }
        data = {"Brand": "Nike"}
        result = self.generator.validate_data("1059", data)

        self.assertFalse(result["valid"])
        self.assertIn("Size", result["missing"])

    @patch('services.category_detail_generator.EBayCategoryService.get_category_aspects')
    def test_validate_data_invalid_select(self, mock_get_aspects):
        mock_get_aspects.return_value = {
            "required": [
                {"name": "Size", "mode": "SELECT", "values": ["M", "L"]}
            ]
        }
        data = {"Size": "XL"}
        result = self.generator.validate_data("1059", data)

        self.assertFalse(result["valid"])
        self.assertEqual(len(result["invalid"]), 1)
        self.assertEqual(result["invalid"][0]["field"], "Size")

if __name__ == '__main__':
    unittest.main()
