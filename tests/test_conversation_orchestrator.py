import sys
from unittest.mock import MagicMock

# Mock required dependencies to test isolated logic


import unittest
from services.conversation_orchestrator import ConversationOrchestrator

class TestConversationOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = ConversationOrchestrator()

    def test_extract_info_condition(self):
        tests = [
            ("condition", "it is brand new", "New"),
            ("condition", "used condition", "Used"),
            ("condition", "it's refurbished", "Seller refurbished"),
            ("condition", "for parts only", "For parts or not working"),
            ("What is the condition?", "It is new", "New"),
            ("condition", "good", None), # Edge case: condition keyword not present
        ]

        for question, answer, expected in tests:
            with self.subTest(question=question, answer=answer):
                result = self.orchestrator._extract_info_from_answer(question, answer)
                self.assertEqual(result.get("condition"), expected)

    def test_extract_info_boolean_fields(self):
        tests = [
            ("functional_issues", "Does it have any issues?", "Yes it is broken", True),
            ("functional_issues", "Does it have any issues?", "No it works perfectly", False),
            ("visible_damage", "Any visible damage?", "Yeah there is a scratch", True),
            ("visible_damage", "Any visible damage?", "Nope, looks great", False),
            ("is_complete", "Is it complete?", "Yes all parts are there", True),
            ("is_complete", "Is it complete?", "No, missing the manual", False),
            ("has_box", "Does it have the box?", "yes", True),
            ("has_box", "Does it have the box?", "no box", False),
            ("has_manual", "Is there a manual?", "yep I have it", True),
            ("has_manual", "Is there a manual?", "don't have it", False), # Testing 'don't' negative match priority
            # Edge case
            ("visible_damage", "Any visible damage?", "I am not sure", None) # Testing 'no' boundary vs 'not'
        ]

        for field, question, answer, expected in tests:
            with self.subTest(field=field, question=question, answer=answer):
                result = self.orchestrator._extract_info_from_answer(question, answer)
                self.assertEqual(result.get(field), expected)

    def test_extract_info_dimensions(self):
        tests = [
            ("What are the dimensions?", "It is 12x8x3 inches", "12 x 8 x 3"),
            ("What are the dimensions?", "12 x 8 x 3", "12 x 8 x 3"),
            ("What are the dimensions?", "10x5x2", "10 x 5 x 2"),
            ("What are the dimensions?", "About 10 x 5 x 2.", "10 x 5 x 2"),
            # Fallback pattern
            ("What are the dimensions?", "It's 12 inches by 8 by 3", "12 x 8 x 3"),
            # Edge cases
            ("What are the dimensions?", "I don't know", None),
            ("What are the dimensions?", "10 and 2", "10 x 2"), # Not enough numbers for fallback
        ]
        for question, answer, expected in tests:
            with self.subTest(question=question, answer=answer):
                result = self.orchestrator._extract_info_from_answer(question, answer)
                self.assertEqual(result.get("dimensions"), expected)

    def test_extract_info_weight(self):
        tests = [
            ("What is the weight?", "It is 5 lbs", "5 lbs"),
            ("What is the weight?", "5.5 pounds", "5.5 pounds"),
            ("What is the weight?", "about 2 kg", "2 kg"),
            ("What is the weight?", "10 oz", "10 oz"),
            # Edge cases
            ("What is the weight?", "I'm not sure", None),
            ("What is the weight?", "5", None), # Missing unit
        ]
        for question, answer, expected in tests:
            with self.subTest(question=question, answer=answer):
                result = self.orchestrator._extract_info_from_answer(question, answer)
                self.assertEqual(result.get("weight"), expected)

    def test_extract_info_price(self):
        tests = [
            ("What price?", "I want $50", 50.0),
            ("What price?", "$50.50", 50.50),
            ("What price?", "50", 50.0),
            ("What price?", "around 100", 100.0),
            # Edge cases
            ("What price?", "I don't know", None),
            ("What price?", "fifty dollars", None), # Doesn't parse words
        ]
        for question, answer, expected in tests:
            with self.subTest(question=question, answer=answer):
                result = self.orchestrator._extract_info_from_answer(question, answer)
                self.assertEqual(result.get("price"), expected)


    def test_process_answer_happy_path(self):
        # Setup initial state
        initial_data = {"item_name": "Test Item"}
        state = self.orchestrator.start_conversation("item-1", initial_data)
        session_id = state.session_id

        # We know "item_name" so "condition" should be the next required field in unknown_fields
        self.assertIn("condition", state.unknown_fields)
        self.assertNotIn("condition", state.known_fields)

        # Override current question to ensure predictable testing
        state.current_question = "What condition is it in?"

        # Process the answer
        new_state = self.orchestrator.process_answer(session_id, "It is brand new")

        # Verify state updated correctly
        self.assertEqual(new_state.known_fields.get("condition"), "New")
        self.assertNotIn("condition", new_state.unknown_fields)
        self.assertFalse(new_state.is_complete)
        self.assertIsNotNone(new_state.current_question)

    def test_process_answer_completion(self):
        # Setup initial state with almost everything known
        initial_data = {
            "item_name": "Test Item",
            "condition": "New",
            "price": 100.0,
            # Missing "category"
        }
        state = self.orchestrator.start_conversation("item-1", initial_data)
        session_id = state.session_id

        # Provide optional fields to ensure confidence >= 0.6
        state.known_fields.update({
            "brand": "Nike", "model": "Air", "color": "Red",
            "material": "Leather", "is_complete": True
        })

        state.current_question = "What category does it belong to?"

        # Process the final required answer
        # Note: _extract_info_from_answer doesn't currently extract "category"
        # but to trigger completion, it just needs to be in known_fields
        # Wait, process_answer only updates based on what _extract_info_from_answer returns.
        # Since _extract_info_from_answer does not have logic for "category", it won't add it.
        # Let's mock _extract_info_from_answer to return the category for this test.
        original_extract = self.orchestrator._extract_info_from_answer
        self.orchestrator._extract_info_from_answer = lambda q, a: {"category": "Shoes"}

        new_state = self.orchestrator.process_answer(session_id, "Shoes")

        # Restore original
        self.orchestrator._extract_info_from_answer = original_extract

        # Verify state is complete
        self.assertTrue(new_state.is_complete)
        self.assertIsNone(new_state.current_question)

    def test_process_answer_invalid_session(self):
        with self.assertRaises(ValueError) as context:
            self.orchestrator.process_answer("invalid-session-id", "Some answer")

        self.assertIn("not found", str(context.exception))

if __name__ == '__main__':
    unittest.main()
