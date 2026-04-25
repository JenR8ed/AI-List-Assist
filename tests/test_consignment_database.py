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

if __name__ == '__main__':
    unittest.main()
