"""
Shared data models for the eBay Listing Assistant.
Defines canonical data structures used across services.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ItemCondition(str, Enum):
    """eBay item condition types."""
    NEW = "New"
    NEW_OTHER = "New other (see details)"
    NEW_WITH_DEFECTS = "New with defects"
    MANUFACTURER_REFURBISHED = "Manufacturer refurbished"
    SELLER_REFURBISHED = "Seller refurbished"
    USED = "Used"
    FOR_PARTS = "For parts or not working"


class Profitability(str, Enum):
    """Profitability assessment levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOT_RECOMMENDED = "not_recommended"


@dataclass
class BoundingBox:
    """Bounding box coordinates for item detection."""
    x: int
    y: int
    width: int
    height: int
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }


@dataclass
class DetectedItem:
    """A single item detected in an image."""
    item_id: str
    bbox: BoundingBox
    confidence: float
    probable_category: Optional[str] = None
    detected_text: List[str] = field(default_factory=list)
    brand: Optional[str] = None
    model: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "bbox": self.bbox.to_dict(),
            "confidence": self.confidence,
            "probable_category": self.probable_category,
            "detected_text": self.detected_text,
            "brand": self.brand,
            "model": self.model
        }


@dataclass
class ItemValuation:
    """Valuation result for an item."""
    item_id: str
    item_name: str
    brand: Optional[str]
    estimated_age: Optional[str]
    condition_score: int  # 1-10
    condition_notes: str
    is_complete: bool
    estimated_value: float
    value_range: Dict[str, float]  # {"low": x, "high": y}
    resale_score: int  # 1-10
    profitability: Profitability
    recommended_platforms: List[str]
    key_factors: List[str]
    risks: List[str]
    listing_tips: List[str]
    worth_listing: bool
    confidence: float  # 0.0-1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "brand": self.brand,
            "estimated_age": self.estimated_age,
            "condition_score": self.condition_score,
            "condition_notes": self.condition_notes,
            "is_complete": self.is_complete,
            "estimated_value": self.estimated_value,
            "value_range": self.value_range,
            "resale_score": self.resale_score,
            "profitability": self.profitability.value,
            "recommended_platforms": self.recommended_platforms,
            "key_factors": self.key_factors,
            "risks": self.risks,
            "listing_tips": self.listing_tips,
            "worth_listing": self.worth_listing,
            "confidence": self.confidence
        }


@dataclass
class ConversationState:
    """State of the AI conversation for gathering listing details."""
    session_id: str
    item_id: str
    known_fields: Dict[str, Any] = field(default_factory=dict)
    unknown_fields: List[str] = field(default_factory=list)
    confidence: float = 0.0
    questions_asked: List[str] = field(default_factory=list)
    current_question: Optional[str] = None
    is_complete: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "item_id": self.item_id,
            "known_fields": self.known_fields,
            "unknown_fields": self.unknown_fields,
            "confidence": self.confidence,
            "questions_asked": self.questions_asked,
            "current_question": self.current_question,
            "is_complete": self.is_complete
        }


@dataclass
class ListingDraft:
    """A draft eBay listing ready for review/publishing."""
    listing_id: str
    item_id: str
    title: str
    description: str
    category_id: Optional[str]
    condition: ItemCondition
    price: float
    item_specifics: Dict[str, str] = field(default_factory=dict)
    shipping_details: Dict[str, Any] = field(default_factory=dict)
    images: List[str] = field(default_factory=list)
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "item_id": self.item_id,
            "title": self.title,
            "description": self.description,
            "category_id": self.category_id,
            "condition": self.condition.value,
            "price": self.price,
            "item_specifics": self.item_specifics,
            "shipping_details": self.shipping_details,
            "images": self.images,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ImageSession:
    """A session for processing one or more images."""
    session_id: str
    images: List[str]  # Image file paths or URLs
    detected_items: List[DetectedItem] = field(default_factory=list)
    valuations: List[ItemValuation] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "images": self.images,
            "detected_items": [item.to_dict() for item in self.detected_items],
            "valuations": [val.to_dict() for val in self.valuations],
            "created_at": self.created_at.isoformat()
        }
