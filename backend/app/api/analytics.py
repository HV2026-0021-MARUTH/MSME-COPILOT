from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List, Dict, Any

from app.db.database import get_db
from app.db.models import Product, Inventory, Sale, SaleItem
from app.services.forecasting import calculate_forecast_for_product
from app.schemas.analytics import (
    DashboardSummaryResponse, SalesTrendResponse, SalesTrendPoint,
    ProductPerformanceItem, SlowMovingProductItem, ForecastItem,
    ForecastResponse, ProductDetailAnalytics
)

router = APIRouter(prefix="/api", tags=["Analytics & Business Intelligence"])

def build_product_forecast(prod: Product, inv_qty: int, db: Session, today: date) -> ForecastItem:
    """Helper to extract daily sales and compute product forecast."""
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

@router.get("/dashboard", response_model=DashboardSummaryResponse)
def get_dashboard_analytics(shop_id: str = "shop_001", db: Session = Depends(get_db)):
    """
    Expanded real database-backed dashboard analytics.
    Every number comes from database query aggregations.
    """
    today = date.today()

    # 1. Today's Financial Summary
    today_sales_records = db.query(Sale).filter(
        Sale.shop_id == shop_id,
        func.date(Sale.created_at) == today
    ).all()

    today_rev = round(sum(float(s.total_amount) for s in today_sales_records), 2)
    today_cost = round(sum(float(s.total_cost) for s in today_sales_records), 2)
    today_profit = round(today_rev - today_cost, 2)
    today_margin = round((today_profit / today_rev * 100), 2) if today_rev > 0 else 0.0

    # 2. Inventory Summaries
    inventories = db.query(Inventory).filter(Inventory.shop_id == shop_id).all()
    products = db.query(Product).all()
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

    # 3. Product Sales Performance Aggregations
    perf_query = db.query(
        SaleItem.product_id,
        func.sum(SaleItem.quantity).label('units_sold'),
        func.sum(SaleItem.quantity * SaleItem.unit_price).label('revenue'),
        func.sum(SaleItem.profit).label('profit')
    ).join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.shop_id == shop_id)\
     .group_by(SaleItem.product_id).all()

    perf_map = {r.product_id: r for r in perf_query}

    # Top Selling Products (by Units Sold)
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

    # 4. Slow Moving Products Logic
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

    # 5. Reorder Suggestions & Forecasts
    reorder_suggestions = []
    for inv in inventories:
        p = prod_map.get(inv.product_id)
        if p:
            fc = build_product_forecast(p, inv.quantity, db, today)
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

