import unittest
import json
import sqlite3
import sqlite3 as real_sqlite3
import os
from unittest.mock import MagicMock, patch
from datetime import datetime
from shared.models import ListingDraft, ItemCondition, ItemValuation, Profitability, ConversationState
from services.listing_synthesis import ListingSynthesisEngine
# from app_enhanced import app, init_db

class TestListingSynthesisEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ListingSynthesisEngine()

    def test_generate_title_full_data(self):
        """Test title generation with all fields provided."""
        data = {
            "brand": "Nikon",
            "model": "D850",
            "item_name": "DSLR Camera",
            "condition": "Used",
            "is_complete": True,
            "has_box": True
        }
        title = self.engine._generate_title(data)
        self.assertEqual(title, "Nikon D850 DSLR Camera Used w/ Box")

    def test_generate_title_minimal_data(self):
        """Test title generation with minimal data."""
        data = {"item_name": "Widget"}
        title = self.engine._generate_title(data)
        self.assertEqual(title, "Widget")

    def test_generate_title_missing_item_name(self):
        """Test title generation when item_name is missing (should default to 'Item')."""
        data = {"brand": "Generic"}
        title = self.engine._generate_title(data)
        self.assertEqual(title, "Generic Item")

    def test_generate_title_item_name_deduplication(self):
        """Test that item_name is not added if already in brand or model."""
        data = {
            "brand": "Nikon Camera",
            "item_name": "Camera"
        }
        title = self.engine._generate_title(data)
        self.assertEqual(title, "Nikon Camera")

        data = {
            "model": "D850 Camera",
            "item_name": "Camera"
        }
        title = self.engine._generate_title(data)
        self.assertEqual(title, "D850 Camera")

    def test_generate_title_model_deduplication(self):
        """Test that model is not added if already in brand."""
        data = {
            "brand": "Nikon D850",
            "model": "D850"
        }
        title = self.engine._generate_title(data)
        self.assertEqual(title, "Nikon D850 Item")

    def test_generate_title_condition_new(self):
        """Test that 'New' condition is excluded from the title."""
        data = {
            "item_name": "Camera",
            "condition": "New"
        }
        title = self.engine._generate_title(data)
        self.assertEqual(title, "Camera")

    def test_generate_title_incomplete_item(self):
        """Test that 'Incomplete' is added when is_complete is False."""
        data = {
            "item_name": "Lego Set",
            "is_complete": False
        }
        title = self.engine._generate_title(data)
        self.assertEqual(title, "Lego Set Incomplete")

    def test_generate_title_truncation(self):
        """Test that title is truncated to exactly 80 characters."""
        data = {
            "brand": "A" * 40,
            "model": "B" * 40,
            "item_name": "C" * 10
        }
        title = self.engine._generate_title(data)
        self.assertEqual(len(title), 80)
        self.assertEqual(title, ("A" * 40 + " " + "B" * 40 + " " + "C" * 10)[:80])

    def test_generate_title_empty_data(self):
        """Test title generation with empty data."""
        data = {}
        title = self.engine._generate_title(data)
        self.assertEqual(title, "Item")

class TestListingReconstruction(unittest.TestCase):
    def setUp(self):
        # Setup a test database
        self.db_path = 'test_listings.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.conn = sqlite3.connect(self.db_path)
        self.init_test_db()

        app.config['TESTING'] = True
        self.client = app.test_client()

        # Patch the database connection in app_enhanced
        self.real_connect = sqlite3.connect
        self.sqlite_patcher = patch('sqlite3.connect')
        self.mock_connect = self.sqlite_patcher.start()
        self.mock_connect.side_effect = lambda path: self.real_connect(self.db_path)

    def tearDown(self):
        self.sqlite_patcher.stop()
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def init_test_db(self):
        c = self.conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            listing_id TEXT PRIMARY KEY,
            item_id TEXT,
            title TEXT,
            price REAL,
            status TEXT,
            ebay_listing_id TEXT,
            draft_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            session_data TEXT
        )
        ''')
        self.conn.commit()

    @patch('services.conversation_orchestrator.ConversationOrchestrator.get_state')
    @patch('services.listing_synthesis.ListingSynthesisEngine.create_listing_draft')
    @patch('services.draft_image_manager.DraftImageManager.save_draft_images')
    def test_create_and_reconstruct_listing(self, mock_save_images, mock_create_draft, mock_get_state):
        # 1. Mock create_listing data
        item_id = "test_item"
        session_id = "test_session"
        listing_id = "test_listing_id"

        # Mock conversation state
        mock_state = ConversationState(session_id=session_id, item_id=item_id)
        mock_state.known_fields = {"item_name": "Test Item", "price": 100.0}
        mock_get_state.return_value = mock_state

        # Mock listing draft
        draft = ListingDraft(
            listing_id=listing_id,
            item_id=item_id,
            title="Test Title",
            description="Test Description",
            category_id="123",
            condition=ItemCondition.USED,
            price=100.0,
            created_at=datetime.now()
        )
        mock_create_draft.return_value = draft
        mock_save_images.return_value = []

        # 2. Call create_listing API
        response = self.client.post('/api/listing/create', json={
            "item_id": item_id,
            "session_id": session_id
        })
        if response.status_code != 200:
            print(f"Create Listing Error: {response.get_data(as_text=True)}")
        self.assertEqual(response.status_code, 200)

        # 3. Verify it's in the DB with draft_data
        c = self.conn.cursor()
        c.execute('SELECT draft_data FROM listings WHERE listing_id = ?', (listing_id,))
        row = c.fetchone()
        self.assertIsNotNone(row)
        self.assertIsNotNone(row[0])
        saved_draft = json.loads(row[0])
        self.assertEqual(saved_draft['title'], "Test Title")
        self.assertEqual(saved_draft['condition'], ItemCondition.USED.value)

        # 4. Mock eBay publish and call it
        with patch('services.ebay_integration.eBayIntegration.create_listing') as mock_ebay_publish:
            mock_ebay_publish.return_value = {
                "listing_id": "ebay_12345",
                "status": "published",
                "url": "http://ebay.com/12345"
            }

            with patch('services.ebay_token_manager.EBayTokenManager.get_valid_token') as mock_get_token:
                mock_get_token.return_value = "valid_token"

                response = self.client.post('/api/listing/publish', json={
                    "listing_id": listing_id
                })

                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertEqual(data['ebay_listing_id'], "ebay_12345")

                # 5. Verify the draft was reconstructed correctly
                # We check this by seeing if create_listing was called with a ListingDraft object
                args, kwargs = mock_ebay_publish.call_args
                reconstructed_draft = args[0]
                self.assertIsInstance(reconstructed_draft, ListingDraft)
                self.assertEqual(reconstructed_draft.title, "Test Title")
                self.assertEqual(reconstructed_draft.condition, ItemCondition.USED)
                self.assertEqual(reconstructed_draft.price, 100.0)

if __name__ == '__main__':
    unittest.main()
