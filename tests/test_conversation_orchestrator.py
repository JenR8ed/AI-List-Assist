import unittest
import os
import sys
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock missing dependencies before importing services
sys.modules['dotenv'] = MagicMock()
sys.modules['httpx'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

from services.conversation_orchestrator import ConversationOrchestrator
from shared.models import ConversationState

class TestConversationOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = ConversationOrchestrator()
        self.item_id = "test-item-123"
        self.initial_data = {
            "item_name": "Vintage Nikon Camera",
            "category": "Cameras"
        }

    def test_start_conversation(self):
        state = self.orchestrator.start_conversation(self.item_id, self.initial_data)

        self.assertIsInstance(state, ConversationState)
        self.assertEqual(state.item_id, self.item_id)
        self.assertEqual(state.known_fields["item_name"], "Vintage Nikon Camera")
        self.assertEqual(state.known_fields["category"], "Cameras")
        self.assertIn("condition", state.unknown_fields)
        self.assertIsNotNone(state.current_question)
        self.assertIn(state.current_question, state.questions_asked)

        # Session should be stored
        self.assertEqual(self.orchestrator.get_state(state.session_id), state)

    def test_process_answer_invalid_session(self):
        with self.assertRaises(ValueError):
            self.orchestrator.process_answer("invalid-session", "Some answer")

    def test_process_answer_condition(self):
        state = self.orchestrator.start_conversation(self.item_id, self.initial_data)
        session_id = state.session_id

        # Simulate question about condition
        state.current_question = "What condition is the camera in?"

        # Test "Used"
        state = self.orchestrator.process_answer(session_id, "It is used but in good shape")
        self.assertEqual(state.known_fields["condition"], "Used")

        # Test "New"
        state.known_fields.pop("condition")
        state.current_question = "What condition is the camera in?"
        state = self.orchestrator.process_answer(session_id, "This is brand new")
        self.assertEqual(state.known_fields["condition"], "New")

        # Test "Refurbished"
        state.known_fields.pop("condition")
        state.current_question = "What condition is the camera in?"
        state = self.orchestrator.process_answer(session_id, "It was refurbished by the seller")
        self.assertEqual(state.known_fields["condition"], "Seller refurbished")

        # Test "Parts"
        state.known_fields.pop("condition")
        state.current_question = "What condition is the camera in?"
        state = self.orchestrator.process_answer(session_id, "It's for parts, not working")
        self.assertEqual(state.known_fields["condition"], "For parts or not working")

    def test_process_answer_boolean(self):
        state = self.orchestrator.start_conversation(self.item_id, self.initial_data)
        session_id = state.session_id

        # Test functional_issues
        state.current_question = "Does it have any functional issues?"
        state = self.orchestrator.process_answer(session_id, "Yes, the shutter is stuck")
        self.assertTrue(state.known_fields["functional_issues"])

        state.current_question = "Does it have any functional issues?"
        state = self.orchestrator.process_answer(session_id, "No, it works perfectly")
        self.assertFalse(state.known_fields["functional_issues"])

        # Test has_box
        state.current_question = "Do you have the original box?"
        state = self.orchestrator.process_answer(session_id, "Yep, I have it")
        self.assertTrue(state.known_fields["has_box"])

    def test_process_answer_dimensions(self):
        state = self.orchestrator.start_conversation(self.item_id, self.initial_data)
        session_id = state.session_id

        state.current_question = "What are the dimensions?"
        state = self.orchestrator.process_answer(session_id, "It is 10 x 5 x 2 inches")
        self.assertEqual(state.known_fields["dimensions"], "10x5x2")

        # Test fallback
        state.known_fields.pop("dimensions")
        state.current_question = "What are the dimensions?"  # Reset question
        state = self.orchestrator.process_answer(session_id, "The size is 12 by 8")
        self.assertEqual(state.known_fields["dimensions"], "12 x 8")

    def test_process_answer_weight(self):
        state = self.orchestrator.start_conversation(self.item_id, self.initial_data)
        session_id = state.session_id

        state.current_question = "What is the weight?"
        state = self.orchestrator.process_answer(session_id, "It weighs about 2.5 lbs")
        self.assertEqual(state.known_fields["weight"], "2.5 lbs")

    def test_process_answer_price(self):
        state = self.orchestrator.start_conversation(self.item_id, self.initial_data)
        session_id = state.session_id

        state.current_question = "What price?"
        state = self.orchestrator.process_answer(session_id, "I want to sell it for $150.50")
        self.assertEqual(state.known_fields["price"], 150.50)

    def test_calculate_confidence(self):
        # Base confidence with 2 fields (item_name, category)
        # item_name and category are 2 of 4 required fields -> 2/4 = 0.5
        # 0 optional fields -> 0
        # total = 0.5
        state = self.orchestrator.start_conversation(self.item_id, self.initial_data)
        self.assertEqual(state.confidence, 0.5)

        # Add another required field (condition)
        # 3/4 = 0.75
        state.known_fields["condition"] = "Used"
        conf = self.orchestrator._calculate_confidence(state.known_fields)
        self.assertEqual(conf, 0.75)

        # Add all required fields
        state.known_fields["price"] = 100.0
        conf = self.orchestrator._calculate_confidence(state.known_fields)
        self.assertEqual(conf, 1.0)

        # Add an optional field
        # 1.0 + (1/13 * 0.3) = 1.023... capped at 1.0
        state.known_fields["brand"] = "Nikon"
        conf = self.orchestrator._calculate_confidence(state.known_fields)
        self.assertEqual(conf, 1.0)

    def test_full_conversation_flow(self):
        initial_data = {
            "item_name": "Test Item",
            "category": "Test Category"
        }
        state = self.orchestrator.start_conversation(self.item_id, initial_data)
        session_id = state.session_id

        # We need condition, price (required)
        # Priority: condition, functional_issues, ...

        # 1. Condition
        self.assertIn("condition", state.current_question.lower())
        state = self.orchestrator.process_answer(session_id, "It is used")

        # 2. Functional issues (next in priority)
        self.assertIn("functional issues", state.current_question.lower())
        state = self.orchestrator.process_answer(session_id, "No issues")

        # 3. Visible damage
        self.assertIn("visible", state.current_question.lower())
        state = self.orchestrator.process_answer(session_id, "None")

        # 4. Is complete
        self.assertIn("complete", state.current_question.lower())
        state = self.orchestrator.process_answer(session_id, "Yes it is")

        # 5. Has box
        self.assertIn("box", state.current_question.lower())
        state = self.orchestrator.process_answer(session_id, "No box")

        # 6. Dimensions
        self.assertIn("dimensions", state.current_question.lower())
        state = self.orchestrator.process_answer(session_id, "10x10x10")

        # 7. Weight
        self.assertIn("weight", state.current_question.lower())
        state = self.orchestrator.process_answer(session_id, "5 lbs")

        # 8. Now price (first unknown required field since no more priority fields are unknown)
        self.assertIn("price", state.current_question.lower())
        state = self.orchestrator.process_answer(session_id, "List it for $50")

        # Now we have all required fields and confidence should be high enough
        # REQUIRED_FIELDS = ["item_name", "condition", "price", "category"]
        # All 4 present -> required_score = 1.0
        # Optional fields gathered: functional_issues, visible_damage, is_complete, has_box, dimensions, weight (6 fields)
        # confidence = 1.0 + (6/13 * 0.3) = 1.138... -> 1.0

        self.assertTrue(state.is_complete)
        self.assertIsNone(state.current_question)

    def test_get_state(self):
        state = self.orchestrator.start_conversation(self.item_id, self.initial_data)
        retrieved = self.orchestrator.get_state(state.session_id)
        self.assertEqual(state, retrieved)

        self.assertIsNone(self.orchestrator.get_state("non-existent"))

if __name__ == '__main__':
    unittest.main()
