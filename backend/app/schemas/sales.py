from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class SaleParseRequest(BaseModel):
    shop_id: str = "shop_001"
    text: str = Field(..., min_length=1, description="Sale text is required")

class ParsedSaleCandidate(BaseModel):
    product_id: str
    name: str
    category: str
    selling_price: float

class ParsedSaleItem(BaseModel):
    raw_segment: str
    extracted_name: str
    quantity: int
    match_status: str  # "MATCHED", "AMBIGUOUS", "NEEDS_MATCH"
    matched_product_id: Optional[str] = None
    matched_product_name: Optional[str] = None
    selling_price: float = 0.0
    purchase_price: float = 0.0
    line_total: float = 0.0
    confidence: float = 0.0
    candidates: List[ParsedSaleCandidate] = []

class SaleParseResponse(BaseModel):
    mode: str = "text"
    raw_text: str
    items: List[ParsedSaleItem]
    estimated_total: float
    estimated_profit: float
    requires_review: bool

class SaleConfirmItemInput(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0, description="Quantity must be greater than 0")

class SaleConfirmPayload(BaseModel):
    shop_id: str = "shop_001"
    source: str = "voice"  # "voice", "text", "manual"
    items: List[SaleConfirmItemInput]

class SaleItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    unit_price: float
    unit_cost: float
    profit: float

    model_config = ConfigDict(from_attributes=True)

class SaleResponse(BaseModel):
    id: str
    shop_id: str
    total_amount: float
    total_cost: float
    profit: float
    margin_pct: float
    source: str
    created_at: datetime
    items: List[SaleItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
