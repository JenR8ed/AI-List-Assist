import unittest
from unittest.mock import patch, MagicMock
from services.ebay_token_manager import EBayTokenManager

class TestEBayTokenManagerRefreshToken(unittest.TestCase):
    """
    Unit tests for EBayTokenManager._refresh_token method.
    Covers happy path (user-delegated and application flows),
    missing credentials, API errors, and exception handling.
    """

    def setUp(self):
        self.client_id = "test_client_id"
        self.client_secret = "test_client_secret"
        self.manager = EBayTokenManager(
            client_id=self.client_id,
            client_secret=self.client_secret,
            use_sandbox=True
        )

    @patch('requests.post')
    def test_refresh_token_no_credentials(self, mock_post):
        """Test that _refresh_token returns None if credentials are missing."""
        self.manager.client_id = None
        result = self.manager._refresh_token()
        self.assertIsNone(result)
        mock_post.assert_not_called()

    @patch('requests.post')
    @patch('services.ebay_token_manager.EBayTokenManager._load_token')
    @patch('services.ebay_token_manager.EBayTokenManager._save_token')
    def test_refresh_token_with_refresh_token_success(self, mock_save, mock_load, mock_post):
        """Test successful refresh using a user-delegated refresh_token."""
        # Setup mocks
        existing_data = {"refresh_token": "old_refresh_token", "some_old_field": "old_value"}
        mock_load.return_value = existing_data

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 7200
        }
        mock_post.return_value = mock_response

        # Execute
        result = self.manager._refresh_token()

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["access_token"], "new_access_token")
        # Ensure refresh token and other existing fields are preserved/merged
        self.assertEqual(result["refresh_token"], "old_refresh_token")
        self.assertEqual(result["some_old_field"], "old_value")

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs['data']['grant_type'], 'refresh_token')
        self.assertEqual(kwargs['data']['refresh_token'], 'old_refresh_token')
        mock_save.assert_called_once()

    @patch('requests.post')
    @patch('services.ebay_token_manager.EBayTokenManager._load_token')
    @patch('services.ebay_token_manager.EBayTokenManager._save_token')
    def test_refresh_token_client_credentials_fallback_success(self, mock_save, mock_load, mock_post):
        """Test fallback to client_credentials (application flow) if no refresh_token is found."""
        # Setup mocks
        mock_load.return_value = None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "app_token",
            "expires_in": 7200
        }
        mock_post.return_value = mock_response

        # Execute
        result = self.manager._refresh_token()

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["access_token"], "app_token")

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs['data']['grant_type'], 'client_credentials')
        mock_save.assert_called_once()

    @patch('requests.post')
    @patch('services.ebay_token_manager.EBayTokenManager._load_token')
    def test_refresh_token_api_error(self, mock_load, mock_post):
        """Test that _refresh_token returns None on non-200 API response."""
        mock_load.return_value = None

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        # Execute
        result = self.manager._refresh_token()

        # Assertions
        self.assertIsNone(result)

    @patch('requests.post')
    @patch('services.ebay_token_manager.EBayTokenManager._load_token')
    def test_refresh_token_exception(self, mock_load, mock_post):
        """Test that _refresh_token logs an error and returns None on exceptions."""
        mock_load.return_value = None
        mock_post.side_effect = Exception("Connection refused")

        with self.assertLogs(level='ERROR') as cm:
            result = self.manager._refresh_token()
            self.assertIsNone(result)
            self.assertTrue(any("Error refreshing token: Connection refused" in output for output in cm.output))

if __name__ == '__main__':
    unittest.main()
