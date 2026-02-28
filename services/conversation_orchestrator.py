"""
AI Conversation Orchestrator
Manages progressive questioning to gather missing listing details.
"""

from typing import Dict, List, Optional, Any
from shared.models import ConversationState
import uuid
import re


class ConversationOrchestrator:
    """Orchestrates AI-driven conversation to gather listing information."""
    
    # Required fields for eBay listing
    REQUIRED_FIELDS = [
        "item_name",
        "condition",
        "price",
        "category"
    ]
    
    # Optional but valuable fields
    OPTIONAL_FIELDS = [
        "brand",
        "model",
        "dimensions",
        "weight",
        "color",
        "material",
        "is_complete",
        "has_box",
        "has_manual",
        "functional_issues",
        "visible_damage",
        "age",
        "purchase_date"
    ]
    
    def __init__(self):
        """Initialize conversation orchestrator."""
        self.sessions: Dict[str, ConversationState] = {}
    
    def start_conversation(self, item_id: str, initial_data: Dict[str, Any]) -> ConversationState:
        """
        Start a new conversation session for an item.
        
        Args:
            item_id: Unique item identifier
            initial_data: Known data from vision/valuation
        
        Returns:
            ConversationState with first question
        """
        session_id = str(uuid.uuid4())
        
        # Determine what we know and what we need
        known_fields = {k: v for k, v in initial_data.items() if v is not None}
        unknown_fields = self._determine_unknown_fields(known_fields)
        
        state = ConversationState(
            session_id=session_id,
            item_id=item_id,
            known_fields=known_fields,
            unknown_fields=unknown_fields,
            confidence=self._calculate_confidence(known_fields)
        )
        
        # Generate first question
        state.current_question = self._generate_question(state)
        state.questions_asked.append(state.current_question)
        
        self.sessions[session_id] = state
        return state
    
    def process_answer(self, session_id: str, answer: str) -> ConversationState:
        """
        Process user's answer and generate next question.
        
        Args:
            session_id: Session identifier
            answer: User's answer to current question
        
        Returns:
            Updated ConversationState
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        state = self.sessions[session_id]
        
        # Extract information from answer
        extracted = self._extract_info_from_answer(state.current_question, answer)
        state.known_fields.update(extracted)
        
        # Update unknown fields
        state.unknown_fields = self._determine_unknown_fields(state.known_fields)
        state.confidence = self._calculate_confidence(state.known_fields)
        
        # Check if we have enough information
        if self._has_sufficient_data(state):
            state.is_complete = True
            state.current_question = None
        else:
            # Generate next question
            state.current_question = self._generate_question(state)
            state.questions_asked.append(state.current_question)
        
        return state
    
    def get_state(self, session_id: str) -> Optional[ConversationState]:
        """Get current conversation state."""
        return self.sessions.get(session_id)
    
    def _determine_unknown_fields(self, known_fields: Dict[str, Any]) -> List[str]:
        """Determine which fields are still unknown."""
        all_fields = set(self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS)
        known = set(known_fields.keys())
        return sorted(list(all_fields - known))
    
    def _calculate_confidence(self, known_fields: Dict[str, Any]) -> float:
        """Calculate confidence score based on known fields."""
        required_count = sum(1 for f in self.REQUIRED_FIELDS if f in known_fields)
        optional_count = sum(1 for f in self.OPTIONAL_FIELDS if f in known_fields)
        
        required_score = required_count / len(self.REQUIRED_FIELDS)
        optional_score = optional_count / len(self.OPTIONAL_FIELDS) * 0.3  # 30% weight
        
        return min(1.0, required_score + optional_score)
    
    def _has_sufficient_data(self, state: ConversationState) -> bool:
        """Check if we have enough data to create a listing."""
        # Must have all required fields
        for field in self.REQUIRED_FIELDS:
            if field not in state.known_fields:
                return False
        
        # Should have at least 60% confidence
        return state.confidence >= 0.6
    
    def _generate_question(self, state: ConversationState) -> str:
        """Generate the next question to ask."""
        # Priority order for questions
        priority_fields = [
            "condition",
            "functional_issues",
            "visible_damage",
            "is_complete",
            "has_box",
            "dimensions",
            "weight"
        ]
        
        # Find highest priority unknown field
        for field in priority_fields:
            if field in state.unknown_fields:
                return self._create_question_for_field(field, state)
        
        # If no priority fields, ask about first unknown required field
        for field in state.unknown_fields:
            if field in self.REQUIRED_FIELDS:
                return self._create_question_for_field(field, state)
        
        # Ask about any remaining field
        if state.unknown_fields:
            return self._create_question_for_field(state.unknown_fields[0], state)
        
        return "Is there anything else you'd like to add about this item?"
    
    def _create_question_for_field(self, field: str, state: ConversationState) -> str:
        """Create a natural language question for a specific field."""
        item_name = state.known_fields.get("item_name", "this item")
        
        questions = {
            "condition": f"What condition is {item_name} in? (New, Used, For parts, etc.)",
            "functional_issues": f"Does {item_name} have any functional issues?",
            "visible_damage": f"Are there any visible scratches, dents, or damage on {item_name}?",
            "is_complete": f"Is {item_name} complete with all original parts?",
            "has_box": f"Do you have the original box or packaging for {item_name}?",
            "has_manual": f"Do you have the instruction manual for {item_name}?",
            "dimensions": f"What are the dimensions of {item_name}? (length x width x height)",
            "weight": f"What is the approximate weight of {item_name}?",
            "color": f"What color is {item_name}?",
            "material": f"What material is {item_name} made of?",
            "age": f"Approximately how old is {item_name}?",
            "price": f"What price would you like to list {item_name} for?",
            "category": f"What category does {item_name} belong to?",
        }
        
        return questions.get(field, f"Tell me about {field} for {item_name}.")
    
    def _extract_info_from_answer(self, question: str, answer: str) -> Dict[str, Any]:
        """Extract structured information from user's answer."""
        extracted = {}
        answer_lower = answer.lower()
        
        # Condition detection
        if "condition" in question.lower():
            if "new" in answer_lower:
                extracted["condition"] = "New"
            elif "used" in answer_lower:
                extracted["condition"] = "Used"
            elif "refurbished" in answer_lower:
                extracted["condition"] = "Seller refurbished"
            elif "parts" in answer_lower or "not working" in answer_lower:
                extracted["condition"] = "For parts or not working"
        
        # Boolean fields
        yes_no_fields = {
            "functional_issues": ["issue", "problem", "broken", "not work"],
            "visible_damage": ["damage", "scratch", "dent", "crack"],
            "is_complete": ["complete", "all parts"],
            "has_box": ["box", "packaging"],
            "has_manual": ["manual", "instructions"]
        }
        
        for field, keywords in yes_no_fields.items():
            if any(kw in question.lower() for kw in keywords):
                # Use regex with word boundaries to avoid matching "no" in "not" or "have" in "don't have"
                if re.search(r'\b(no|nope|don\'t|dont)\b', answer_lower):
                    extracted[field] = False
                elif re.search(r'\b(yes|yep|yeah|have|do)\b', answer_lower):
                    extracted[field] = True
        
        # Dimensions
        if "dimension" in question.lower():
            # Extract dimensions like "12x8x3" or "12 x 8 x 3"
            dim_match = re.search(r'(\d+)\s*x\s*(\d+)\s*x\s*(\d+)', answer)
            if dim_match:
                extracted["dimensions"] = f"{dim_match.group(1)} x {dim_match.group(2)} x {dim_match.group(3)}"
        
        # Weight
        if "weight" in question.lower():
            weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(lbs|lb|pounds|pound|kilograms|kilogram|kg|ounces|ounce|oz)', answer_lower)
            if weight_match:
                extracted["weight"] = f"{weight_match.group(1)} {weight_match.group(2)}"
        
        # Price
        if "price" in question.lower():
            price_match = re.search(r'\$?(\d+(?:\.\d{2})?)', answer)
            if price_match:
                extracted["price"] = float(price_match.group(1))
        
        # Dimensions (fallback/alternative)
        if "dimension" in question.lower() and "dimensions" not in extracted:
            # Try to extract numbers (simple pattern)
            numbers = re.findall(r'\d+\.?\d*', answer)
            if len(numbers) >= 2:
                extracted["dimensions"] = " x ".join(numbers[:3])
        
        return extracted
