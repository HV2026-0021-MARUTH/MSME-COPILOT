from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum

class StockStatusEnum(str, Enum):
    OUT_OF_STOCK = "OUT_OF_STOCK"
    LOW_STOCK = "LOW_STOCK"
    HEALTHY = "HEALTHY"

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, description="Product name is required")
    category: str = Field(..., min_length=1, description="Category is required")
    brand: Optional[str] = None
    unit: str = "unit"
    purchase_price: float = Field(..., ge=0, description="Purchase price must be >= 0")
    selling_price: float = Field(..., ge=0, description="Selling price must be >= 0")
    reorder_level: int = Field(10, ge=0, description="Reorder level must be >= 0")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, min_length=1)
    brand: Optional[str] = None
    unit: Optional[str] = None
    purchase_price: Optional[float] = Field(None, ge=0)
    selling_price: Optional[float] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)

class ProductResponse(ProductBase):
    id: str

    model_config = ConfigDict(from_attributes=True)

class InventoryItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    category: str
    brand: Optional[str] = None
    unit: str
    quantity: int
    purchase_price: float
    selling_price: float
    inventory_value: float
    reorder_level: int
    stock_status: StockStatusEnum

    model_config = ConfigDict(from_attributes=True)

class ExtractedInvoiceItem(BaseModel):
    extracted_name: str
    quantity: int = Field(..., gt=0)
    unit: str = "unit"
    unit_cost: float = Field(..., ge=0)
    total: float
    match_status: str  # "MATCHED" or "NEEDS_MATCH"
    matched_product_id: Optional[str] = None
    matched_product_name: Optional[str] = None
    confidence: float

class InvoiceExtractionResult(BaseModel):
    mode: str  # "ai" or "demo"
    supplier: str
    invoice_number: str
    invoice_date: str
    items: List[ExtractedInvoiceItem]
    subtotal: float
    tax: float
    grand_total: float
    confidence: float
    duplicate_warning: Optional[str] = None
