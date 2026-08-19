from app.api.deps import get_current_user
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from app.db.database import get_db
from app.db.models import Sale, SaleItem, Product, Inventory
from app.services.forecasting import calculate_forecast_for_product
from app.schemas.analytics import DashboardSummaryResponse, SlowMovingProductItem, ForecastItem

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_user)])

def build_product_forecast_internal(prod: Product, inv_qty: int, db: Session, today: date) -> ForecastItem:
    sales_query = db.query(
        func.date(Sale.created_at).label('sale_date'),
        func.sum(SaleItem.quantity).label('daily_qty')
    ).join(SaleItem, Sale.id == SaleItem.sale_id)\
     .filter(SaleItem.product_id == prod.id)\
     .group_by(func.date(Sale.created_at)).all()

    daily_sales_map = {}
    for r in sales_query:
        d_val = r.sale_date
        if isinstance(d_val, str):
            d_val = date.fromisoformat(d_val[:10])
        daily_sales_map[d_val] = int(r.daily_qty)

    calc = calculate_forecast_for_product(
        daily_sales=daily_sales_map,
        current_stock=inv_qty,
        reorder_level=prod.reorder_level,
        target_days=7,
        today=today
    )

    return ForecastItem(
        product_id=prod.id,
        name=prod.name,
        category=prod.category,
        current_stock=inv_qty,
        reorder_level=prod.reorder_level,
        forecast_status=calc["forecast_status"],
        forecast_daily_demand=calc["forecast_daily_demand"],
        days_of_stock=calc["days_of_stock"],
        stock_status=calc["stock_status"],
        reason=calc["reason"],
        planning_suggestion=calc["planning_suggestion"],
        explanation=calc["explanation"]
    )

@router.get("", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Expanded real database-backed dashboard summary.
    Every metric is derived deterministically from database records.
    """
    today = date.today()
    shop_id = current_user["shop_id"]

    sales = db.query(Sale).filter(Sale.shop_id == shop_id).all()
    today_rev = round(sum(float(s.total_amount) for s in sales), 2)
    today_cost = round(sum(float(s.total_cost) for s in sales), 2)
    today_profit = round(today_rev - today_cost, 2)
    today_margin = round((today_profit / today_rev * 100), 2) if today_rev > 0 else 0.0

    inventories = db.query(Inventory).filter(Inventory.shop_id == shop_id).all()
    products = db.query(Product).filter(Product.shop_id == shop_id).all()
    prod_map = {p.id: p for p in products}

    inventory_value = 0.0
    low_stock_count = 0
    out_of_stock_count = 0

    for inv in inventories:
        p = prod_map.get(inv.product_id)
        if p:
            cp = float(p.purchase_price)
            inventory_value += inv.quantity * cp
            if inv.quantity == 0:
                out_of_stock_count += 1
            elif inv.quantity <= p.reorder_level:
                low_stock_count += 1

    inventory_value = round(inventory_value, 2)

    perf_query = db.query(
        SaleItem.product_id,
        func.sum(SaleItem.quantity).label('units_sold'),
        func.sum(SaleItem.quantity * SaleItem.unit_price).label('revenue'),
        func.sum(SaleItem.profit).label('profit')
    ).join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.shop_id == shop_id)\
     .group_by(SaleItem.product_id).all()

    perf_map = {r.product_id: r for r in perf_query}

    top_selling = []
    for p in products:
        rec = perf_map.get(p.id)
        u_sold = int(rec.units_sold) if rec else 0
        rev = float(rec.revenue) if rec else 0.0
        prof = float(rec.profit) if rec else 0.0
        if u_sold > 0:
            top_selling.append({
                "product_id": p.id,
                "name": p.name,
                "category": p.category,
                "units_sold": u_sold,
                "revenue": round(rev, 2),
                "profit": round(prof, 2)
            })

    top_selling_sorted = sorted(top_selling, key=lambda x: x["units_sold"], reverse=True)[:5]
    profit_leaders_sorted = sorted(top_selling, key=lambda x: x["profit"], reverse=True)[:5]

    slow_moving = []
    for inv in inventories:
        p = prod_map.get(inv.product_id)
        if not p or inv.quantity == 0:
            continue

        rec = perf_map.get(p.id)
        u_sold_30d = int(rec.units_sold) if rec else 0
        velocity = round(u_sold_30d / 30.0, 2)

        last_sale = db.query(func.max(Sale.created_at))\
                      .join(SaleItem, Sale.id == SaleItem.sale_id)\
                      .filter(SaleItem.product_id == p.id).scalar()

        last_sale_str = last_sale.strftime('%Y-%m-%d') if last_sale else "Never"

        if u_sold_30d == 0:
            slow_moving.append(SlowMovingProductItem(
                product_id=p.id,
                name=p.name,
                current_stock=inv.quantity,
                units_sold_30d=0,
                velocity_per_day=0.0,
                last_sale_date=last_sale_str,
                reason="Zero sales recorded in historical database records.",
                status="SLOW_MOVING"
            ))
        elif velocity < 0.2 and inv.quantity > p.reorder_level:
            slow_moving.append(SlowMovingProductItem(
                product_id=p.id,
                name=p.name,
                current_stock=inv.quantity,
                units_sold_30d=u_sold_30d,
                velocity_per_day=velocity,
                last_sale_date=last_sale_str,
                reason=f"Low sales velocity ({velocity} units/day) relative to stock level ({inv.quantity} units).",
                status="SLOW_MOVING"
            ))

    reorder_suggestions = []
    for inv in inventories:
        p = prod_map.get(inv.product_id)
        if p:
            fc = build_product_forecast_internal(p, inv.quantity, db, today)
            if fc.stock_status in ["OUT_OF_STOCK", "LOW_STOCK", "AT_RISK"] or fc.planning_suggestion.recommended_purchase > 0:
                reorder_suggestions.append(fc)

    reorder_suggestions.sort(key=lambda x: x.planning_suggestion.recommended_purchase, reverse=True)

    return DashboardSummaryResponse(
        shop_id=shop_id,
        today_revenue=today_rev,
        today_sales=today_rev,
        today_profit=today_profit,
        today_margin=today_margin,
        inventory_value=inventory_value,
        total_products=len(products),
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        top_selling_products=top_selling_sorted,
        profit_leaders=profit_leaders_sorted,
        slow_moving_products=slow_moving[:5],
        reorder_suggestions=reorder_suggestions[:5]
    )
