"""
Listing Synthesis Engine
Transforms gathered data into structured eBay listing format using Gemini structured outputs.
"""

import json
import os
import re
from typing import Any, Dict
import uuid
from pydantic import ValidationError
from shared.models import ConversationState, ItemCondition, ItemValuation, ListingDraft
from services.gemini_rest_client import GeminiRestClient


LISTING_DRAFT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "listing_id": {"type": "string"},
        "item_id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "category_id": {"type": "string"},
        "condition": {
            "type": "string",
            "enum": [
                "New",
                "New other (see details)",
                "New with defects",
                "Manufacturer refurbished",
                "Seller refurbished",
                "Used",
                "For parts or not working",
            ],
        },
        "price": {"type": "number"},
        "item_specifics": {"type": "object"},
        "shipping_details": {"type": "object"},
        "images": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        "missing_required_specifics": {"type": "array", "items": {"type": "string"}},
        "ready_for_api": {"type": "boolean"},
    },
    "required": [
        "title",
        "description",
        "category_id",
        "condition",
        "price",
    ],
}


class ListingSynthesisEngine:
    """Synthesizes eBay listings from gathered item data."""

    def __init__(self):
        """Initialize listing synthesis engine."""
        self.gemini_client = GeminiRestClient(api_key=os.getenv("GOOGLE_API_KEY"))

    def create_listing_draft(
        self,
        item_id: str,
        valuation: ItemValuation,
        conversation_state: ConversationState,
        images: list = None,
    ) -> ListingDraft:
        """
        Create a listing draft using an LLM with native responseSchema structured output.
        """
        all_data = {**valuation.to_dict(), **conversation_state.known_fields}

        schema_instruction = """
Return strictly valid JSON following this format:
{
    "listing_id": "auto_generated",
    "item_id": "the_item_id",
    "title": "eBay optimized title (max 80 chars)",
    "description": "HTML description",
    "category_id": "category id string",
    "condition": "New" | "New other (see details)" | "New with defects" | "Manufacturer refurbished" | "Seller refurbished" | "Used" | "For parts or not working",
    "price": 0.0,
    "item_specifics": {},
    "shipping_details": {},
    "images": [],
    "confidence": 0.0,
    "missing_required_specifics": [],
    "ready_for_api": false
}
"""

        prompt = f"Create an optimized eBay listing draft based on this data:\n{json.dumps(all_data, indent=2)}\n{schema_instruction}"

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                try:
                    response_text, _ = self.gemini_client.generate_content(
                        prompt,
                        response_schema=LISTING_DRAFT_SCHEMA,
                    )
                except TypeError:
                    response_text, _ = self.gemini_client.generate_content(prompt)

                clean_json = response_text
                json_match = re.search(r"```(?:json)?\s*({.*?})\s*```", response_text, re.DOTALL)
                if json_match:
                    clean_json = json_match.group(1)
                else:
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        clean_json = response_text[json_start:json_end]

                parsed_data = json.loads(clean_json)
                parsed_data["listing_id"] = str(uuid.uuid4())
                parsed_data["item_id"] = item_id
                parsed_data["images"] = images or []

                clean_json = json.dumps(parsed_data)
                draft = ListingDraft.model_validate_json(clean_json)
                return draft

            except (ValidationError, json.JSONDecodeError) as e:
                if attempt < max_retries:
                    prompt += f"\n\nValidation failed: {e}. Please correct the format and return strictly valid JSON."
                else:
                    raise e

        raise RuntimeError("Failed to generate listing draft")

    def _generate_title(self, data: Dict[str, Any]) -> str:
        """Generate eBay listing title from item data."""
        parts = []

        if data.get("brand"):
            parts.append(data["brand"])

        parts_lower_joined = "\0".join(parts).lower()

        if data.get("model"):
            model = data["model"]
            model_lower = model.lower()
            if model_lower not in parts_lower_joined:
                parts.append(model)
                parts_lower_joined += f"\0{model_lower}"

        item_name = data.get("item_name", "Item")
        item_name_lower = item_name.lower()
        if item_name_lower not in parts_lower_joined:
            parts.append(item_name)

        condition = data.get("condition", "")
        if condition and condition != "New":
            parts.append(condition)

        if data.get("is_complete") is False:
            parts.append("Incomplete")

        if data.get("has_box"):
            parts.append("w/ Box")

        title = " ".join(parts)
        return title[:80] if len(title) > 80 else title

    def _generate_description(self, data: Dict[str, Any], valuation: ItemValuation) -> str:
        """Generate detailed listing description."""
        lines = []

        lines.append(f"<h2>{data.get('item_name', 'Item')}</h2>")

        if data.get("brand"):
            lines.append(f"<p><strong>Brand:</strong> {data['brand']}</p>")
        if data.get("model"):
            lines.append(f"<p><strong>Model:</strong> {data['model']}</p>")

        condition_notes = data.get("condition_notes") or valuation.condition_notes
        if condition_notes:
            lines.append("<h3>Condition:</h3>")
            lines.append(f"<p>{condition_notes}</p>")

        if data.get("is_complete") is False:
            lines.append("<p><em>Note: Item may be incomplete.</em></p>")

        if valuation.key_factors:
            lines.append("<h3>Key Features:</h3><ul>")
            for factor in valuation.key_factors:
                lines.append(f"<li>{factor}</li>")
            lines.append("</ul>")

        if valuation.listing_tips:
            lines.append("<h3>Seller Notes:</h3><ul>")
            for tip in valuation.listing_tips:
                lines.append(f"<li>{tip}</li>")
            lines.append("</ul>")

        lines.append("<p><small>Please review all photos carefully. Item sold as-is.</small></p>")

        return "\n".join(lines)

    def _determine_condition(self, data: Dict[str, Any]) -> ItemCondition:
        """Determine eBay condition from data."""
        condition_str = data.get("condition", "").lower()

        if "new" in condition_str:
            if "defect" in condition_str:
                return ItemCondition.NEW_WITH_DEFECTS
            elif "other" in condition_str:
                return ItemCondition.NEW_OTHER
            return ItemCondition.NEW
        elif "refurbished" in condition_str:
            if "manufacturer" in condition_str:
                return ItemCondition.MANUFACTURER_REFURBISHED
            return ItemCondition.SELLER_REFURBISHED
        elif "parts" in condition_str or "not working" in condition_str:
            return ItemCondition.FOR_PARTS
        else:
            return ItemCondition.USED

    def _calculate_price(self, data: Dict[str, Any], valuation: ItemValuation) -> float:
        """Calculate listing price from valuation and user input."""
        if "price" in data and data["price"]:
            return float(data["price"])

        if valuation.estimated_value:
            return valuation.estimated_value

        value_range = valuation.value_range
        if value_range and isinstance(value_range, dict):
            low = value_range.get("low", 0)
            high = value_range.get("high", 0)
            if high > 0:
                return (low + high) / 2

        return 0.0

    def _extract_item_specifics(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract eBay item specifics from data."""
        specifics = {}

        if data.get("brand"):
            specifics["Brand"] = data["brand"]
        if data.get("model"):
            specifics["Model"] = data["model"]
        if data.get("color"):
            specifics["Color"] = data["color"]
        if data.get("material"):
            specifics["Material"] = data["material"]
        if data.get("dimensions"):
            specifics["Dimensions"] = data["dimensions"]
        if data.get("weight"):
            specifics["Weight"] = data["weight"]

        return specifics

    def _generate_shipping_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate default shipping details."""
        return {
            "shipping_type": "Calculated",
            "handling_time": "1",
            "domestic_shipping": True,
            "international_shipping": False,
        }
