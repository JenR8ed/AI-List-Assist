import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_category_service import EBayCategoryService

class TestEBayCategoryService(unittest.TestCase):
    def setUp(self):
        # Clear environment variables before each test
        if 'EBAY_CATEGORY_TREE_ID' in os.environ:
            del os.environ['EBAY_CATEGORY_TREE_ID']

    def test_default_initialization(self):
        service = EBayCategoryService()
        # Should now default to "0" and use sandbox URL
        self.assertEqual(service.category_tree_id, "0")
        self.assertEqual(service.base_url, "https://api.sandbox.ebay.com/commerce/taxonomy/v1/category_tree")

    def test_parameterized_initialization(self):
        service = EBayCategoryService(category_tree_id="200", use_sandbox=False)
        self.assertEqual(service.category_tree_id, "200")
        self.assertEqual(service.base_url, "https://api.ebay.com/commerce/taxonomy/v1/category_tree")

    def test_env_var_initialization(self):
        os.environ['EBAY_CATEGORY_TREE_ID'] = "300"
        service = EBayCategoryService()
        self.assertEqual(service.category_tree_id, "300")

    @patch('services.ebay_category_service.requests.get')
    @patch('services.ebay_token_manager.EBayTokenManager.get_valid_token')
    def test_get_category_aspects_api_call(self, mock_token, mock_get):
        mock_token.return_value = "valid_token"
        service = EBayCategoryService(access_token="valid_token")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"aspects": []}
        mock_get.return_value = mock_response

        # Ensure we are using the mocked get_valid_token
        self.assertEqual(service.token_manager.get_valid_token(), "valid_token")

        service.get_category_aspects("123")

        # Verify URL used
        self.assertTrue(mock_get.called)
        args, kwargs = mock_get.call_args
        expected_url = f"{service.base_url}/{service.category_tree_id}/get_item_aspects_for_category"
        self.assertEqual(args[0], expected_url)

if __name__ == '__main__':
    unittest.main()
