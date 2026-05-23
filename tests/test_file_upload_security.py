import sys
import os
import unittest
from io import BytesIO
import types
from unittest.mock import patch, MagicMock

# Fix imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock external dependencies
sys.modules['httpx'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['requests'] = MagicMock()

# Create a mock for flask
mock_flask = types.ModuleType("flask")
class MockFlask:
    def __init__(self, *args, **kwargs):
        self.config = {}

    def route(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator

    def after_request(self, f):
        return f

mock_flask.Flask = MockFlask
mock_flask.render_template = MagicMock()
mock_flask.request = MagicMock()
mock_flask.jsonify = MagicMock(side_effect=lambda x: str(x).encode())
sys.modules["flask"] = mock_flask

# Create a mock for werkzeug.utils
mock_werkzeug = types.ModuleType("werkzeug")
mock_werkzeug.utils = types.ModuleType("werkzeug.utils")
mock_werkzeug.utils.secure_filename = lambda x: x
sys.modules["werkzeug.utils"] = mock_werkzeug.utils

# Set environment variable to bypass the secret key check
os.environ['SECRET_KEY'] = 'test'

class TestFileUploadSecurity(unittest.TestCase):
    @patch('services.vision_service.VisionService')
    @patch('services.valuation_service.ValuationService')
    @patch('services.conversation_orchestrator.ConversationOrchestrator')
    @patch('services.listing_synthesis.ListingSynthesisEngine')
    @patch('services.category_detail_generator.CategoryDetailGenerator')
    @patch('services.ebay_integration.eBayIntegration')
    def test_allowed_file(self, *mocks):
        from app_enhanced import allowed_file

        # Test valid extensions
        self.assertTrue(allowed_file('image.png'))
        self.assertTrue(allowed_file('photo.jpg'))
        self.assertTrue(allowed_file('picture.jpeg'))
        self.assertTrue(allowed_file('animation.gif'))
        self.assertTrue(allowed_file('web.webp'))

        # Test valid extensions with uppercase
        self.assertTrue(allowed_file('image.PNG'))
        self.assertTrue(allowed_file('photo.JPG'))

        # Test invalid extensions
        self.assertFalse(allowed_file('script.py'))
        self.assertFalse(allowed_file('shell.sh'))
        self.assertFalse(allowed_file('page.html'))
        self.assertFalse(allowed_file('document.pdf'))
        self.assertFalse(allowed_file('executable.exe'))

        # Test multiple dots (double extensions)
        self.assertFalse(allowed_file('image.png.php'))
        self.assertTrue(allowed_file('test.file.png'))

        # Test no extension
        self.assertFalse(allowed_file('image'))

if __name__ == '__main__':
    unittest.main()
