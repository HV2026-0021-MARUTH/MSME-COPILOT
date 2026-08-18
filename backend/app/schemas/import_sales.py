from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class ColumnMapping(BaseModel):
    date_col: str
    product_col: str
    quantity_col: str
    selling_price_col: str
    cost_price_col: Optional[str] = None
    category_col: Optional[str] = None

class ParsedRow(BaseModel):
    row_index: int
    date: Optional[str] = None
    product_name: str
    quantity: int
    selling_price: float
    cost_price: Optional[float] = None
    category: Optional[str] = None
    
    is_valid: bool
    errors: List[str] = []
    
    # Matching
    matched_product_id: Optional[str] = None
    is_new_product: bool = False

class ImportPreviewResponse(BaseModel):
    file_id: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    detected_columns: List[str]
    mapped_columns: ColumnMapping
    
    new_products: List[str] = []
    
    rows: List[ParsedRow] = []

class NewProductDefinition(BaseModel):
    name: str
    category: str = "Uncategorized"
    selling_price: float
    purchase_price: float = 0.0
    unit: str = "unit"

class ImportConfirmPayload(BaseModel):
    shop_id: str = "shop_001"
    file_id: str
    mapping: ColumnMapping
    create_new_products: bool = False
    # If the user provides specific definitions for the new products
    new_products_info: List[NewProductDefinition] = []

class ImportSummaryResponse(BaseModel):
    status: str
    imported_sales: int
    products_created: int
    skipped_rows: int
    errors: int
    duplicates_detected: int
    message: str
