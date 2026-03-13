import sys
from unittest.mock import MagicMock
import pytest
sys.modules['httpx'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

import os
import sqlite3
import json
from services.valuation_database import ValuationDatabase
from shared.models import ItemValuation, ItemCondition, Profitability

class TestValuationDatabaseBulk:
    def setup_method(self):
        self.db_path = 'test_bulk_valuations.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = ValuationDatabase(self.db_path)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_valuations_bulk(self):
        v1 = ItemValuation(
            item_id="1", item_name="Item 1", brand="Brand 1", estimated_value=10.0,
            estimated_age=None,
            condition_score=8, condition_notes="Good", is_complete=True,
            value_range=(5, 15), resale_score=8, recommended_platforms=[],
            key_factors=[], risks=[], listing_tips=[],
            profitability=Profitability.MEDIUM, worth_listing=True, confidence=0.9
        )
        v2 = ItemValuation(
            item_id="2", item_name="Item 2", brand="Brand 2", estimated_value=20.0,
            estimated_age=None,
            condition_score=7, condition_notes="Good", is_complete=True,
            value_range=(15, 25), resale_score=8, recommended_platforms=[],
            key_factors=[], risks=[], listing_tips=[],
            profitability=Profitability.HIGH, worth_listing=True, confidence=0.8
        )
        v3 = ItemValuation(
            item_id="3", item_name="Item 3", brand="Brand 3", estimated_value=30.0,
            estimated_age=None,
            condition_score=6, condition_notes="Fair", is_complete=True,
            value_range=(25, 35), resale_score=8, recommended_platforms=[],
            key_factors=[], risks=[], listing_tips=[],
            profitability=Profitability.LOW, worth_listing=False, confidence=0.7
        )

        ids = self.db.save_valuations("test_bulk.jpg", "hashbulk", [v1, v2, v3])

        assert len(ids) == 3

        recent = self.db.get_recent_valuations()
        assert len(recent) == 3
        names = [r["item_name"] for r in recent]
        assert "Item 1" in names
        assert "Item 2" in names
        assert "Item 3" in names

    def test_save_valuations_empty(self):
        ids = self.db.save_valuations("test_bulk.jpg", "hashbulk", [])
        assert len(ids) == 0
        assert len(self.db.get_recent_valuations()) == 0
