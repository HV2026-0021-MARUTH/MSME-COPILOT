from app.api.deps import get_current_user
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from app.db.database import get_db
from app.db.models import Purchase, PurchaseItem, Inventory, Product
from app.schemas.inventory import InvoiceExtractionResult, ProductCreate
from app.services.invoice_parser import parse_invoice_image
from app.services.analytics import update_inventory_on_purchase

router = APIRouter(prefix="/api/purchases", tags=["Purchases"], dependencies=[Depends(get_current_user)])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

class ConfirmedPurchaseItemInput(BaseModel):
    product_id: Optional[str] = None
    extracted_name: Optional[str] = None
    quantity: int = Field(..., gt=0, description="Quantity must be positive")
    unit_cost: float = Field(..., ge=0, description="Unit cost must be non-negative")
    new_product: Optional[ProductCreate] = None

class PurchaseConfirmPayload(BaseModel):
    shop_id: str = "shop_001"
    supplier_name: Optional[str] = "Supplier"
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    force_confirm: Optional[bool] = False
    items: List[ConfirmedPurchaseItemInput]

@router.post("/invoice", response_model=InvoiceExtractionResult)
async def upload_and_extract_invoice(
    file: UploadFile = File(...),
    shop_id: str = "shop_001",
    db: Session = Depends(get_db)
):
    # 1. Validate File MIME Type
    if file.content_type not in ALLOWED_MIME_TYPES and not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Supported formats: JPEG, PNG, WebP."
        )

    # 2. Validate File Size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds 10MB limit (Uploaded size: {len(contents) / (1024*1024):.1f} MB)."
        )

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 3. Fetch existing products for matching
    db_products = db.query(Product).all()

    # 4. Perform AI / OCR Extraction & Product Matching (Does NOT modify inventory)
    extraction = parse_invoice_image(
        image_bytes=contents,
        filename=file.filename,
        db_products=db_products
    )

    # 5. Duplicate Invoice Protection Check
    inv_num = extraction.get("invoice_number")
    if inv_num:
        existing_purch = db.query(Purchase).filter(
            Purchase.shop_id == shop_id,
            Purchase.invoice_number == inv_num
        ).first()
        if existing_purch:
            extraction["duplicate_warning"] = f"Warning: Invoice '{inv_num}' has already been processed for this store."

    return extraction

@router.post("/manual", status_code=status.HTTP_201_CREATED)
@router.post("/confirm", status_code=status.HTTP_201_CREATED)
def confirm_purchase_and_update_inventory(req: PurchaseConfirmPayload, db: Session = Depends(get_db)):
    if not req.items:
        raise HTTPException(status_code=400, detail="Purchase items list cannot be empty.")

    # Duplicate Protection Check on Confirmation
    if req.invoice_number and not req.force_confirm:
        existing = db.query(Purchase).filter(
            Purchase.shop_id == req.shop_id,
            Purchase.invoice_number == req.invoice_number
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate Invoice Protection: Invoice '{req.invoice_number}' has already been confirmed."
            )

    purch_id = f"purch_{uuid.uuid4().hex[:8]}"

    # Transactional Atomic Update
    try:
        total_amount = 0.0
        purchase_items_to_add = []
        updated_inventories = []

        for item in req.items:
            if item.quantity <= 0:
                raise HTTPException(status_code=400, detail="Item quantity must be greater than 0.")
            if item.unit_cost < 0:
                raise HTTPException(status_code=400, detail="Unit cost cannot be negative.")

            target_product_id = item.product_id

            # Handle New Product creation inline if requested
            if not target_product_id and item.new_product:
                if not item.new_product.name or not item.new_product.name.strip():
                    raise HTTPException(status_code=400, detail="New product name is required.")
                if item.new_product.selling_price < 0 or item.new_product.purchase_price < 0:
                    raise HTTPException(status_code=400, detail="Product selling/purchase prices cannot be negative.")

                new_prod_id = f"prod_{uuid.uuid4().hex[:8]}"
                created_prod = Product(
                    id=new_prod_id,
                    name=item.new_product.name.strip(),
                    category=item.new_product.category.strip() if item.new_product.category else "General",
                    brand=item.new_product.brand.strip() if item.new_product.brand else None,
                    unit=item.new_product.unit.strip() if item.new_product.unit else "unit",
                    purchase_price=item.unit_cost if item.new_product.purchase_price == 0 else item.new_product.purchase_price,
                    selling_price=item.new_product.selling_price,
                    reorder_level=item.new_product.reorder_level
                )
                db.add(created_prod)
                target_product_id = new_prod_id

            if not target_product_id:
                raise HTTPException(status_code=400, detail=f"Product not selected or created for item '{item.extracted_name or 'Unknown'}'.")

            product = db.query(Product).filter(Product.id == target_product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with id '{target_product_id}' not found.")

            line_cost = round(item.quantity * item.unit_cost, 2)
            total_amount += line_cost

            # Fetch inventory record
            inv = db.query(Inventory).filter(
                Inventory.shop_id == req.shop_id,
                Inventory.product_id == target_product_id
            ).first()

            if not inv:
                inv = Inventory(
                    id=f"inv_{uuid.uuid4().hex[:8]}",
                    shop_id=req.shop_id,
                    product_id=target_product_id,
                    quantity=item.quantity
                )
                db.add(inv)
                new_qty = item.quantity
            else:
                new_qty = update_inventory_on_purchase(inv.quantity, item.quantity)
                inv.quantity = new_qty

            purchase_items_to_add.append({
                "product_id": target_product_id,
                "quantity": item.quantity,
                "unit_cost": item.unit_cost
            })

            updated_inventories.append({
                "product_id": target_product_id,
                "product_name": product.name,
                "new_quantity": new_qty
            })

        purchase = Purchase(
            id=purch_id,
            shop_id=req.shop_id,
            supplier_name=req.supplier_name or "Supplier",
            invoice_number=req.invoice_number or f"INV-{uuid.uuid4().hex[:6].upper()}",
            total_amount=round(total_amount, 2)
        )
        db.add(purchase)

        for pi in purchase_items_to_add:
            pi_id = f"pi_{uuid.uuid4().hex[:8]}"
            db.add(PurchaseItem(
                id=pi_id,
                purchase_id=purch_id,
                product_id=pi["product_id"],
                quantity=pi["quantity"],
                unit_cost=pi["unit_cost"]
            ))

        db.commit()

        return {
            "success": True,
            "status": "confirmed",
            "purchase_id": purch_id,
            "total_amount": round(total_amount, 2),
            "updated_inventories": updated_inventories
        }

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Purchase transaction failed: {str(e)}")
