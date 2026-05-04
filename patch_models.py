import re

with open('shared/models.py', 'r') as f:
    content = f.read()

# Add pydantic imports
if 'from pydantic import BaseModel, Field' not in content:
    content = content.replace('from dataclasses import dataclass, field', 'from dataclasses import dataclass, field\nfrom pydantic import BaseModel, Field')

# Update ListingDraft
old_draft = '''@dataclass
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
        }'''

new_draft = '''class ListingDraft(BaseModel):
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "item_id": self.item_id,
            "title": self.title,
            "description": self.description,
            "category_id": self.category_id,
            "condition": self.condition.value if hasattr(self.condition, 'value') else self.condition,
            "price": self.price,
            "item_specifics": self.item_specifics,
            "shipping_details": self.shipping_details,
            "images": self.images,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at,
            "missing_required_specifics": self.missing_required_specifics,
            "ready_for_api": self.ready_for_api
        }'''

content = content.replace(old_draft, new_draft)

with open('shared/models.py', 'w') as f:
    f.write(content)
