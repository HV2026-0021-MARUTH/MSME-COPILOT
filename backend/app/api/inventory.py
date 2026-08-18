from app.api.deps import get_current_user
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import Product, Inventory
from app.schemas.inventory import (
    ProductCreate, ProductUpdate, ProductResponse, InventoryItemResponse, StockStatusEnum
)
from app.services.analytics import determine_stock_status, calculate_inventory_value

router = APIRouter(tags=["Inventory & Products"], dependencies=[Depends(get_current_user)])

@router.get("/api/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.name.asc()).all()
    return products

@router.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id '{product_id}' not found")
    return product

@router.post("/api/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    # Validate fields
    if not product_in.name or not product_in.name.strip():
        raise HTTPException(status_code=400, detail="Product name is required")
    if product_in.purchase_price < 0 or product_in.selling_price < 0:
        raise HTTPException(status_code=400, detail="Prices cannot be negative")
    if product_in.reorder_level < 0:
        raise HTTPException(status_code=400, detail="Reorder level cannot be negative")

    prod_id = f"prod_{uuid.uuid4().hex[:8]}"
    product = Product(
        id=prod_id,
        name=product_in.name.strip(),
        category=product_in.category.strip(),
        brand=product_in.brand.strip() if product_in.brand else None,
        unit=product_in.unit.strip() if product_in.unit else "unit",
        purchase_price=product_in.purchase_price,
        selling_price=product_in.selling_price,
        reorder_level=product_in.reorder_level
    )
    db.add(product)

    # Initialize inventory record for default shop if it doesn't exist
    inv = Inventory(id=f"inv_{uuid.uuid4().hex[:8]}", shop_id="shop_001", product_id=prod_id, quantity=0)
    db.add(inv)

    db.commit()
    db.refresh(product)
    return product

@router.put("/api/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, product_in: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id '{product_id}' not found")

    update_data = product_in.model_dump(exclude_unset=True)

    if "name" in update_data:
        if not update_data["name"] or not update_data["name"].strip():
            raise HTTPException(status_code=400, detail="Product name cannot be empty")
        product.name = update_data["name"].strip()

    if "category" in update_data and update_data["category"]:
        product.category = update_data["category"].strip()

    if "brand" in update_data:
        product.brand = update_data["brand"].strip() if update_data["brand"] else None

    if "unit" in update_data and update_data["unit"]:
        product.unit = update_data["unit"].strip()

    if "purchase_price" in update_data:
        if update_data["purchase_price"] < 0:
            raise HTTPException(status_code=400, detail="Purchase price cannot be negative")
        product.purchase_price = update_data["purchase_price"]

    if "selling_price" in update_data:
        if update_data["selling_price"] < 0:
            raise HTTPException(status_code=400, detail="Selling price cannot be negative")
        product.selling_price = update_data["selling_price"]

    if "reorder_level" in update_data:
        if update_data["reorder_level"] < 0:
            raise HTTPException(status_code=400, detail="Reorder level cannot be negative")
        product.reorder_level = update_data["reorder_level"]

    db.commit()
    db.refresh(product)
    return product

@router.get("/api/inventory", response_model=List[InventoryItemResponse])
def get_inventory(shop_id: str = "shop_001", db: Session = Depends(get_db)):
    items = db.query(Inventory).join(Product).filter(Inventory.shop_id == shop_id).all()
    res = []
    for item in items:
        p_price = float(item.product.purchase_price)
        s_price = float(item.product.selling_price)
        inv_val = calculate_inventory_value(item.quantity, p_price)
        status_str = determine_stock_status(item.quantity, item.product.reorder_level)

        res.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.name,
            "category": item.product.category,
            "brand": item.product.brand,
            "unit": item.product.unit,
            "quantity": item.quantity,
            "purchase_price": p_price,
            "selling_price": s_price,
            "inventory_value": inv_val,
            "reorder_level": item.product.reorder_level,
            "stock_status": StockStatusEnum(status_str)
        })
    return res
