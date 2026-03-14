import time
import os
import sys
import json
import uuid
from typing import List

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from unittest.mock import MagicMock
# Mock dependencies to avoid import errors from services/__init__.py
sys.modules["flask"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["httpx"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.vision"] = MagicMock()
sys.modules["requests"] = MagicMock()

# Mock the services that are imported in services/__init__.py but we don't need
sys.modules["services.vision_service"] = MagicMock()
sys.modules["services.mock_valuation_service"] = MagicMock()
sys.modules["services.conversation_orchestrator"] = MagicMock()
sys.modules["services.listing_synthesis"] = MagicMock()
sys.modules["services.ebay_integration"] = MagicMock()
sys.modules["services.category_detail_generator"] = MagicMock()
sys.modules["services.ebay_token_manager"] = MagicMock()

# Now we can import ValuationDatabase safely
from services.valuation_database import ValuationDatabase
from shared.models import ItemValuation, Profitability

def create_mock_valuation(i: int) -> ItemValuation:
    return ItemValuation(
        item_id=f"test-id-{i}",
        item_name=f"Test Item {i}",
        brand="Test Brand",
        estimated_age="2 years",
        condition_score=8,
        condition_notes="Good condition",
        is_complete=True,
        estimated_value=100.0 + i,
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

def benchmark_individual(db: ValuationDatabase, valuations: List[ItemValuation]):
    start_time = time.time()
    for v in valuations:
        db.save_valuation("test.jpg", "hash123", v)
    end_time = time.time()
    return end_time - start_time

def benchmark_bulk(db: ValuationDatabase, valuations: List[ItemValuation]):
    # This will be implemented after adding the method to the class
    if not hasattr(db, 'save_valuations'):
        return None
    start_time = time.time()
    db.save_valuations("test.jpg", "hash123", valuations)
    end_time = time.time()
    return end_time - start_time

if __name__ == "__main__":
    db_path = "benchmark_valuations.db"
    num_items = 100

    # Setup
    if os.path.exists(db_path):
        os.remove(db_path)

    db = ValuationDatabase(db_path)
    valuations = [create_mock_valuation(i) for i in range(num_items)]

    print(f"Benchmarking with {num_items} items...")

    # Individual inserts
    indiv_time = benchmark_individual(db, valuations)
    print(f"Individual inserts: {indiv_time:.4f}s")

    # We will run bulk after we implement it
    bulk_time = benchmark_bulk(db, valuations)
    if bulk_time:
        print(f"Bulk inserts: {bulk_time:.4f}s")
        print(f"Improvement: {(indiv_time - bulk_time) / indiv_time * 100:.2f}%")
    else:
        print("Bulk insert method not yet implemented.")

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
