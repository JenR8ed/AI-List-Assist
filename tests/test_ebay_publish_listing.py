import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock dependencies that cause import errors
sys.modules['dotenv'] = MagicMock()
sys.modules['shared.models'] = MagicMock()
sys.modules['services.ebay_token_manager'] = MagicMock()

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration

class TestEBayPublishListing(unittest.TestCase):
    def setUp(self):
        self.ebay = eBayIntegration(app_id="test_app", cert_id="test_cert", use_sandbox=True)
        self.ebay.access_token = "test_token"

    @patch('requests.post')
    def test_publish_listing_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"listingId": "ebay123", "status": "published"}
        mock_post.return_value = mock_response

        result = self.ebay._publish_listing("offer123")

        self.assertEqual(result["listingId"], "ebay123")
        self.assertEqual(result["status"], "published")
        self.assertIn("/sell/inventory/v1/offer/offer123/publish", mock_post.call_args[0][0])

    @patch('requests.post')
    @patch('services.ebay_integration.eBayIntegration._get_offer')
    def test_publish_listing_conflict_recovery(self, mock_get_offer, mock_post):
        # Mock 409 Conflict
        mock_response_409 = MagicMock()
        mock_response_409.status_code = 409
        mock_post.return_value = mock_response_409

        # Mock recovery via _get_offer
        mock_get_offer.return_value = {"listingId": "ebay456", "status": "PUBLISHED"}

        result = self.ebay._publish_listing("offer456")

        self.assertEqual(result["listingId"], "ebay456")
        self.assertEqual(result["status"], "published")
        mock_get_offer.assert_called_once_with("offer456")

    @patch('requests.post')
    def test_publish_listing_bad_request(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "errors": [
                {"message": "Missing field", "parameter": "brand"}
            ]
        }
        mock_post.return_value = mock_response

        result = self.ebay._publish_listing("offer789")

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_code"], 400)
        self.assertIn("brand", result["missing_fields"])

if __name__ == '__main__':
    unittest.main()
