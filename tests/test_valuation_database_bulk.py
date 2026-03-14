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
sys.modules["httpx"] = MagicMock()
sys.modules["flask"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()

from services.valuation_database import ValuationDatabase
from shared.models import ItemValuation, Profitability

class TestValuationDatabaseBulk(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_bulk_valuations.db"
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

    def test_save_valuations_bulk(self):
        valuations = [self.valuation, self.valuation]
        val_ids = self.db.save_valuations("test.jpg", "hash123", valuations)

        self.assertEqual(len(val_ids), 2)

        recent = self.db.get_recent_valuations(limit=10)
        self.assertEqual(len(recent), 2)

        # Recent valuations are ordered by upload_timestamp DESC.
        # Since they are inserted in the same transaction, they might have the same timestamp.
        # Let's just check that both IDs are present.
        recent_ids = [r["id"] for r in recent]
        self.assertIn(val_ids[0], recent_ids)
        self.assertIn(val_ids[1], recent_ids)

    def test_save_valuations_empty(self):
        val_ids = self.db.save_valuations("test.jpg", "hash123", [])
        self.assertEqual(len(val_ids), 0)

if __name__ == '__main__':
    unittest.main()
