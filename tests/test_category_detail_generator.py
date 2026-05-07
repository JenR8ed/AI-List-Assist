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
from services.ebay_category_service import EBayCategoryService

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
    def test_validate_data_valid(self, mock_get_required):
        # Mock required fields
        mock_get_required.return_value = [
            {"name": "Brand", "input_mode": "FREETEXT", "allowed_values": []},
            {"name": "Size", "input_mode": "SELECT", "allowed_values": ["S", "M", "L"]}
        ]

        data = {"Brand": "Nike", "Size": "M"}
        result = self.generator.validate_data("1059", data)

        self.assertTrue(result["valid"])
        self.assertEqual(len(result["missing"]), 0)
        self.assertEqual(len(result["invalid"]), 0)

    @patch.object(CategoryDetailGenerator, 'get_required_fields')
    def test_validate_data_missing_field(self, mock_get_required):
        mock_get_required.return_value = [
            {"name": "Brand", "input_mode": "FREETEXT", "allowed_values": []},
            {"name": "Size", "input_mode": "SELECT", "allowed_values": ["S", "M", "L"]}
        ]

        data = {"Brand": "Nike"} # Size missing
        result = self.generator.validate_data("1059", data)

        self.assertFalse(result["valid"])
        self.assertIn("Size", result["missing"])

    @patch.object(CategoryDetailGenerator, 'get_required_fields')
    def test_validate_data_empty_field(self, mock_get_required):
        mock_get_required.return_value = [
            {"name": "Brand", "input_mode": "FREETEXT", "allowed_values": []}
        ]

        data = {"Brand": ""} # Empty value
        result = self.generator.validate_data("1059", data)

        self.assertFalse(result["valid"])
        self.assertIn("Brand", result["missing"])

    @patch.object(CategoryDetailGenerator, 'get_required_fields')
    def test_validate_data_invalid_select_value(self, mock_get_required):
        mock_get_required.return_value = [
            {"name": "Size", "input_mode": "SELECT", "allowed_values": ["S", "M", "L"]}
        ]

        data = {"Size": "XL"} # Not in allowed_values
        result = self.generator.validate_data("1059", data)

        self.assertFalse(result["valid"])
        self.assertEqual(len(result["invalid"]), 1)
        self.assertEqual(result["invalid"][0]["field"], "Size")
        self.assertEqual(result["invalid"][0]["value"], "XL")
        self.assertEqual(result["invalid"][0]["allowed"], ["S", "M", "L"])

    @patch.object(CategoryDetailGenerator, 'get_required_fields')
    def test_validate_data_multiple_issues(self, mock_get_required):
        mock_get_required.return_value = [
            {"name": "Brand", "input_mode": "FREETEXT", "allowed_values": []},
            {"name": "Size", "input_mode": "SELECT", "allowed_values": ["S", "M", "L"]}
        ]

        data = {"Size": "XL"} # Brand missing, Size invalid
        result = self.generator.validate_data("1059", data)

        self.assertFalse(result["valid"])
        self.assertIn("Brand", result["missing"])
        self.assertEqual(len(result["invalid"]), 1)
        self.assertEqual(result["invalid"][0]["field"], "Size")

    @patch.object(EBayCategoryService, 'get_category_aspects')
    def test_get_required_fields_mapping(self, mock_get_aspects):
        # Mock what EBayCategoryService returns
        mock_get_aspects.return_value = {
            "required": [
                {"name": "Brand", "mode": "FREETEXT", "values": [], "dataType": "STRING"},
                {"name": "Size", "mode": "SELECT", "values": ["S", "M"], "dataType": "STRING"}
            ],
            "recommended": []
        }

        required_fields = self.generator.get_required_fields("1059")

        self.assertEqual(len(required_fields), 2)

        brand_field = next(f for f in required_fields if f["name"] == "Brand")
        self.assertEqual(brand_field["input_mode"], "FREETEXT")
        self.assertTrue(brand_field["required"])
        self.assertEqual(brand_field["data_type"], "STRING")
        self.assertEqual(brand_field["allowed_values"], [])

        size_field = next(f for f in required_fields if f["name"] == "Size")
        self.assertEqual(size_field["input_mode"], "SELECT")
        self.assertEqual(size_field["allowed_values"], ["S", "M"])

    @patch.object(CategoryDetailGenerator, 'get_required_fields')
    def test_generate_questions_missing_some(self, mock_get_required):
        mock_get_required.return_value = [
            {"name": "Brand", "input_mode": "FREETEXT", "allowed_values": []},
            {"name": "Size", "input_mode": "SELECT", "allowed_values": ["S", "M", "L"]},
            {"name": "Color", "input_mode": "FREETEXT", "allowed_values": []}
        ]

        known_data = {"Brand": "Nike"} # Size and Color missing
        questions = self.generator.generate_questions("1059", known_data)

        self.assertEqual(len(questions), 2)
        fields = [q["field"] for q in questions]
        self.assertIn("Size", fields)
        self.assertIn("Color", fields)

        size_question = next(q for q in questions if q["field"] == "Size")
        self.assertEqual(size_question["input_type"], "select")
        self.assertEqual(size_question["options"], ["S", "M", "L"])

        color_question = next(q for q in questions if q["field"] == "Color")
        self.assertEqual(color_question["input_type"], "text")

    @patch.object(CategoryDetailGenerator, 'get_required_fields')
    def test_generate_questions_limit_to_3(self, mock_get_required):
        mock_get_required.return_value = [
            {"name": "F1", "input_mode": "FREETEXT", "allowed_values": []},
            {"name": "F2", "input_mode": "FREETEXT", "allowed_values": []},
            {"name": "F3", "input_mode": "FREETEXT", "allowed_values": []},
            {"name": "F4", "input_mode": "FREETEXT", "allowed_values": []}
        ]

        known_data = {}
        questions = self.generator.generate_questions("1059", known_data)

        self.assertEqual(len(questions), 3)

if __name__ == '__main__':
    unittest.main()
