import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock dependencies to avoid importing the whole app
sys.modules["flask"] = MagicMock()
sys.modules["werkzeug.utils"] = MagicMock()
sys.modules["shared.models"] = MagicMock()
sys.modules["services.vision_service"] = MagicMock()
sys.modules["services.conversation_orchestrator"] = MagicMock()
sys.modules["services.listing_synthesis"] = MagicMock()
sys.modules["services.ebay_integration"] = MagicMock()
sys.modules["services.valuation_database"] = MagicMock()
sys.modules["services.valuation_service"] = MagicMock()
sys.modules["services.ebay_category_service"] = MagicMock()
sys.modules["services.draft_image_manager"] = MagicMock()
sys.modules["services.category_detail_generator"] = MagicMock()

class TestSecurityOAuthRedirect(unittest.TestCase):
    def test_oauth_redirect_uri_not_using_request_args(self):
        # We verify that 'redirect_uri = request.args.get' is removed
        with open("app_enhanced.py", "r") as f:
            content = f.read()

        # Vulnerable pattern should be absent
        self.assertNotIn("redirect_uri = request.args.get('redirect_uri'", content)

        # Secure pattern should be present
        self.assertIn("redirect_uri = os.getenv('EBAY_RU_NAME', 'http://localhost:5000/api/ebay/oauth/callback')", content)

if __name__ == "__main__":
    unittest.main()
