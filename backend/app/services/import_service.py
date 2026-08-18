import pandas as pd
import io
import math
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.db.models import Product
from app.schemas.import_sales import ColumnMapping, ParsedRow, ImportPreviewResponse

def normalize_column_name(col: str) -> str:
    return str(col).strip().lower()

def auto_detect_mapping(columns: List[str]) -> ColumnMapping:
    # Common variations
    date_vars = ['date', 'sale date', 'transaction date', 'sold date']
    product_vars = ['product', 'product name', 'item', 'item name']
    qty_vars = ['qty', 'quantity', 'units', 'count']
    sp_vars = ['selling price', 'price', 'sale price', 'revenue', 'amount']
    cp_vars = ['cost', 'cost price', 'purchase price']
    cat_vars = ['category', 'type', 'department']

    mapping = {
        'date_col': '',
        'product_col': '',
        'quantity_col': '',
        'selling_price_col': '',
        'cost_price_col': None,
        'category_col': None
    }
    
    norm_cols = {c: normalize_column_name(c) for c in columns}

    for orig, norm in norm_cols.items():
        if not mapping['date_col'] and any(v in norm for v in date_vars):
            mapping['date_col'] = orig
        elif not mapping['product_col'] and any(v in norm for v in product_vars):
            mapping['product_col'] = orig
        elif not mapping['quantity_col'] and any(v == norm or norm.startswith(v) for v in qty_vars):
            mapping['quantity_col'] = orig
        elif not mapping['selling_price_col'] and any(v in norm for v in sp_vars):
            mapping['selling_price_col'] = orig
        elif not mapping['cost_price_col'] and any(v in norm for v in cp_vars):
            mapping['cost_price_col'] = orig
        elif not mapping['category_col'] and any(v in norm for v in cat_vars):
            mapping['category_col'] = orig

    return ColumnMapping(**mapping)

def parse_and_validate_file(file_content: bytes, filename: str, db_products: List[Product]) -> ImportPreviewResponse:
    if filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(file_content))
    else:
        df = pd.read_excel(io.BytesIO(file_content))
        
    detected_columns = list(df.columns)
    mapping = auto_detect_mapping(detected_columns)
    
    total_rows = len(df)
    valid_rows = 0
    invalid_rows = 0
    new_products_set = set()
    rows = []
    
    product_map = {p.name.strip().lower(): p for p in db_products}
    
    for index, row in df.iterrows():
        parsed = ParsedRow(row_index=index, product_name="", quantity=0, selling_price=0.0, is_valid=True)
        errors = []
        
        # Product Name
        if mapping.product_col and mapping.product_col in df.columns:
            val = row[mapping.product_col]
            if pd.isna(val) or str(val).strip() == "":
                errors.append("Product name is required")
            else:
                parsed.product_name = str(val).strip()
        else:
            errors.append("Product column missing")
            
        # Date
        if mapping.date_col and mapping.date_col in df.columns:
            val = row[mapping.date_col]
            if not pd.isna(val):
                parsed.date = str(val).strip()
            else:
                errors.append("Date is required")
        else:
            errors.append("Date column missing")
            
        # Quantity
        if mapping.quantity_col and mapping.quantity_col in df.columns:
            val = row[mapping.quantity_col]
            try:
                qty = int(val)
                if qty <= 0:
                    errors.append("Quantity must be greater than zero")
                else:
                    parsed.quantity = qty
            except:
                errors.append("Quantity must be a valid number")
        else:
            errors.append("Quantity column missing")
            
        # Selling Price
        if mapping.selling_price_col and mapping.selling_price_col in df.columns:
            val = row[mapping.selling_price_col]
            try:
                price = float(val)
                if price < 0:
                    errors.append("Selling price cannot be negative")
                else:
                    parsed.selling_price = price
            except:
                errors.append("Selling price must be a valid number")
        else:
            errors.append("Selling price column missing")
            
        # Cost Price
        if mapping.cost_price_col and mapping.cost_price_col in df.columns:
            val = row[mapping.cost_price_col]
            if not pd.isna(val):
                try:
                    price = float(val)
                    if price < 0:
                        errors.append("Cost price cannot be negative")
                    else:
                        parsed.cost_price = price
                except:
                    errors.append("Cost price must be a valid number")
                    
        # Category
        if mapping.category_col and mapping.category_col in df.columns:
            val = row[mapping.category_col]
            if not pd.isna(val):
                parsed.category = str(val).strip()
        
        # Product Matching
        if parsed.product_name:
            match_name = parsed.product_name.lower()
            if match_name in product_map:
                parsed.matched_product_id = product_map[match_name].id
            else:
                parsed.is_new_product = True
                new_products_set.add(parsed.product_name)
        
        if errors:
            parsed.is_valid = False
            parsed.errors = errors
            invalid_rows += 1
        else:
            valid_rows += 1
            
        rows.append(parsed)
        
    return ImportPreviewResponse(
        file_id="temp", # To be managed by API
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        detected_columns=detected_columns,
        mapped_columns=mapping,
        new_products=list(new_products_set),
        rows=rows
    )
