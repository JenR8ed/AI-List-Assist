"""
AI Category-Specific Detail Generator
"""

import os
from typing import Any, Dict, List
from services.ebay_category_service import EBayCategoryService
from services.gemini_rest_client import GeminiRestClient


class CategoryDetailGenerator:
    # Class constants for keyword matching to avoid list recreation on every call
    ELECTRONICS_KEYWORDS = ("phone", "headphone", "electronic", "computer", "laptop", "tablet", "camera", "speaker", "tv", "monitor")
    FASHION_KEYWORDS = ("shirt", "dress", "shoe", "sneaker", "jacket", "pants", "bag", "handbag", "watch", "jewelry")
    HOME_KEYWORDS = ("furniture", "table", "chair", "sofa", "lamp", "kitchen", "decor", "rug")

    def __init__(self):
        self.category_service = EBayCategoryService()
        # Category suggestions do not require Gemini. Only initialize the
        # optional client when a server-side key is configured.
        self.gemini_client = None
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            try:
                self.gemini_client = GeminiRestClient(api_key=api_key)
            except Exception:
                # Keep local/fixture category suggestions available if the
                # optional Gemini client cannot initialize.
                self.gemini_client = None

    def generate_details(self, item_name: str, category_id: str = None, image_b64: str = None) -> Dict[str, Any]:
        """Generate category-specific item details and suggested aspects."""
        if not category_id:
            suggestions = self._suggest_category(item_name)
            category_id = suggestions[0]["category_id"] if suggestions else "293"

        aspects = self.category_service.get_item_aspects_for_category(category_id) or []
        return {
            "category_id": category_id,
            "aspects": aspects,
            "suggested_title": item_name[:80],
            "confidence": 0.7,
        }

    def _suggest_category(self, item_name: str) -> List[Dict[str, Any]]:
        item_name = (item_name or "").lower()
        for word in self.ELECTRONICS_KEYWORDS:
            if word in item_name:
                return [{"category_id": "293", "confidence": 0.8}]
        for word in self.FASHION_KEYWORDS:
            if word in item_name:
                return [{"category_id": "11450", "confidence": 0.75}]
        for word in self.HOME_KEYWORDS:
            if word in item_name:
                return [{"category_id": "11700", "confidence": 0.7}]
        return [{"category_id": "293", "confidence": 0.3}]  # Default to electronics

    def suggest_category_from_data(self, item_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest a category from item metadata without external API calls."""
        name = str((item_data or {}).get("item_name") or "").lower()
        groups = (
            (("phone", "headphone", "electronic", "computer", "laptop", "tablet",
              "camera", "speaker", "monitor"), "293", 0.8),
            (("shirt", "pants", "clothing", "jacket", "dress", "shoe",
              "sneaker"), "1059", 0.7),
            (("vintage", "collectible", "antique"), "20081", 0.6),
            (("car", "auto", "vehicle", "engine"), "6024", 0.7),
        )
        for keywords, category_id, confidence in groups:
            if any(word in name for word in keywords):
                return [{"category_id": category_id, "confidence": confidence}]
        return [{"category_id": "293", "confidence": 0.3}]

    def get_required_fields(self, category_id: str) -> List[Dict[str, Any]]:
        """Normalize required aspects from the category service."""
        aspects = self.category_service.get_category_aspects(category_id) or {}
        return [
            {
                "name": aspect["name"],
                "input_mode": aspect.get("input_mode", aspect.get("mode", "FREETEXT")),
                "allowed_values": aspect.get("allowed_values", aspect.get("values", [])),
            }
            for aspect in aspects.get("required", [])
        ]

    def validate_data(self, category_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check required fields and constrained selections without publishing."""
        missing = []
        invalid = []
        for definition in self.get_required_fields(category_id):
            name = definition["name"]
            value = (data or {}).get(name)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(name)
                continue
            allowed = definition.get("allowed_values", [])
            if definition.get("input_mode") == "SELECT" and allowed and value not in allowed:
                invalid.append({"field": name, "value": value, "allowed": allowed})
        return {"valid": not missing and not invalid, "missing": missing, "invalid": invalid}
