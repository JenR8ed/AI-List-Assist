import unittest
import os
import sys
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock missing dependencies before importing services
sys.modules['dotenv'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

from services.listing_synthesis import ListingSynthesisEngine
from shared.models import ListingDraft, ItemCondition, ConversationState, ItemValuation, Profitability

class TestListingSynthesis(unittest.TestCase):
    def setUp(self):
        self.engine = ListingSynthesisEngine()
        self.item_id = "test-item-123"

    def create_mock_valuation(self):
        return ItemValuation(
            item_id=self.item_id,
            item_name="Vintage Camera",
            brand="Canon",
            estimated_age="1970s",
            condition_score=8,
            condition_notes="Excellent working condition, minor brassing.",
            is_complete=True,
            estimated_value=150.0,
            value_range={"low": 120.0, "high": 180.0},
            resale_score=9,
            profitability=Profitability.HIGH,
            recommended_platforms=["eBay", "Etsy"],
            key_factors=["Classic model", "Fully functional"],
            risks=["Old optics may have internal dust"],
            listing_tips=["Include film test photos"],
            worth_listing=True,
            confidence=0.95
        )

    def create_mock_conversation_state(self):
        return ConversationState(
            session_id="session-456",
            item_id=self.item_id,
            known_fields={
                "brand": "Canon",
                "model": "AE-1",
                "condition": "Used",
                "has_box": True,
                "color": "Silver/Black",
                "material": "Metal"
            },
            confidence=0.9
        )

    def test_create_listing_draft_happy_path(self):
        valuation = self.create_mock_valuation()
        conv_state = self.create_mock_conversation_state()
        images = ["img1.jpg", "img2.jpg"]

        draft = self.engine.create_listing_draft(
            self.item_id, valuation, conv_state, images
        )

        self.assertIsInstance(draft, ListingDraft)
        self.assertEqual(draft.item_id, self.item_id)
        self.assertIn("Canon AE-1 Vintage Camera", draft.title)
        self.assertIn("<h2>Vintage Camera</h2>", draft.description)
        self.assertEqual(draft.condition, ItemCondition.USED)
        self.assertEqual(draft.price, 150.0)
        self.assertEqual(draft.images, images)
        self.assertEqual(draft.confidence, 0.9)
        self.assertEqual(draft.item_specifics["Brand"], "Canon")
        self.assertEqual(draft.item_specifics["Model"], "AE-1")
        self.assertEqual(draft.item_specifics["Color"], "Silver/Black")

    def test_generate_title(self):
        # Case 1: All fields present
        data = {
            "brand": "Sony",
            "model": "WH-1000XM4",
            "item_name": "Headphones",
            "condition": "Like New",
            "is_complete": False,
            "has_box": True
        }
        title = self.engine._generate_title(data)
        self.assertEqual(title, "Sony WH-1000XM4 Headphones Like New Incomplete w/ Box")

        # Case 2: Redundant item name
        data = {
            "brand": "Nike",
            "model": "Air Max 90",
            "item_name": "Air Max 90",
            "condition": "Used"
        }
        title = self.engine._generate_title(data)
        # Should not duplicate "Air Max 90"
        self.assertEqual(title, "Nike Air Max 90 Used")

        # Case 3: Condition "New" (should be omitted)
        data = {
            "brand": "Lego",
            "item_name": "Star Wars Set",
            "condition": "New"
        }
        title = self.engine._generate_title(data)
        self.assertEqual(title, "Lego Star Wars Set")

        # Case 4: Long title truncation
        data = {
            "brand": "Extremely Long Brand Name That Takes Up Way Too Much Space In The Title Generator",
            "model": "Model X Super Pro Ultra Max Extreme Version 2.0 With Extra Features",
            "item_name": "Gadget"
        }
        title = self.engine._generate_title(data)
        self.assertEqual(len(title), 80)
        self.assertTrue(title.startswith("Extremely Long Brand Name"))

    def test_generate_description(self):
        valuation = self.create_mock_valuation()
        data = {
            "item_name": "Vintage Camera",
            "brand": "Canon",
            "model": "AE-1",
            "condition_notes": "Data notes",
            "is_complete": False,
            "has_box": False
        }
        # Incomplete, no box
        desc = self.engine._generate_description(data, valuation)
        self.assertIn("<h2>Vintage Camera</h2>", desc)
        self.assertIn("<strong>Brand:</strong> Canon", desc)
        self.assertIn("<strong>Model:</strong> AE-1", desc)
        self.assertIn("<h3>Condition:</h3>", desc)
        self.assertIn("<p>Data notes</p>", desc)
        self.assertIn("<strong>Note:</strong> Item is incomplete or missing parts.", desc)
        self.assertNotIn("Includes original box and packaging.", desc)
        self.assertIn("<h3>Key Features:</h3>", desc)
        self.assertIn("<li>Classic model</li>", desc)
        self.assertIn("<h3>Additional Information:</h3>", desc)
        self.assertIn("<li>Include film test photos</li>", desc)
        self.assertIn("<h3>Please Note:</h3>", desc)
        self.assertIn("<li>Old optics may have internal dust</li>", desc)
        self.assertIn("Please review all photos carefully. Item sold as-is.", desc)

        # Complete with box, use valuation condition notes if data notes missing
        data2 = {
            "item_name": "Vintage Camera",
            "is_complete": True,
            "has_box": True
        }
        desc2 = self.engine._generate_description(data2, valuation)
        self.assertIn("<p>Excellent working condition, minor brassing.</p>", desc2)
        self.assertIn("<p>Includes original box and packaging.</p>", desc2)
        self.assertNotIn("<strong>Note:</strong> Item is incomplete", desc2)

    def test_determine_condition(self):
        test_cases = [
            ("New", ItemCondition.NEW),
            ("Brand New", ItemCondition.NEW),
            ("New with defects", ItemCondition.NEW_WITH_DEFECTS),
            ("New other", ItemCondition.NEW_OTHER),
            ("Manufacturer refurbished", ItemCondition.MANUFACTURER_REFURBISHED),
            ("Seller refurbished", ItemCondition.SELLER_REFURBISHED),
            ("Refurbished", ItemCondition.SELLER_REFURBISHED),
            ("For parts", ItemCondition.FOR_PARTS),
            ("Not working", ItemCondition.FOR_PARTS),
            ("Used", ItemCondition.USED),
            ("Excellent", ItemCondition.USED),
            ("", ItemCondition.USED),
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                result = self.engine._determine_condition({"condition": input_str})
                self.assertEqual(result, expected)

    def test_calculate_price(self):
        valuation = self.create_mock_valuation()
        valuation.estimated_value = 150.0
        valuation.value_range = {"low": 120.0, "high": 180.0}

        # 1. User price takes precedence
        data1 = {"price": "199.99"}
        self.assertEqual(self.engine._calculate_price(data1, valuation), 199.99)

        # 2. Estimated value if no user price
        data2 = {}
        self.assertEqual(self.engine._calculate_price(data2, valuation), 150.0)

        # 3. Value range midpoint if no estimated value
        valuation.estimated_value = None
        data3 = {}
        self.assertEqual(self.engine._calculate_price(data3, valuation), 150.0)

        # 4. Default to 0.0
        valuation.value_range = None
        self.assertEqual(self.engine._calculate_price({}, valuation), 0.0)

    def test_extract_item_specifics(self):
        data = {
            "brand": "Apple",
            "model": "iPhone 13",
            "color": "Blue",
            "material": "Glass/Aluminum",
            "dimensions": "146.7 x 71.5 x 7.7 mm",
            "weight": "174g",
            "ignored": "value"
        }
        specifics = self.engine._extract_item_specifics(data)
        self.assertEqual(specifics["Brand"], "Apple")
        self.assertEqual(specifics["Model"], "iPhone 13")
        self.assertEqual(specifics["Color"], "Blue")
        self.assertEqual(specifics["Material"], "Glass/Aluminum")
        self.assertEqual(specifics["Dimensions"], "146.7 x 71.5 x 7.7 mm")
        self.assertEqual(specifics["Weight"], "174g")
        self.assertNotIn("Ignored", specifics)
        self.assertNotIn("ignored", specifics)

if __name__ == '__main__':
    unittest.main()
