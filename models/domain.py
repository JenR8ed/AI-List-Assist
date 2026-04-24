# models/domain.py
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Column, JSON

# ==========================================
# SQLMODEL DATABASE TABLES (Data Layer)
# ==========================================


class ValuationRecord(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(
        uuid.uuid4()), primary_key=True)
    item_name: str
    estimated_value: float
    worth_listing: bool
    valuation_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ListingDraftRecord(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(
        uuid.uuid4()), primary_key=True)
    valuation_id: str = Field(foreign_key="valuationrecord.id")
    title: str
    price: float
    status: str = Field(default="draft")
    ebay_listing_id: Optional[str] = None
    aspects: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# PYDANTIC API SCHEMAS (Validation Layer)
# ==========================================

# -- Conversation Payloads --
class ConversationStartRequest(BaseModel):
    item_id: str
    initial_data: Dict[str, Any] = {}


class ConversationAnswerRequest(BaseModel):
    session_id: str
    answer: str

# -- Listing Payloads --


class ListingDraftCreateRequest(BaseModel):
    valuation_id: str
    title: str
    price: float
    description: str
    category_id: str
    condition: str
    aspects: Dict[str, Any] = {}


class EbayPublishRequest(BaseModel):
    listing_id: str

# -- Category Payloads --


class CategoryQuestionsRequest(BaseModel):
    category_id: str = "293"
    known_data: Dict[str, Any] = {}
