import unittest
from unittest.mock import patch, MagicMock
import json
import sqlite3
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock services that app_enhanced.py imports to avoid dependency issues
sys.modules['services.vision_service'] = MagicMock()
sys.modules['services.conversation_orchestrator'] = MagicMock()
sys.modules['services.listing_synthesis'] = MagicMock()
sys.modules['services.valuation_database'] = MagicMock()
sys.modules['services.valuation_service'] = MagicMock()
sys.modules['services.ebay_category_service'] = MagicMock()
sys.modules['services.draft_image_manager'] = MagicMock()
sys.modules['services.category_detail_generator'] = MagicMock()

# Set required environment variables before importing app
os.environ['SECRET_KEY'] = 'test_secret'

from app_enhanced import app

class TestGetEBayListingRoute(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Setup test databases
        if os.path.exists('listings.db'):
            os.rename('listings.db', 'listings.db.bak')
        if os.path.exists('valuations.db'):
            os.rename('valuations.db', 'valuations.db.bak')

        conn = sqlite3.connect('listings.db')
        c = conn.cursor()
        c.execute('CREATE TABLE listings (listing_id TEXT, draft_data TEXT, ebay_listing_id TEXT)')
        c.execute('INSERT INTO listings (listing_id, draft_data, ebay_listing_id) VALUES (?, ?, ?)',
                  ('SKU1', json.dumps({'title': 'Draft Title', 'price': 100.0}), 'EBAY123'))
        conn.commit()
        conn.close()

        conn = sqlite3.connect('valuations.db')
        c = conn.cursor()
        c.execute('CREATE TABLE ebay_submissions (valuation_id TEXT, ebay_listing_id TEXT)')
        c.execute('CREATE TABLE valuations (id TEXT, valuation_data TEXT)')
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists('listings.db'):
            os.remove('listings.db')
        if os.path.exists('valuations.db'):
            os.remove('valuations.db')
        if os.path.exists('listings.db.bak'):
            os.rename('listings.db.bak', 'listings.db')
        if os.path.exists('valuations.db.bak'):
            os.rename('valuations.db.bak', 'valuations.db')

    @patch('app_enhanced.ebay_integration')
    def test_get_ebay_listing_success(self, mock_ebay):
        mock_ebay.get_listing_details.return_value = {
            "title": "Real eBay Title",
            "price": 150.0
        }

        response = self.app.get('/api/ebay/listing/EBAY123')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['listing']['title'], "Real eBay Title")
        self.assertFalse(data['is_cached_fallback'])
        mock_ebay.get_listing_details.assert_called_with('SKU1', force_refresh=False)

    @patch('app_enhanced.ebay_integration')
    def test_get_ebay_listing_fallback(self, mock_ebay):
        # Mock eBay API failure
        mock_ebay.get_listing_details.side_effect = Exception("API Down")

        response = self.app.get('/api/ebay/listing/EBAY123')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['listing']['title'], "Draft Title")
        self.assertTrue(data['is_cached_fallback'])

    def test_get_ebay_listing_not_found(self):
        response = self.app.get('/api/ebay/listing/NONEXISTENT')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
