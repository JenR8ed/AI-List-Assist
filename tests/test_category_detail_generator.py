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

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

if __name__ == '__main__':
    unittest.main()
