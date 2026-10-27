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
