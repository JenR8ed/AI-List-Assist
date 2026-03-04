# The strict JSON structure we demand from Gemini
ITEM_DETECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string"},
                    "probable_category": {"type": "string"},
                    "detected_text": {"type": "array", "items": {"type": "string"}},
                    "brand": {"type": "string"},
                    "model": {"type": "string"}
                },
                "required": ["probable_category", "brand"]
            }
        }
    },
    "required": ["items"]
}

# The prompt instructions to inject into Vision Service
SCHEMA_INSTRUCTION = """
Return strictly valid JSON following this schema:
{
    "items": [
        {
            "item_id": "item_1",
            "probable_category": "Electronics",
            "detected_text": ["Sony", "WH-1000XM4"],
            "brand": "Sony",
            "model": "WH-1000XM4"
        }
    ]
}
"""
