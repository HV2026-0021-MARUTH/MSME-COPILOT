from app.api.deps import get_current_user
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Product, Sale, SaleItem, Inventory
from app.schemas.import_sales import ImportPreviewResponse, ImportConfirmPayload, ImportSummaryResponse
from app.services.import_service import parse_and_validate_file, normalize_column_name, auto_detect_mapping
from app.services.analytics import update_inventory_on_sale
from datetime import datetime
import pandas as pd
import io

router = APIRouter(prefix="/api/import", tags=["Import"], dependencies=[Depends(get_current_user)])

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/preview", response_model=ImportPreviewResponse)
async def preview_import(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported")
        
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
        
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(content)
        
    db_products = db.query(Product).all()
    preview = parse_and_validate_file(content, file.filename, db_products)
    preview.file_id = file_id + "_" + file.filename
    
    return preview

@router.post("/confirm", response_model=ImportSummaryResponse)
def confirm_import(payload: ImportConfirmPayload, db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_DIR, payload.file_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Uploaded file not found or expired.")
        
    if payload.file_id.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
        
    db_products = db.query(Product).all()
    product_map = {p.name.strip().lower(): p for p in db_products}
    
    products_created = 0
    imported_sales = 0
    skipped_rows = 0
    errors = 0
    duplicates = 0
    
    # 1. Handle New Products
    if payload.create_new_products and payload.new_products_info:
        for p_info in payload.new_products_info:
            p_name_lower = p_info.name.strip().lower()
            if p_name_lower not in product_map:
                new_p = Product(
                    id=f"prod_{uuid.uuid4().hex[:8]}",
                    name=p_info.name.strip(),
                    category=p_info.category,
                    selling_price=p_info.selling_price,
                    purchase_price=p_info.purchase_price,
                    unit=p_info.unit
                )
                db.add(new_p)
                db.flush()
                # Create default inventory
                inv = Inventory(
                    id=f"inv_{uuid.uuid4().hex[:8]}",
                    shop_id=payload.shop_id,
                    product_id=new_p.id,
                    quantity=0
                )
                db.add(inv)
                product_map[p_name_lower] = new_p
                products_created += 1
                
    mapping = payload.mapping
    
    # Pre-fetch existing sales to do a simple duplicate check by date + total amount (heuristic)
    # For a real system we would need transaction IDs, but we do basic duplicate protection
    existing_sales = db.query(Sale).filter(Sale.shop_id == payload.shop_id).all()
    existing_sale_signatures = set(f"{s.created_at.strftime('%Y-%m-%d')}_{float(s.total_amount)}" for s in existing_sales)
    
    try:
        # 2. Import Sales
        # Group by date to create one Sale per day, or one Sale per row?
        # Usually one row = one transaction or one line item. We will group by Date to create a Sale per date.
        
        # We need a robust parsing of rows again, skipping invalid ones
        
        valid_items_by_date = {}
        
        for index, row in df.iterrows():
            try:
                p_name_raw = row[mapping.product_col]
                if pd.isna(p_name_raw) or str(p_name_raw).strip() == "":
                    skipped_rows += 1
                    continue
                p_name_lower = str(p_name_raw).strip().lower()
                
                if p_name_lower not in product_map:
                    skipped_rows += 1
                    continue
                    
                product = product_map[p_name_lower]
                
                date_val = str(row[mapping.date_col]).strip()
                # Attempt to parse date
                try:
                    parsed_date = pd.to_datetime(date_val).date()
                except:
                    skipped_rows += 1
                    continue
                    
                qty = int(row[mapping.quantity_col])
                if qty <= 0:
                    skipped_rows += 1
                    continue
                    
                sp_val = float(row[mapping.selling_price_col])
                if sp_val < 0:
                    skipped_rows += 1
                    continue
                    
                cp_val = float(product.purchase_price)
                if mapping.cost_price_col and mapping.cost_price_col in df.columns:
                    cv = row[mapping.cost_price_col]
                    if not pd.isna(cv) and float(cv) >= 0:
                        cp_val = float(cv)
                        
                date_str = parsed_date.strftime('%Y-%m-%d')
                if date_str not in valid_items_by_date:
                    valid_items_by_date[date_str] = []
                    
                valid_items_by_date[date_str].append({
                    "product": product,
                    "quantity": qty,
                    "unit_price": sp_val,
                    "unit_cost": cp_val
                })
            except Exception as e:
                errors += 1
                skipped_rows += 1
                
        # Now create Sales records
        for date_str, items in valid_items_by_date.items():
            total_amount = sum(i["quantity"] * i["unit_price"] for i in items)
            total_cost = sum(i["quantity"] * i["unit_cost"] for i in items)
            profit = total_amount - total_cost
            
            sig = f"{date_str}_{total_amount}"
            if sig in existing_sale_signatures:
                duplicates += 1
                continue
                
            sale_id = f"sale_{uuid.uuid4().hex[:8]}"
            sale_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            sale = Sale(
                id=sale_id,
                shop_id=payload.shop_id,
                total_amount=total_amount,
                total_cost=total_cost,
                profit=profit,
                source="csv_import",
                created_at=sale_date
            )
            db.add(sale)
            
            for item in items:
                si_id = f"si_{uuid.uuid4().hex[:8]}"
                item_profit = (item["unit_price"] - item["unit_cost"]) * item["quantity"]
                db.add(SaleItem(
                    id=si_id,
                    sale_id=sale_id,
                    product_id=item["product"].id,
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    unit_cost=item["unit_cost"],
                    profit=item_profit
                ))
                
                # Update inventory
                inv = db.query(Inventory).filter(
                    Inventory.shop_id == payload.shop_id,
                    Inventory.product_id == item["product"].id
                ).first()
                if inv:
                    inv.quantity = max(0, inv.quantity - item["quantity"])
                    
            imported_sales += len(items)
            
        db.commit()
        
        # Clean up file
        os.remove(file_path)
        
        return ImportSummaryResponse(
            status="success",
            imported_sales=imported_sales,
            products_created=products_created,
            skipped_rows=skipped_rows,
            errors=errors,
            duplicates_detected=duplicates,
            message="Import completed successfully"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
