from pydantic import BaseModel, Field
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

class BoundingBox(BaseModel):
    """Bounding box coordinates for item detection."""
    x: int
    y: int
    width: int
    height: int

class DetectedItem(BaseModel):
    """A single item detected in an image."""
    item_id: str
    bbox: BoundingBox
    confidence: float
    probable_category: Optional[str] = None
    detected_text: List[str] = Field(default_factory=list)
    brand: Optional[str] = None
    model: Optional[str] = None

class ItemValuation(BaseModel):
    """Valuation result for an item."""
    item_id: str
    item_name: str
    brand: Optional[str] = None
    estimated_age: Optional[str] = None
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

class ConversationState(BaseModel):
    """State of the AI conversation for gathering listing details."""
    session_id: str
    item_id: str
    known_fields: Dict[str, Any] = Field(default_factory=dict)
    unknown_fields: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    questions_asked: List[str] = Field(default_factory=list)
    current_question: Optional[str] = None
    is_complete: bool = False

class ListingDraft(BaseModel):
    """A draft eBay listing ready for review/publishing."""
    listing_id: str
    item_id: str
    title: str = Field(max_length=80)
    description: str
    category_id: str
    condition: ItemCondition
    price: float
    item_specifics: Dict[str, str] = Field(default_factory=dict)
    shipping_details: Dict[str, Any] = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    missing_required_specifics: List[str] = Field(default_factory=list)
    ready_for_api: bool = False

class ImageSession(BaseModel):
    """A session for processing one or more images."""
    session_id: str
    images: List[str]  # Image file paths or URLs
    detected_items: List[DetectedItem] = Field(default_factory=list)
    valuations: List[ItemValuation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
