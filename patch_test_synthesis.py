import re

with open('tests/test_listing_synthesis.py', 'r') as f:
    content = f.read()

old_test = """    def test_create_listing_draft_happy_path(self):
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
        self.assertEqual(draft.item_specifics["Color"], "Silver/Black")"""

new_test = """    @patch('services.gemini_rest_client.GeminiRestClient.generate_content')
    def test_create_listing_draft_happy_path(self, mock_generate_content):
        # Mock LLM response matching ListingDraft Pydantic model
        import json
        mock_response_dict = {
            "listing_id": "will_be_replaced",
            "item_id": "will_be_replaced",
            "title": "Canon AE-1 Vintage Camera",
            "description": "<h2>Vintage Camera</h2>",
            "category_id": "20081",
            "condition": "Used",
            "price": 150.0,
            "item_specifics": {"Brand": "Canon", "Model": "AE-1", "Color": "Silver/Black"},
            "shipping_details": {},
            "images": [],
            "confidence": 0.9,
            "missing_required_specifics": [],
            "ready_for_api": True
        }
        mock_generate_content.return_value = (json.dumps(mock_response_dict), {})

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
        self.assertEqual(draft.item_specifics["Color"], "Silver/Black")"""

content = content.replace("from unittest.mock import MagicMock", "from unittest.mock import MagicMock, patch")
content = content.replace(old_test, new_test)

with open('tests/test_listing_synthesis.py', 'w') as f:
    f.write(content)
