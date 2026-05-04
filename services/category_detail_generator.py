"""
AI Category-Specific Detail Generator
"""

from typing import Dict, List, Any
from services.ebay_category_service import EBayCategoryService
from services.gemini_rest_client import GeminiRestClient
import os

class CategoryDetailGenerator:
    # Class constants for keyword matching to avoid list recreation on every call
    ELECTRONICS_KEYWORDS = ('phone', 'headphone', 'electronic', 'computer', 'laptop')
    CLOTHING_KEYWORDS = ('shirt', 'pants', 'clothing', 'jacket')
    VINTAGE_KEYWORDS = ('vintage', 'collectible', 'antique')
    AUTO_KEYWORDS = ('car', 'auto', 'vehicle', 'engine')

    def __init__(self):
        self.CATEGORY_MAPPING = [
            (self.ELECTRONICS_KEYWORDS, "293", 0.8),
            (self.CLOTHING_KEYWORDS, "1059", 0.7),
            (self.VINTAGE_KEYWORDS, "20081", 0.6),
            (self.AUTO_KEYWORDS, "6024", 0.7)
        ]
        self.category_service = EBayCategoryService()
        try:
            self.gemini_client = GeminiRestClient(api_key=os.getenv('GOOGLE_API_KEY'))
        except:
            self.gemini_client = None
    
    def get_required_fields(self, category_id: str) -> List[Dict]:
        """Get exact required fields from eBay Taxonomy API."""
        aspects = self.category_service.get_category_aspects(category_id)
        required_fields = []
        
        for aspect in aspects.get("required", []):
            field_info = {
                "name": aspect["name"],
                "required": True,
                "data_type": aspect.get("dataType", "STRING"),
                "input_mode": aspect.get("mode", "FREETEXT"),
                "allowed_values": aspect.get("values", [])
            }
            required_fields.append(field_info)
        
        return required_fields
    
    def generate_questions(self, category_id: str, known_data: Dict[str, Any]) -> List[Dict]:
        """Generate questions for missing required fields."""
        required_fields = self.get_required_fields(category_id)
        questions = []
        
        # Performance optimization: pre-compute normalized keys to avoid repeated O(M) list comprehensions
        known_keys = {k.lower() for k in known_data}

        for field in required_fields:
            if field["name"].lower() not in known_keys:
                questions.append({
                    "field": field["name"],
                    "question": self._create_question(field, known_data),
                    "type": "required",
                    "input_type": "select" if field["input_mode"] == "SELECT" else "text",
                    "options": field["allowed_values"]
                })
        
        return questions[:3]
    
    def _create_question(self, field: Dict, known_data: Dict) -> str:
        name = field["name"].lower()
        item = known_data.get("item_name", "this item")
        
        templates = {
            "brand": f"What brand is {item}?",
            "type": f"What type is {item}?",
            "size": f"What size is {item}?",
            "color": f"What color is {item}?",
            "condition": f"What condition is {item} in?",
        }
        
        for key, template in templates.items():
            if key in name:
                return template
        
        return f"What is the {field['name']} for {item}?"
    
    def validate_data(self, category_id: str, data: Dict) -> Dict:
        """Validate data against exact eBay requirements."""
        required_fields = self.get_required_fields(category_id)
        missing = []
        invalid = []
        
        for field in required_fields:
            field_name = field["name"]
            if field_name not in data or not data[field_name]:
                missing.append(field_name)
            elif field["input_mode"] == "SELECT" and field["allowed_values"]:
                if data[field_name] not in field["allowed_values"]:
                    invalid.append({
                        "field": field_name,
                        "value": data[field_name],
                        "allowed": field["allowed_values"][:5]
                    })
        
        return {
            "valid": len(missing) == 0 and len(invalid) == 0,
            "missing": missing,
            "invalid": invalid
        }
    
    def suggest_category_from_data(self, item_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest eBay categories based on item data."""
        
        # Simple keyword-based category mapping
        item_name = item_data.get('item_name', '').lower()
        
        # Performance optimization: use pre-allocated tuples and for-loops to avoid list and generator overhead
        for keywords, category_id, confidence in self.CATEGORY_MAPPING:
            for word in keywords:
                if word in item_name:
                    return [{"category_id": category_id, "confidence": confidence}]

        return [{"category_id": "293", "confidence": 0.3}]  # Default to electronics
