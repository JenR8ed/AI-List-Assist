"""
Mock Valuation Service for testing
"""

from typing import Dict, Any, Optional
from models.agent_contracts import ItemValuation, Profitability

class MockValuationService:
    """Mock valuation service that returns varied test data."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.mock_items = [
            {
                "item_name": "Sony WH-1000XM4 Headphones",
                "brand": "Sony",
                "estimated_age": "2-3 years",
                "condition_score": 8,
                "condition_notes": "Good condition, minor wear on ear cups",
                "estimated_value": 180.00,
                "value_range": {"low": 150.00, "high": 220.00},
                "resale_score": 9,
                "profitability": "high",
                "recommended_platforms": ["eBay", "Amazon", "Mercari"],
                "key_factors": ["Popular brand", "High demand", "Good condition"],
                "risks": ["Market saturation"],
                "listing_tips": ["Include original box if available", "Highlight noise cancellation"],
                "worth_listing": True,
                "confidence": 0.9
            },
            {
                "item_name": "Vintage Ceramic Mug",
                "brand": "Unknown",
                "estimated_age": "10+ years",
                "condition_score": 6,
                "condition_notes": "Some chips on rim, faded design",
                "estimated_value": 8.50,
                "value_range": {"low": 5.00, "high": 12.00},
                "resale_score": 4,
                "profitability": "low",
                "recommended_platforms": ["eBay"],
                "key_factors": ["Vintage appeal"],
                "risks": ["Low demand", "Shipping fragility"],
                "listing_tips": ["Pack carefully", "Market as vintage"],
                "worth_listing": False,
                "confidence": 0.6
            },
            {
                "item_name": "Apple iPhone 12 Pro",
                "brand": "Apple",
                "estimated_age": "3-4 years",
                "condition_score": 7,
                "condition_notes": "Screen scratches, battery at 85%",
                "estimated_value": 320.00,
                "value_range": {"low": 280.00, "high": 380.00},
                "resale_score": 8,
                "profitability": "high",
                "recommended_platforms": ["eBay", "Swappa", "Facebook Marketplace"],
                "key_factors": ["Apple brand", "Still supported", "Good specs"],
                "risks": ["Battery degradation", "New models available"],
                "listing_tips": ["Include battery health", "Show all angles"],
                "worth_listing": True,
                "confidence": 0.85
            }
        ]
    
    def evaluate_item(self, image_base64: str, media_type: str, detected_item: Optional[Dict[str, Any]] = None) -> ItemValuation:
        """Return a valuation based on detected item information."""
        if detected_item:
            # Try to match detected item with mock data
            detected_brand = (detected_item.get("brand") or "").lower()
            detected_category = (detected_item.get("probable_category") or "").lower()
            detected_text = " ".join(detected_item.get("detected_text") or []).lower()

            # Match based on brand or detected text
            if "apple" in detected_brand or "iphone" in detected_text:
                mock_data = self.mock_items[2]  # iPhone 12 Pro
            elif "sony" in detected_brand or "wh-1000xm" in detected_text:
                mock_data = self.mock_items[0]  # Sony headphones
            elif "mug" in detected_category or "ceramic" in detected_text:
                mock_data = self.mock_items[1]  # Vintage mug
            else:
                # Default to first item if no match
                mock_data = self.mock_items[0]
        else:
            # Fallback to hash-based selection for backward compatibility
            image_hash = hash(image_base64) % len(self.mock_items)
            mock_data = self.mock_items[image_hash]

        return ItemValuation(
            item_id=detected_item.get("item_id", "item_1") if detected_item else "item_1",
            item_name=mock_data["item_name"],
            brand=mock_data["brand"],
            estimated_age=mock_data["estimated_age"],
            condition_score=mock_data["condition_score"],
            condition_notes=mock_data["condition_notes"],
            is_complete=True,
            estimated_value=mock_data["estimated_value"],
            value_range=mock_data["value_range"],
            resale_score=mock_data["resale_score"],
            profitability=Profitability(mock_data["profitability"]),
            recommended_platforms=mock_data["recommended_platforms"],
            key_factors=mock_data["key_factors"],
            risks=mock_data["risks"],
            listing_tips=mock_data["listing_tips"],
            worth_listing=mock_data["worth_listing"],
            confidence=mock_data["confidence"]
        )
