import unittest
import os
from io import BytesIO

# Set environment variables for testing
os.environ['SECRET_KEY'] = 'test_secret_key'
os.environ['EBAY_CLIENT_ID'] = 'test'
os.environ['EBAY_CLIENT_SECRET'] = 'test'
os.environ['GOOGLE_API_KEY'] = 'test'

from app_enhanced import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.config['TESTING'] = True

    def test_upload_invalid_extension(self):
        data = {
            'image': (BytesIO(b"<html><script>alert(1)</script></html>"), 'malicious.html')
        }
        response = self.app.post('/api/analyze', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid file type. Only images are allowed.", response.data)

    def test_upload_valid_extension_invalid_mime(self):
        data = {
            'image': (BytesIO(b"<html><script>alert(1)</script></html>"), 'malicious.jpg', 'text/html')
        }
        response = self.app.post('/api/analyze', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid file type. Only images are allowed.", response.data)

if __name__ == '__main__':
    unittest.main()
