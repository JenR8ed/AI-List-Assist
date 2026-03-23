import unittest
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services import consignment_database

class TestConsignmentDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_consignment.db"
        consignment_database.DB_PATH = self.db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        consignment_database.init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_create_participant_success(self):
        participant = consignment_database.create_participant(
            display_name="Test User",
            email="test@example.com",
            tax_nexus_code="US-CA",
            payout_method_type="BANK_TRANSFER"
        )

        self.assertIsNotNone(participant)
        self.assertEqual(participant["display_name"], "Test User")
        self.assertEqual(participant["email"], "test@example.com")
        self.assertEqual(participant["tax_nexus_code"], "US-CA")
        self.assertEqual(participant["payout_method_type"], "BANK_TRANSFER")
        self.assertEqual(participant["kyc_status"], "PENDING")
        self.assertTrue(participant["participant_id"].startswith("P-"))
        self.assertIsNotNone(participant["created_at"])

    def test_create_participant_defaults(self):
        participant = consignment_database.create_participant(
            display_name="Test User Default",
            email="default@example.com"
        )

        self.assertIsNotNone(participant)
        self.assertEqual(participant["display_name"], "Test User Default")
        self.assertEqual(participant["email"], "default@example.com")
        self.assertIsNone(participant["tax_nexus_code"])
        self.assertIsNone(participant["payout_method_type"])
        self.assertEqual(participant["kyc_status"], "PENDING")
        self.assertTrue(participant["participant_id"].startswith("P-"))
        self.assertIsNotNone(participant["created_at"])

if __name__ == '__main__':
    unittest.main()
