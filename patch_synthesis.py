import re

with open('services/listing_synthesis.py', 'r') as f:
    content = f.read()

imports = """
from typing import Dict, Any, Optional
from shared.models import ListingDraft, ItemCondition, ConversationState, ItemValuation
import uuid
from services.gemini_rest_client import GeminiRestClient
import os
import json
import re
from pydantic import ValidationError
"""

content = re.sub(r'from typing import Dict, Any, Optional\nfrom shared\.models import ListingDraft, ItemCondition, ConversationState, ItemValuation\nimport uuid', imports, content)

init_method = """    def __init__(self):
        \"\"\"Initialize listing synthesis engine.\"\"\"
        self.gemini_client = GeminiRestClient(api_key=os.getenv('GOOGLE_API_KEY'))"""

content = re.sub(r'    def __init__\(self\):\n\s*\"\"\"Initialize listing synthesis engine\.\"\"\"\n\s*pass', init_method, content)

create_method_old = """    def create_listing_draft(
        self,
        item_id: str,
        valuation: ItemValuation,
        conversation_state: ConversationState,
        images: list = None
    ) -> ListingDraft:
        \"\"\"
        Create a listing draft from valuation and conversation data.

        Args:
            item_id: Item identifier
            valuation: Item valuation data
            conversation_state: Conversation state with gathered details
            images: List of image URLs/paths

        Returns:
            ListingDraft ready for review
        \"\"\"
        # Merge data from valuation and conversation
        all_data = {**valuation.to_dict(), **conversation_state.known_fields}

        # Generate title
        title = self._generate_title(all_data)

        # Generate description
        description = self._generate_description(all_data, valuation)

        # Determine condition
        condition = self._determine_condition(all_data)

        # Calculate price
        price = self._calculate_price(all_data, valuation)

        # Extract item specifics
        item_specifics = self._extract_item_specifics(all_data)

        # Shipping details (defaults)
        shipping_details = self._generate_shipping_details(all_data)

        listing_id = str(uuid.uuid4())

        return ListingDraft(
            listing_id=listing_id,
            item_id=item_id,
            title=title,
            description=description,
            category_id=None,  # Would need eBay category mapping
            condition=condition,
            price=price,
            item_specifics=item_specifics,
            shipping_details=shipping_details,
            images=images or [],
            confidence=conversation_state.confidence
        )"""

create_method_new = """    def create_listing_draft(
        self,
        item_id: str,
        valuation: ItemValuation,
        conversation_state: ConversationState,
        images: list = None
    ) -> ListingDraft:
        \"\"\"
        Create a listing draft using an LLM to generate the structured payload.
        \"\"\"
        all_data = {**valuation.to_dict(), **conversation_state.known_fields}

        schema_instruction = \"\"\"
Return strictly valid JSON following this format:
{
    "listing_id": "auto_generated",
    "item_id": "the_item_id",
    "title": "eBay optimized title (max 80 chars)",
    "description": "HTML description",
    "category_id": "category id string",
    "condition": "New" | "New other (see details)" | "New with defects" | "Manufacturer refurbished" | "Seller refurbished" | "Used" | "For parts or not working",
    "price": 0.0,
    "item_specifics": {"Brand": "...", "Model": "..."},
    "shipping_details": {"shipping_type": "Calculated", "handling_time": "1", "domestic_shipping": true, "international_shipping": false},
    "images": [],
    "confidence": 0.9,
    "missing_required_specifics": [],
    "ready_for_api": true
}
\"\"\"
        prompt = f"Generate an eBay listing draft based on this data:\\n{json.dumps(all_data, indent=2)}\\n{schema_instruction}"

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response_text, _ = self.gemini_client.generate_content(prompt)

                # Strip markdown
                clean_json = response_text
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    clean_json = json_match.group(1)
                else:
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        clean_json = response_text[json_start:json_end]

                # Update listing_id, item_id, images before validation if necessary, or just load and overwrite
                parsed_data = json.loads(clean_json)
                parsed_data["listing_id"] = str(uuid.uuid4())
                parsed_data["item_id"] = item_id
                parsed_data["images"] = images or []

                # Re-dump to string for model_validate_json
                clean_json = json.dumps(parsed_data)

                draft = ListingDraft.model_validate_json(clean_json)
                return draft

            except (ValidationError, json.JSONDecodeError) as e:
                if attempt < max_retries:
                    prompt += f"\\n\\nValidation failed: {e}. Please correct the format and return strictly valid JSON."
                else:
                    raise e

        raise Exception("Failed to generate listing draft")"""

content = content.replace(create_method_old, create_method_new)

with open('services/listing_synthesis.py', 'w') as f:
    f.write(content)
