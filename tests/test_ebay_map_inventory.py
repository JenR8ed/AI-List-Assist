import unittest
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ebay_integration import eBayIntegration
from shared.models import ListingDraft, ItemCondition
from datetime import datetime

class TestEBayMapInventory(unittest.TestCase):
    def setUp(self):
        self.app_id = "test_app_id"
        self.cert_id = "test_cert_id"
        os.environ['EBAY_CLIENT_ID'] = self.app_id
        os.environ['EBAY_CLIENT_SECRET'] = self.cert_id
        self.ebay = eBayIntegration(use_sandbox=True)

    def test_map_to_ebay_inventory_happy_path(self):
        """Test mapping a fully populated ListingDraft to eBay Inventory format."""
        draft = ListingDraft(
            listing_id="test-sku-123",
            item_id="item-456",
            title="Vintage Camera",
            description="A classic vintage camera.",
            category_id="12345",
            condition=ItemCondition.USED,
            price=99.99,
            item_specifics={"Brand": "Canon", "Model": "AE-1"},
            images=["http://example.com/image1.jpg", "http://example.com/image2.jpg"]
        )

        result = self.ebay._map_to_ebay_inventory(draft)

        self.assertEqual(result["sku"], "test-sku-123")
        self.assertEqual(result["product"]["title"], "Vintage Camera")
        self.assertEqual(result["product"]["description"], "A classic vintage camera.")
        self.assertEqual(result["product"]["aspects"], {"Brand": "Canon", "Model": "AE-1"})
        self.assertEqual(result["product"]["imageUrls"], ["http://example.com/image1.jpg", "http://example.com/image2.jpg"])
        self.assertEqual(result["condition"], "Used")
        self.assertEqual(result["availability"]["shipToLocationAvailability"]["quantity"], 1)

    def test_map_to_ebay_inventory_missing_brand(self):
        """Test mapping when item_specifics is missing Brand, it should NOT default to 'Unbranded' based on current code in `ebay_integration.py`."""
        draft = ListingDraft(
            listing_id="test-sku-456",
            item_id="item-789",
            title="Generic Item",
            description="Just an item.",
            category_id="54321",
            condition=ItemCondition.NEW,
            price=19.99,
            item_specifics={"Color": "Blue"},
            images=["http://example.com/image.jpg"]
        )

        result = self.ebay._map_to_ebay_inventory(draft)

        self.assertEqual(result["sku"], "test-sku-456")
        self.assertEqual(result["product"]["title"], "Generic Item")
        # Ensure 'Brand' is not magically added if it's not in the draft specifics
        self.assertNotIn("Brand", result["product"]["aspects"])
        self.assertEqual(result["product"]["aspects"], {"Color": "Blue"})
        self.assertEqual(result["condition"], "New")

    def test_map_to_ebay_inventory_empty_specifics_and_images(self):
        """Test mapping with empty item specifics and images."""
        draft = ListingDraft(
            listing_id="test-sku-789",
            item_id="item-101",
            title="Minimal Item",
            description="Minimal desc.",
            category_id="9999",
            condition=ItemCondition.NEW_OTHER,
            price=5.00,
            item_specifics={},
            images=[]
        )

        result = self.ebay._map_to_ebay_inventory(draft)

        self.assertEqual(result["sku"], "test-sku-789")
        self.assertEqual(result["product"]["title"], "Minimal Item")
        self.assertEqual(result["product"]["aspects"], {})
        self.assertEqual(result["product"]["imageUrls"], [])
        self.assertEqual(result["condition"], "New other (see details)")


if __name__ == '__main__':
    unittest.main()
