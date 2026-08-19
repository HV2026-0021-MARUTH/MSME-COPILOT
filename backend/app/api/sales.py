import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import Sale, SaleItem, Inventory, Product
from app.schemas.sales import (
    SaleParseRequest,
    SaleParseResponse,
    SaleConfirmPayload,
    SaleResponse,
)
from app.services.sales_parser import parse_sales_text
from app.services.analytics import update_inventory_on_sale
from app.api.deps import get_current_user

router = APIRouter(
    prefix="/api/sales", tags=["Sales"], dependencies=[Depends(get_current_user)]
)


@router.post("/parse", response_model=SaleParseResponse)
def parse_sale(
    req: SaleParseRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Parse natural-language sale text (voice or text input).
    CRITICAL SAFETY RULE: This endpoint reads data only and NEVER mutates inventory or database records.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Sale text cannot be empty.")

    db_products = (
        db.query(Product).filter(Product.shop_id == current_user["shop_id"]).all()
    )
    parsed_res = parse_sales_text(req.text, db_products)

    return parsed_res


@router.post(
    "/confirm", response_model=SaleResponse, status_code=status.HTTP_201_CREATED
)
def confirm_sale(
    req: SaleConfirmPayload,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Confirm sale, decrease inventory, and record financial metrics.
    CRITICAL SAFETY RULE: Server ALWAYS queries selling_price and purchase_price directly
    from the database Product table. Client-provided prices are ignored.
    """
    if not req.items:
        raise HTTPException(status_code=400, detail="Sale items list cannot be empty.")

    sale_id = f"sale_{uuid.uuid4().hex[:8]}"
    active_shop_id = current_user["shop_id"]

    # Transactional Atomic Execution
    try:
        total_amount = 0.0
        total_cost = 0.0
        sale_items_to_add = []

        # 1. Validation & Stock Check Pass
        for item in req.items:
            if item.quantity <= 0:
                raise HTTPException(
                    status_code=400, detail="Item quantity must be greater than 0."
                )

            product = (
                db.query(Product)
                .filter(
                    Product.id == item.product_id, Product.shop_id == active_shop_id
                )
                .first()
            )
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product with id '{item.product_id}' not found.",
                )

            inv = (
                db.query(Inventory)
                .filter(
                    Inventory.shop_id == active_shop_id,
                    Inventory.product_id == item.product_id,
                )
                .first()
            )

            current_qty = inv.quantity if inv else 0
            if item.quantity > current_qty:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for '{product.name}'. Available: {current_qty}, Requested: {item.quantity}.",
                )

            # Deterministic calculation using database prices
            sp = float(product.selling_price)
            cp = float(product.purchase_price)

            item_rev = round(item.quantity * sp, 2)
            item_cogs = round(item.quantity * cp, 2)
            item_profit = round(item_rev - item_cogs, 2)

            total_amount += item_rev
            total_cost += item_cogs

            new_qty = update_inventory_on_sale(current_qty, item.quantity)

            sale_items_to_add.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": sp,
                    "unit_cost": cp,
                    "profit": item_profit,
                    "inv_record": inv,
                    "new_qty": new_qty,
                }
            )

        total_amount = round(total_amount, 2)
        total_cost = round(total_cost, 2)
        profit = round(total_amount - total_cost, 2)

        # 2. Database Record & Inventory Decrement Pass
        sale = Sale(
            id=sale_id,
            shop_id=active_shop_id,
            total_amount=total_amount,
            total_cost=total_cost,
            profit=profit,
            source=req.source,
        )
        db.add(sale)

        for s_item in sale_items_to_add:
            si_id = f"si_{uuid.uuid4().hex[:8]}"
            db.add(
                SaleItem(
                    id=si_id,
                    sale_id=sale_id,
                    product_id=s_item["product_id"],
                    quantity=s_item["quantity"],
                    unit_price=s_item["unit_price"],
                    unit_cost=s_item["unit_cost"],
                    profit=s_item["profit"],
                )
            )
            s_item["inv_record"].quantity = s_item["new_qty"]

        db.commit()
        db.refresh(sale)

        margin_pct = (
            round((profit / total_amount * 100), 2) if total_amount > 0 else 0.0
        )

        return {
            "id": sale.id,
            "shop_id": sale.shop_id,
            "total_amount": float(sale.total_amount),
            "total_cost": float(sale.total_cost),
            "profit": float(sale.profit),
            "margin_pct": margin_pct,
            "source": sale.source,
            "created_at": sale.created_at,
            "items": [
                {
                    "id": si.id,
                    "product_id": si.product_id,
                    "product_name": si.product.name if si.product else None,
                    "quantity": si.quantity,
                    "unit_price": float(si.unit_price),
                    "unit_cost": float(si.unit_cost),
                    "profit": float(si.profit),
                }
                for si in sale.items
            ],
        }

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=400, detail=f"Sale transaction failed: {str(e)}"
        )


@router.get("", response_model=List[SaleResponse])
def list_sales_history(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    sales = (
        db.query(Sale)
        .filter(Sale.shop_id == current_user["shop_id"])
        .order_by(Sale.created_at.desc())
        .all()
    )
    result = []
    for s in sales:
        total = float(s.total_amount)
        profit = float(s.profit)
        margin = round((profit / total * 100), 2) if total > 0 else 0.0
        result.append(
            {
                "id": s.id,
                "shop_id": s.shop_id,
                "total_amount": total,
                "total_cost": float(s.total_cost),
                "profit": profit,
                "margin_pct": margin,
                "source": s.source,
                "created_at": s.created_at,
                "items": [
                    {
                        "id": si.id,
                        "product_id": si.product_id,
                        "product_name": si.product.name if si.product else None,
                        "quantity": si.quantity,
                        "unit_price": float(si.unit_price),
                        "unit_cost": float(si.unit_cost),
                        "profit": float(si.profit),
                    }
                    for si in s.items
                ],
            }
        )
    return result
