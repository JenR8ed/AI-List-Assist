"""
Real Valuation Service
Uses Gemini to evaluate an item from an image.
"""

import json
import os
from typing import Dict, Any, Optional, List
from shared.models import ItemValuation, Profitability
from services.gemini_rest_client import GeminiRestClient
from services.mock_valuation_service import MockValuationService

class ValuationService:
    """Service that evaluates items using Gemini APIs."""

    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not provided")

        self.api_key = api_key

        # Initialize Gemini client
        try:
            self.gemini_client = GeminiRestClient(api_key=api_key, model="gemini-2.5-flash")
        except:
            self.gemini_client = GeminiRestClient(api_key=api_key, model="gemini-1.5-flash")

    def evaluate_item(self, image_base64: str, media_type: str, detected_item: Optional[Dict[str, Any]] = None, sold_comps: Optional[List[Dict[str, Any]]] = None, seo_tokens: Optional[List[str]] = None) -> ItemValuation:
        """Evaluate an item using Gemini, optionally informed by real market comps."""
        prompt = """You are an expert appraiser and eBay seller. Analyze this item and provide a valuation.
Please provide the following information in JSON format EXACTLY matching this structure:
{
    "item_name": "Name of the item",
    "brand": "Brand name, or null if unknown",
    "estimated_age": "Approximate age of the item",
    "condition_score": 1, // 1-10 integer score (1=poor, 10=mint)
    "condition_notes": "Detailed notes about the condition and wear",
    "is_complete": true, // boolean
    "estimated_value": 0.0, // Number (estimated selling price in USD)
    "value_range": {
        "low": 0.0,
        "high": 0.0
    },
    "resale_score": 1, // 1-10 integer score for how easy it is to resell
    "profitability": "high", // "high", "medium", "low", or "not_recommended"
    "recommended_platforms": ["eBay"],
    "key_factors": ["List of key value factors"],
    "risks": ["List of risks when selling"],
    "listing_tips": ["List of tips for the listing"],
    "worth_listing": true, // boolean
    "confidence": 0.5 // Number between 0.0 and 1.0 representing your confidence
}"""
        if detected_item:
            prompt += f"\n\nHere is some info already detected about the item: {json.dumps(detected_item, indent=2)}"

        if sold_comps:
            prompt += f"\n\nREAL MARKET DATA (Actual Sold Comps on eBay): {json.dumps(sold_comps[:5], indent=2)}"

        if seo_tokens:
            prompt += f"\n\nPOPULAR LISTING KEYWORDS: {', '.join(seo_tokens)}"

        try:
            response_text, usage = self.gemini_client.generate_content(
                prompt=prompt,
                inline_image_base64=image_base64,
                inline_image_mime_type=media_type,
                temperature=0.2,
                max_output_tokens=1024
            )

            # Extract JSON block
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)

                profitability_val = data.get("profitability", "low").lower()
                # Ensure profitability is valid enum value
                if profitability_val not in [p.value for p in Profitability]:
                    profitability_val = "low"

                valuation = ItemValuation(
                    item_id=detected_item.get("item_id", "item_1") if detected_item else "item_1",
                    item_name=data.get("item_name", "Unknown Item"),
                    brand=data.get("brand"),
                    estimated_age=data.get("estimated_age"),
                    condition_score=data.get("condition_score", 5),
                    condition_notes=data.get("condition_notes", ""),
                    is_complete=data.get("is_complete", True),
                    estimated_value=float(data.get("estimated_value", 0.0)),
                    value_range=data.get("value_range", {"low": 0.0, "high": 0.0}),
                    resale_score=data.get("resale_score", 5),
                    profitability=Profitability(profitability_val),
                    recommended_platforms=data.get("recommended_platforms", ["eBay"]),
                    key_factors=data.get("key_factors", []),
                    risks=data.get("risks", []),
                    listing_tips=data.get("listing_tips", []),
                    worth_listing=False,  # Computed below
                    confidence=float(data.get("confidence", 0.5)),
                    sold_comps=sold_comps or [],
                    seo_tokens=seo_tokens or []
                )

                # Apply business logic gate
                worth_listing = True
                if valuation.estimated_value < 15.0:
                    worth_listing = False
                    valuation.risks.append("Low value, shipping margins may destroy profitability")
                if valuation.condition_score < 3:
                    worth_listing = False
                    valuation.risks.append("Extremely poor condition makes it hard to sell")
                if valuation.profitability == Profitability.NOT_RECOMMENDED:
                    worth_listing = False

                valuation.worth_listing = worth_listing
                return valuation
        except Exception as e:
            print(f"Error evaluating item with Gemini: {e}")

        # Fallback to mock logic
        print("Falling back to mock valuation")
        mock_service = MockValuationService()
        return mock_service.evaluate_item(image_base64, media_type, detected_item)
