"""
shared/schemas/gemini_response.py

Re-exports the canonical Gemini item detection schema from item_response.py
for backward compatibility.
"""

from .item_response import ITEM_DETECTION_SCHEMA, SCHEMA_INSTRUCTION

__all__ = ["ITEM_DETECTION_SCHEMA", "SCHEMA_INSTRUCTION"]
