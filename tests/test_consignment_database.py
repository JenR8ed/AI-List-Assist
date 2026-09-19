import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Mock missing dependencies

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.consignment_database import calculate_commission

class TestConsignmentDatabase(unittest.TestCase):

    @patch('services.consignment_database.get_asset')
    def test_calculate_commission_asset_not_found(self, mock_get_asset):
        mock_get_asset.return_value = None
        result = calculate_commission("non_existent_id")
        self.assertEqual(result, {"error": "Asset not found"})
        mock_get_asset.assert_called_once_with("non_existent_id")

    @patch('services.consignment_database.get_asset')
    def test_calculate_commission_not_sold(self, mock_get_asset):
        mock_get_asset.return_value = {"current_status": "LISTED"}
        result = calculate_commission("asset_id_1")
        self.assertEqual(result, {"error": "Asset is not yet SOLD"})

    @patch('services.consignment_database.list_transactions')
    @patch('services.consignment_database.get_asset')
    def test_calculate_commission_default_multiplier(self, mock_get_asset, mock_list_transactions):
        mock_get_asset.return_value = {
            "current_status": "SOLD",
            "sale_price": 100.0
        }
        mock_list_transactions.return_value = [
            {"call_type": "LISTING_SUBMISSION", "commission_multiplier": 0.20} # not a sale record
        ]

        result = calculate_commission("asset_id_2")

        # Expected: 100.0 * 0.15 (default) = 15.0
        self.assertEqual(result["commission_multiplier"], 0.15)
        self.assertEqual(result["commission_amount"], 15.0)
        self.assertEqual(result["participant_payout"], 85.0)
        self.assertEqual(result["sale_price"], 100.0)

    @patch('services.consignment_database.list_transactions')
    @patch('services.consignment_database.get_asset')
    def test_calculate_commission_custom_multiplier(self, mock_get_asset, mock_list_transactions):
        mock_get_asset.return_value = {
            "current_status": "SOLD",
            "sale_price": 200.0
        }
        mock_list_transactions.return_value = [
            {"call_type": "SALE_RECORD", "commission_multiplier": 0.10},
            {"call_type": "LISTING_SUBMISSION", "commission_multiplier": 0.15}
        ]

        result = calculate_commission("asset_id_3")

        # Expected: 200.0 * 0.10 = 20.0
        self.assertEqual(result["commission_multiplier"], 0.10)
        self.assertEqual(result["commission_amount"], 20.0)
        self.assertEqual(result["participant_payout"], 180.0)

    @patch('services.consignment_database.list_transactions')
    @patch('services.consignment_database.get_asset')
    def test_calculate_commission_no_sale_price(self, mock_get_asset, mock_list_transactions):
        mock_get_asset.return_value = {
            "current_status": "SOLD",
            "sale_price": None
        }
        mock_list_transactions.return_value = [
            {"call_type": "SALE_RECORD", "commission_multiplier": 0.10}
        ]

        result = calculate_commission("asset_id_4")

        # Expected: 0.0 * 0.10 = 0.0
        self.assertEqual(result["sale_price"], 0.0)
        self.assertEqual(result["commission_amount"], 0.0)
        self.assertEqual(result["participant_payout"], 0.0)


    @patch('services.consignment_database.list_transactions')
    @patch('services.consignment_database.get_asset')
    def test_calculate_commission_empty_transactions(self, mock_get_asset, mock_list_transactions):
        mock_get_asset.return_value = {
            "current_status": "SOLD",
            "sale_price": 300.0
        }
        mock_list_transactions.return_value = []

        result = calculate_commission("asset_id_5")

        # Expected: 300.0 * 0.15 (default fallback) = 45.0
        self.assertEqual(result["commission_multiplier"], 0.15)
        self.assertEqual(result["commission_amount"], 45.0)
        self.assertEqual(result["participant_payout"], 255.0)
        self.assertEqual(result["sale_price"], 300.0)

    @patch('services.consignment_database.list_transactions')
    @patch('services.consignment_database.get_asset')
    def test_calculate_commission_multiple_sale_records(self, mock_get_asset, mock_list_transactions):
        mock_get_asset.return_value = {
            "current_status": "SOLD",
            "sale_price": 500.0
        }
        mock_list_transactions.return_value = [
            {"call_type": "SALE_RECORD", "commission_multiplier": 0.12}, # Most recent
            {"call_type": "SALE_RECORD", "commission_multiplier": 0.18}  # Older
        ]

        result = calculate_commission("asset_id_6")

        # Expected: 500.0 * 0.12 = 60.0
        self.assertEqual(result["commission_multiplier"], 0.12)
        self.assertEqual(result["commission_amount"], 60.0)
        self.assertEqual(result["participant_payout"], 440.0)

    def test_calculate_commission_amount_negative(self):
        # We need to import the new function first
        from services.consignment_database import calculate_commission_amount
        self.assertEqual(calculate_commission_amount(-100), -15.0)

    def test_calculate_commission_amount_zero(self):
        from services.consignment_database import calculate_commission_amount
        self.assertEqual(calculate_commission_amount(0), 0.0)

    def test_calculate_commission_amount_below_1000(self):
        from services.consignment_database import calculate_commission_amount
        self.assertEqual(calculate_commission_amount(500), 75.0)

    def test_calculate_commission_amount_exactly_1000(self):
        from services.consignment_database import calculate_commission_amount
        self.assertEqual(calculate_commission_amount(1000), 150.0)

    def test_calculate_commission_amount_just_above_1000(self):
        from services.consignment_database import calculate_commission_amount
        self.assertAlmostEqual(calculate_commission_amount(1001), 120.12)

    def test_calculate_commission_amount_below_5000(self):
        from services.consignment_database import calculate_commission_amount
        self.assertEqual(calculate_commission_amount(2500), 300.0)

    def test_calculate_commission_amount_exactly_5000(self):
        from services.consignment_database import calculate_commission_amount
        self.assertEqual(calculate_commission_amount(5000), 600.0)

    def test_calculate_commission_amount_just_above_5000(self):
        from services.consignment_database import calculate_commission_amount
        self.assertAlmostEqual(calculate_commission_amount(5001), 500.1)

    def test_calculate_commission_amount_large_amount(self):
        from services.consignment_database import calculate_commission_amount
        self.assertEqual(calculate_commission_amount(10000), 1000.0)

if __name__ == '__main__':
    unittest.main()
