"""
shared/schemas/item_response.py

Defines the strict JSON output format expected from Gemini/AI models.
This acts as the "Contract" between the AI and the Python backend.
"""

# The detailed schema structure (useful for validation or documentation)
ITEM_DETECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "description": "Unique ID like item_1"},
                    "probable_category": {"type": "string", "description": "High-level eBay category (e.g., Electronics)"},
                    "detected_text": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Visible text on label/product"
                    },
                    "brand": {"type": "string"},
                    "model": {"type": "string"},
                    "visual_condition": {"type": "string", "description": "Brief visual assessment (e.g., Scratched, New)"}
                },
                "required": ["probable_category"]
            }
        }
    },
    "required": ["items"]
}

# The specific instruction string to inject into AI prompts
# This replaces the hardcoded string currently in vision_service.py
SCHEMA_INSTRUCTION = """
Return strictly valid JSON following this format:
{
    "items": [
        {
            "item_id": "item_1",
            "probable_category": "Electronics",
            "detected_text": ["Sony", "WH-1000XM4"],
            "brand": "Sony",
            "model": "WH-1000XM4",
            "visual_condition": "Good, minor wear on ear cups"
        }
    ]
}
"""
