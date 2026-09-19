import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.consignment_database import calculate_commission, calculate_commission_amount, init_db, DB_PATH, create_participant, create_asset, log_transaction, update_asset_status

class TestConsignmentDatabase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        p = create_participant("Test Participant", "test@test.com")
        self.pid = p["participant_id"]

    def tearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def test_calculate_commission_asset_not_found(self):
        result = calculate_commission("non_existent_id")
        self.assertEqual(result, {"error": "Asset not found"})

    def test_calculate_commission_not_sold(self):
        a = create_asset(self.pid, 100.0)
        result = calculate_commission(a["asset_id"])
        self.assertEqual(result, {"error": "Asset is not yet SOLD"})

    def test_calculate_commission_default_multiplier(self):
        a = create_asset(self.pid, 100.0)
        update_asset_status(a["asset_id"], "SOLD", sale_price=100.0)
        # No SALE_RECORD transaction
        result = calculate_commission(a["asset_id"])

        self.assertEqual(result["commission_multiplier"], 0.15)
        self.assertEqual(result["commission_amount"], 15.0)
        self.assertEqual(result["participant_payout"], 85.0)
        self.assertEqual(result["sale_price"], 100.0)

    def test_calculate_commission_custom_multiplier(self):
        a = create_asset(self.pid, 200.0)
        update_asset_status(a["asset_id"], "SOLD", sale_price=200.0)
        log_transaction(a["asset_id"], "SALE_RECORD", commission_multiplier=0.10)

        result = calculate_commission(a["asset_id"])

        self.assertEqual(result["commission_multiplier"], 0.10)
        self.assertEqual(result["commission_amount"], 20.0)
        self.assertEqual(result["participant_payout"], 180.0)

    def test_calculate_commission_no_sale_price(self):
        a = create_asset(self.pid, 300.0)
        update_asset_status(a["asset_id"], "SOLD", sale_price=None)
        log_transaction(a["asset_id"], "SALE_RECORD", commission_multiplier=0.10)

        result = calculate_commission(a["asset_id"])

        self.assertEqual(result["sale_price"], 0.0)
        self.assertEqual(result["commission_amount"], 0.0)
        self.assertEqual(result["participant_payout"], 0.0)


    def test_calculate_commission_empty_transactions(self):
        a = create_asset(self.pid, 300.0)
        update_asset_status(a["asset_id"], "SOLD", sale_price=300.0)

        result = calculate_commission(a["asset_id"])

        self.assertEqual(result["commission_multiplier"], 0.15)
        self.assertEqual(result["commission_amount"], 45.0)
        self.assertEqual(result["participant_payout"], 255.0)
        self.assertEqual(result["sale_price"], 300.0)

    def test_calculate_commission_multiple_sale_records(self):
        import time
        a = create_asset(self.pid, 500.0)
        update_asset_status(a["asset_id"], "SOLD", sale_price=500.0)
        log_transaction(a["asset_id"], "SALE_RECORD", commission_multiplier=0.18)
        time.sleep(0.01) # Ensure different timestamp
        log_transaction(a["asset_id"], "SALE_RECORD", commission_multiplier=0.12)

        result = calculate_commission(a["asset_id"])

        self.assertEqual(result["commission_multiplier"], 0.12)
        self.assertEqual(result["commission_amount"], 60.0)
        self.assertEqual(result["participant_payout"], 440.0)

    def test_calculate_commission_amount_negative(self):
        self.assertEqual(calculate_commission_amount(-100), -15.0)

    def test_calculate_commission_amount_zero(self):
        self.assertEqual(calculate_commission_amount(0), 0.0)

    def test_calculate_commission_amount_below_1000(self):
        self.assertEqual(calculate_commission_amount(500), 75.0)

    def test_calculate_commission_amount_exactly_1000(self):
        self.assertEqual(calculate_commission_amount(1000), 150.0)

    def test_calculate_commission_amount_just_above_1000(self):
        self.assertAlmostEqual(calculate_commission_amount(1001), 120.12)

    def test_calculate_commission_amount_below_5000(self):
        self.assertEqual(calculate_commission_amount(2500), 300.0)

    def test_calculate_commission_amount_exactly_5000(self):
        self.assertEqual(calculate_commission_amount(5000), 600.0)

    def test_calculate_commission_amount_just_above_5000(self):
        self.assertAlmostEqual(calculate_commission_amount(5001), 500.1)

    def test_calculate_commission_amount_large_amount(self):
        self.assertEqual(calculate_commission_amount(10000), 1000.0)

if __name__ == '__main__':
    unittest.main()
