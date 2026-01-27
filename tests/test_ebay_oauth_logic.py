import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration
from services.ebay_token_manager import EBayTokenManager

class TestEBayOAuth(unittest.TestCase):
    def setUp(self):
        self.app_id = "test_app_id"
        self.cert_id = "test_cert_id"
        os.environ['EBAY_CLIENT_ID'] = self.app_id
        os.environ['EBAY_CLIENT_SECRET'] = self.cert_id

    @patch('services.ebay_token_manager.EBayTokenManager.exchange_code_for_token')
    def test_ebay_integration_authenticate_success(self, mock_exchange):
        # Mock successful exchange
        mock_exchange.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 7200
        }

        ebay = eBayIntegration(app_id=self.app_id, cert_id=self.cert_id)
        result = ebay.authenticate("auth_code", "http://redirect.uri")

        self.assertTrue(result)
        self.assertEqual(ebay.access_token, "test_access_token")
        self.assertEqual(ebay.refresh_token, "test_refresh_token")

        # Verify the call to token manager
        mock_exchange.assert_called_once_with("auth_code", "http://redirect.uri")

    @patch('services.ebay_token_manager.EBayTokenManager._refresh_token')
    def test_ebay_integration_refresh_token_success(self, mock_refresh):
        # Mock successful refresh
        mock_refresh.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 7200
        }

        ebay = eBayIntegration(app_id=self.app_id, cert_id=self.cert_id)
        result = ebay.refresh_access_token()

        self.assertTrue(result)
        self.assertEqual(ebay.access_token, "new_access_token")
        self.assertEqual(ebay.refresh_token, "new_refresh_token")

        # Verify the call to token manager
        mock_refresh.assert_called_once()

    @patch('requests.post')
    @patch('services.ebay_token_manager.EBayTokenManager._save_token')
    @patch('services.ebay_token_manager.EBayTokenManager._update_env')
    @patch('services.ebay_token_manager.EBayTokenManager._load_token')
    def test_token_manager_refresh_with_refresh_token(self, mock_load, mock_update_env, mock_save, mock_post):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "refreshed_access_token",
            "expires_in": 7200
        }
        mock_post.return_value = mock_response

        # Mock existing token data with a refresh token
        mock_load.return_value = {"refresh_token": "existing_refresh_token"}

        manager = EBayTokenManager()
        result = manager._refresh_token()

        self.assertIsNotNone(result)
        self.assertEqual(result['access_token'], "refreshed_access_token")

        # Verify it used refresh_token grant
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['data']['grant_type'], 'refresh_token')
        self.assertEqual(kwargs['data']['refresh_token'], 'existing_refresh_token')

    @patch('requests.post')
    @patch('services.ebay_token_manager.EBayTokenManager._save_token')
    @patch('services.ebay_token_manager.EBayTokenManager._update_env')
    @patch('services.ebay_token_manager.EBayTokenManager._load_token')
    def test_token_manager_client_credentials_fallback(self, mock_load, mock_update_env, mock_save, mock_post):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "client_creds_token",
            "expires_in": 7200
        }
        mock_post.return_value = mock_response

        # Mock no existing token data
        mock_load.return_value = None

        manager = EBayTokenManager()
        result = manager._refresh_token()

        self.assertIsNotNone(result)
        self.assertEqual(result['access_token'], "client_creds_token")

        # Verify it used client_credentials grant
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['data']['grant_type'], 'client_credentials')

if __name__ == '__main__':
    unittest.main()