@router.get("/analytics/sales-trend", response_model=SalesTrendResponse)
def get_sales_trend(
    days: int = Query(30, ge=7, le=90),
    shop_id: str = "shop_001",
    db: Session = Depends(get_db)
):
    """
    Daily sales trend over a selectable period (7, 30, or 90 days).
    Queries real daily aggregations from DB sales table.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    daily_query = db.query(
        func.date(Sale.created_at).label('sale_date'),
        func.sum(Sale.total_amount).label('revenue'),
        func.sum(Sale.total_cost).label('cost'),
        func.sum(Sale.profit).label('profit')
    ).filter(
        Sale.shop_id == shop_id,
        func.date(Sale.created_at) >= start_date,
        func.date(Sale.created_at) <= end_date
    ).group_by(func.date(Sale.created_at)).all()

    daily_map = {}
    for r in daily_query:
        d_str = r.sale_date[:10] if isinstance(r.sale_date, str) else r.sale_date.strftime('%Y-%m-%d')
        daily_map[d_str] = {
            "revenue": round(float(r.revenue), 2),
            "cost": round(float(r.cost), 2),
            "profit": round(float(r.profit), 2)
        }

    units_query = db.query(
        func.date(Sale.created_at).label('sale_date'),
        func.sum(SaleItem.quantity).label('units_sold')
    ).join(SaleItem, Sale.id == SaleItem.sale_id)\
     .filter(
        Sale.shop_id == shop_id,
        func.date(Sale.created_at) >= start_date,
        func.date(Sale.created_at) <= end_date
    ).group_by(func.date(Sale.created_at)).all()

    units_map = {}
    for r in units_query:
        d_str = r.sale_date[:10] if isinstance(r.sale_date, str) else r.sale_date.strftime('%Y-%m-%d')
        units_map[d_str] = int(r.units_sold)

    trend_points = []
    total_rev = 0.0
    total_prof = 0.0
    total_u = 0

    curr = start_date
    while curr <= end_date:
        d_str = curr.strftime('%Y-%m-%d')
        val = daily_map.get(d_str, {"revenue": 0.0, "cost": 0.0, "profit": 0.0})
        u_count = units_map.get(d_str, 0)

        trend_points.append(SalesTrendPoint(
            date=d_str,
            revenue=val["revenue"],
            cost=val["cost"],
            profit=val["profit"],
            units_sold=u_count
        ))

        total_rev += val["revenue"]
        total_prof += val["profit"]
        total_u += u_count
        curr += timedelta(days=1)

    return SalesTrendResponse(
        period_days=days,
        data=trend_points,
        total_revenue=round(total_rev, 2),
        total_profit=round(total_prof, 2),
        total_units=total_u
    )

@router.get("/analytics/products", response_model=List[ProductPerformanceItem])
def get_product_performance(shop_id: str = "shop_001", db: Session = Depends(get_db)):
    today = date.today()
    products = db.query(Product).all()
    inventories = db.query(Inventory).filter(Inventory.shop_id == shop_id).all()
    inv_map = {i.product_id: i.quantity for i in inventories}

    perf_query = db.query(
        SaleItem.product_id,
        func.sum(SaleItem.quantity).label('units_sold'),
        func.sum(SaleItem.quantity * SaleItem.unit_price).label('revenue'),
        func.sum(SaleItem.quantity * SaleItem.unit_cost).label('cost'),
        func.sum(SaleItem.profit).label('profit')
    ).join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.shop_id == shop_id)\
     .group_by(SaleItem.product_id).all()

    perf_map = {r.product_id: r for r in perf_query}

    result = []
    for p in products:
        qty = inv_map.get(p.id, 0)
        rec = perf_map.get(p.id)

        u_sold = int(rec.units_sold) if rec else 0
        rev = float(rec.revenue) if rec else 0.0
        cost = float(rec.cost) if rec else 0.0
        prof = float(rec.profit) if rec else 0.0
        margin = round((prof / rev * 100), 2) if rev > 0 else 0.0
        inv_val = round(qty * float(p.purchase_price), 2)

        fc = build_product_forecast(p, qty, db, today)

        result.append(ProductPerformanceItem(
            product_id=p.id,
            name=p.name,
            category=p.category,
            brand=p.brand,
            selling_price=float(p.selling_price),
            purchase_price=float(p.purchase_price),
            units_sold=u_sold,
            revenue=round(rev, 2),
            cost=round(cost, 2),
            profit=round(prof, 2),
            margin_pct=margin,
            current_stock=qty,
            inventory_value=inv_val,
            reorder_level=p.reorder_level,
            average_daily_demand=fc.forecast_daily_demand,
            days_of_stock=fc.days_of_stock,
            stock_status=fc.stock_status
        ))

    return result

@router.get("/analytics/forecast", response_model=ForecastResponse)
def get_demand_forecasts(shop_id: str = "shop_001", db: Session = Depends(get_db)):
    today = date.today()
    products = db.query(Product).all()
    inventories = db.query(Inventory).filter(Inventory.shop_id == shop_id).all()
    inv_map = {i.product_id: i.quantity for i in inventories}

    forecasts = []
    for p in products:
        qty = inv_map.get(p.id, 0)
        fc = build_product_forecast(p, qty, db, today)
        forecasts.append(fc)

    return ForecastResponse(
        shop_id=shop_id,
        total_products=len(forecasts),
        forecasts=forecasts
    )

@router.get("/analytics/products/{product_id}", response_model=ProductDetailAnalytics)
def get_product_detail_analytics(product_id: str, shop_id: str = "shop_001", db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")

    inv = db.query(Inventory).filter(Inventory.shop_id == shop_id, Inventory.product_id == product_id).first()
    qty = inv.quantity if inv else 0
    sp = float(prod.selling_price)
    cp = float(prod.purchase_price)

    agg = db.query(
        func.sum(SaleItem.quantity).label('units_sold'),
        func.sum(SaleItem.quantity * SaleItem.unit_price).label('revenue'),
        func.sum(SaleItem.quantity * SaleItem.unit_cost).label('cost'),
        func.sum(SaleItem.profit).label('profit')
    ).join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.shop_id == shop_id, SaleItem.product_id == product_id).first()

    u_sold = int(agg.units_sold) if agg and agg.units_sold else 0
    rev = float(agg.revenue) if agg and agg.revenue else 0.0
    cost = float(agg.cost) if agg and agg.cost else 0.0
    prof = float(agg.profit) if agg and agg.profit else 0.0
    margin = round((prof / rev * 100), 2) if rev > 0 else 0.0

    today = date.today()
    fc = build_product_forecast(prod, qty, db, today)

    recent_sales_records = db.query(SaleItem, Sale)\
        .join(Sale, Sale.id == SaleItem.sale_id)\
        .filter(SaleItem.product_id == product_id)\
        .order_by(Sale.created_at.desc()).limit(10).all()

    recent_sales_list = [
        {
            "sale_id": s.Sale.id,
            "date": s.Sale.created_at.strftime('%Y-%m-%d %H:%M'),
            "quantity": s.SaleItem.quantity,
            "unit_price": float(s.SaleItem.unit_price),
            "total": round(s.SaleItem.quantity * float(s.SaleItem.unit_price), 2),
            "source": s.Sale.source
        }
        for s in recent_sales_records
    ]

    return ProductDetailAnalytics(
        product_id=prod.id,
        name=prod.name,
        category=prod.category,
        brand=prod.brand,
        unit=prod.unit,
        purchase_price=cp,
        selling_price=sp,
        reorder_level=prod.reorder_level,
        current_stock=qty,
        inventory_value=round(qty * cp, 2),
        units_sold_total=u_sold,
        revenue_total=round(rev, 2),
        cost_total=round(cost, 2),
        profit_total=round(prof, 2),
        margin_pct=margin,
        forecast=fc,
        recent_sales=recent_sales_list
    )
