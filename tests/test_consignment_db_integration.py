import unittest
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Mock missing dependencies
sys.modules['httpx'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['pydantic'] = MagicMock()

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import services.consignment_database as consignment_db

class TestConsignmentDBIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for the database
        self.db_fd, self.db_path = tempfile.mkstemp()
        # Patch the DB_PATH in the module
        self.patcher = patch('services.consignment_database.DB_PATH', self.db_path)
        self.patcher.start()
        # Initialize the database
        consignment_db.init_db()

    def tearDown(self):
        self.patcher.stop()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_db_initialization(self):
        # Verify that tables are created
        with consignment_db._get_conn() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in cursor.fetchall()]
            self.assertIn('participants', tables)
            self.assertIn('assets', tables)
            self.assertIn('transactions', tables)
            self.assertIn('documents', tables)

    def test_calculate_commission_workflow(self):
        # 1. Create a participant
        participant = consignment_db.create_participant(
            display_name="Test User",
            email="test@example.com"
        )
        participant_id = participant['participant_id']

        # 2. Create an asset
        asset = consignment_db.create_asset(
            participant_id=participant_id,
            basis_value=50.0,
            condition_state="GOOD"
        )
        asset_id = asset['asset_id']

        # 3. Update asset status to SOLD and set sale price
        consignment_db.update_asset_status(
            asset_id=asset_id,
            new_status="SOLD",
            sale_price=150.0
        )

        # 4. Log a sale transaction with custom multiplier
        consignment_db.log_transaction(
            asset_id=asset_id,
            call_type="SALE_RECORD",
            commission_multiplier=0.12
        )

        # 5. Calculate commission
        result = consignment_db.calculate_commission(asset_id)

        # Expected values:
        # sale_price = 150.0
        # multiplier = 0.12
        # commission = 150.0 * 0.12 = 18.0
        # payout = 150.0 - 18.0 = 132.0
        self.assertEqual(result['asset_id'], asset_id)
        self.assertEqual(result['sale_price'], 150.0)
        self.assertEqual(result['commission_multiplier'], 0.12)
        self.assertEqual(result['commission_amount'], 18.0)
        self.assertEqual(result['participant_payout'], 132.0)

    def test_calculate_commission_default_multiplier_integration(self):
        # 1. Create participant and asset
        participant = consignment_db.create_participant("User2", "u2@ex.com")
        asset = consignment_db.create_asset(participant['participant_id'], 10.0)
        asset_id = asset['asset_id']

        # 2. Mark as SOLD without logging a SALE_RECORD transaction
        consignment_db.update_asset_status(asset_id, "SOLD", sale_price=100.0)

        # 3. Calculate commission (should use default 0.15)
        result = consignment_db.calculate_commission(asset_id)
        self.assertEqual(result['commission_multiplier'], 0.15)
        self.assertEqual(result['commission_amount'], 15.0)

if __name__ == '__main__':
    unittest.main()
