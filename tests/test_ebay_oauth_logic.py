import unittest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_token_manager import EBayTokenManager

class TestEBayOAuth(unittest.TestCase):
    def setUp(self):
        os.environ['EBAY_CLIENT_ID'] = "test_app_id"
        os.environ['EBAY_CLIENT_SECRET'] = "test_cert_id"
        self.manager = EBayTokenManager(use_sandbox=True)

    @patch('services.ebay_token_manager.requests.post')
    def test_token_manager_refresh_with_refresh_token(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "refreshed_access_token",
            "expires_in": 7200
        }
        mock_post.return_value = mock_response

        self.manager._load_token = MagicMock(return_value={"refresh_token": "existing_refresh_token"})
        self.manager._save_token = MagicMock()

        self.manager.client_id = 'test_id'
        self.manager.client_secret = 'test_secret'
        result = self.manager._refresh_token()

        self.assertIsNotNone(result)
        self.assertEqual(result['access_token'], "refreshed_access_token")

    @patch('services.ebay_token_manager.requests.post')
    def test_token_manager_client_credentials_fallback(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "client_creds_token",
            "expires_in": 7200
        }
        mock_post.return_value = mock_response

        self.manager._load_token = MagicMock(return_value=None)
        self.manager._save_token = MagicMock()

        self.manager.client_id = 'test_id'
        self.manager.client_secret = 'test_secret'
        result = self.manager._refresh_token()

        self.assertIsNotNone(result)
        self.assertEqual(result['access_token'], "client_creds_token")

if __name__ == '__main__':
    unittest.main()
