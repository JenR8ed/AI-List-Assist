import unittest
import os
import sys
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock dependencies
sys.modules["requests"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.vision"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

from services.valuation_database import ValuationDatabase
from shared.models import ItemValuation, Profitability

class TestValuationDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_valuations.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = ValuationDatabase(self.db_path)

        self.valuation = ItemValuation(
            item_id="test-id",
            item_name="Test Item",
            brand="Test Brand",
            estimated_age="2 years",
            condition_score=8,
            condition_notes="Good condition",
            is_complete=True,
            estimated_value=100.0,
            value_range={"low": 80, "high": 120},
            resale_score=8,
            profitability=Profitability.HIGH,
            recommended_platforms=["eBay"],
            key_factors=["Factor 1"],
            risks=["Risk 1"],
            listing_tips=["Tip 1"],
            worth_listing=True,
            confidence=0.9
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_get_valuation(self):
        val_id = self.db.save_valuation("test.jpg", "hash123", self.valuation)
        self.assertIsNotNone(val_id)

        recent = self.db.get_recent_valuations(limit=1)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["id"], val_id)
        self.assertEqual(recent[0]["item_name"], "Test Item")

    def test_approve_valuation(self):
        val_id = self.db.save_valuation("test.jpg", "hash123", self.valuation)
        success = self.db.approve_valuation(val_id)
        self.assertTrue(success)

        approved = self.db.get_approved_valuations()
        self.assertEqual(len(approved), 1)
        self.assertEqual(approved[0]["id"], val_id)
        self.assertEqual(approved[0]["status"], "approved")

    def test_submit_to_ebay(self):
        val_id = self.db.save_valuation("test.jpg", "hash123", self.valuation)
        sub_id = self.db.submit_to_ebay(
            val_id, "ebay123", "Title", 99.9, {"resp": "ok"}
        )
        self.assertIsNotNone(sub_id)

        submissions = self.db.get_ebay_submissions()
        self.assertEqual(len(submissions), 1)
        self.assertEqual(submissions[0]["ebay_listing_id"], "ebay123")

    def test_get_stats(self):
        self.db.save_valuation("test1.jpg", "hash1", self.valuation)
        self.db.save_valuation("test2.jpg", "hash2", self.valuation)

        stats = self.db.get_valuation_stats()
        self.assertEqual(stats["total_valuations"], 2)
        self.assertEqual(stats["worth_listing"], 2)

if __name__ == '__main__':
    unittest.main()
