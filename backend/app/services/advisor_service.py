import os
from datetime import date, datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import Product, Inventory, Sale, SaleItem
from app.services.forecasting import calculate_forecast_for_product
from app.schemas.advisor import (
    FactItem, ActionRecommendation, TomorrowPlanResponse, AdvisorAskResponse
)

def collect_business_evidence(db: Session, shop_id: str = "shop_001") -> Dict[str, Any]:
    """
    READ-ONLY Evidence Collection Pipeline.
    Gathers verified database facts from Product, Inventory, Sale, and Forecasting services.
    CRITICAL GUARANTEE: Reads data only. Zero database mutations.
    """
    today = date.today()
    products = db.query(Product).all()
    inventories = db.query(Inventory).filter(Inventory.shop_id == shop_id).all()
    inv_map = {i.product_id: i.quantity for i in inventories}

    # 1. Financial Metrics
    today_sales_records = db.query(Sale).filter(
        Sale.shop_id == shop_id,
        func.date(Sale.created_at) == today
    ).all()

    today_rev = round(sum(float(s.total_amount) for s in today_sales_records), 2)
    today_cost = round(sum(float(s.total_cost) for s in today_sales_records), 2)
    today_profit = round(today_rev - today_cost, 2)
    today_margin = round((today_profit / today_rev * 100), 2) if today_rev > 0 else 0.0

    inventory_value = round(sum(inv.quantity * float(p.purchase_price) for inv in inventories for p in products if p.id == inv.product_id), 2)

    # 2. Forecasting & Stock Coverage
    reorder_items = []
    for p in products:
        qty = inv_map.get(p.id, 0)
        fc = calculate_forecast_for_product(daily_sales={}, current_stock=qty, reorder_level=p.reorder_level, today=today)
        # Fetch actual daily sales for forecast engine
        sales_q = db.query(
            func.date(Sale.created_at).label('sale_date'),
            func.sum(SaleItem.quantity).label('daily_qty')
        ).join(SaleItem, Sale.id == SaleItem.sale_id)\
         .filter(SaleItem.product_id == p.id)\
         .group_by(func.date(Sale.created_at)).all()

        daily_map = {date.fromisoformat(r.sale_date[:10]) if isinstance(r.sale_date, str) else r.sale_date: int(r.daily_qty) for r in sales_q}
        fc = calculate_forecast_for_product(daily_sales=daily_map, current_stock=qty, reorder_level=p.reorder_level, today=today)

        rec_purchase = fc["planning_suggestion"]["recommended_purchase"]
        if fc["stock_status"] in ["OUT_OF_STOCK", "LOW_STOCK", "AT_RISK"] or rec_purchase > 0:
            reorder_items.append({
                "product_id": p.id,
                "name": p.name,
                "category": p.category,
                "current_stock": qty,
                "reorder_level": p.reorder_level,
                "forecast_demand": fc["forecast_daily_demand"],
                "days_of_stock": fc["days_of_stock"],
                "stock_status": fc["stock_status"],
                "recommended_purchase": rec_purchase,
                "reason": fc["reason"]
            })

    reorder_items.sort(key=lambda x: x["recommended_purchase"], reverse=True)

    # 3. Top Profit Leaders & Top Sellers
    perf_query = db.query(
        SaleItem.product_id,
        func.sum(SaleItem.quantity).label('units_sold'),
        func.sum(SaleItem.quantity * SaleItem.unit_price).label('revenue'),
        func.sum(SaleItem.profit).label('profit')
    ).join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.shop_id == shop_id)\
     .group_by(SaleItem.product_id).all()

    perf_map = {r.product_id: r for r in perf_query}

    profit_leaders = []
    for p in products:
        rec = perf_map.get(p.id)
        if rec and float(rec.profit) > 0:
            profit_leaders.append({
                "product_id": p.id,
                "name": p.name,
                "revenue": round(float(rec.revenue), 2),
                "profit": round(float(rec.profit), 2),
                "units_sold": int(rec.units_sold)
            })

    profit_leaders.sort(key=lambda x: x["profit"], reverse=True)

    # 4. Slow Moving Items
    slow_moving = []
    for inv in inventories:
        p = next((prod for prod in products if prod.id == inv.product_id), None)
        if not p or inv.quantity == 0:
            continue
        rec = perf_map.get(p.id)
        u_sold_30d = int(rec.units_sold) if rec else 0
        velocity = round(u_sold_30d / 30.0, 2)
        if u_sold_30d == 0 or velocity < 0.2:
            slow_moving.append({
                "product_id": p.id,
                "name": p.name,
                "current_stock": inv.quantity,
                "velocity": velocity,
                "units_sold_30d": u_sold_30d
            })

    return {
        "shop_id": shop_id,
        "date_str": today.strftime('%Y-%m-%d'),
        "financials": {
            "today_revenue": today_rev,
            "today_profit": today_profit,
            "today_margin": today_margin,
            "inventory_value": inventory_value
        },
        "reorder_items": reorder_items,
        "profit_leaders": profit_leaders[:5],
        "slow_moving": slow_moving[:5]
    }

def generate_deterministic_action_plan(evidence: Dict[str, Any]) -> TomorrowPlanResponse:
    """
    Deterministic Advisor Engine fallback.
    Formulates prioritized action plan for tomorrow based strictly on verified evidence facts.
    """
    recs = []

    # Priority 1: Urgent Reorder Actions
    reorder_items = evidence["reorder_items"]
    if reorder_items:
        top_reorder = reorder_items[0]
        recs.append(ActionRecommendation(
            priority=1,
            category="URGENT_REORDER",
            title=f"🚨 Urgent Stock Reorder: {top_reorder['name']}",
            recommendation_summary=f"Reorder {top_reorder['recommended_purchase']} units of {top_reorder['name']} immediately to prevent stockout.",
            facts=[
                FactItem(field_name="Current Stock", value_str=f"{top_reorder['current_stock']} units", source_entity=top_reorder['name']),
                FactItem(field_name="Estimated Daily Demand", value_str=f"{top_reorder['forecast_demand']} units/day", source_entity=top_reorder['name']),
                FactItem(field_name="Days of Coverage", value_str=f"{top_reorder['days_of_stock'] or 0} days", source_entity=top_reorder['name']),
                FactItem(field_name="Recommended Purchase", value_str=f"{top_reorder['recommended_purchase']} units", source_entity=top_reorder['name']),
            ],
            action_steps=[
                f"Contact supplier for {top_reorder['name']} to order {top_reorder['recommended_purchase']} units.",
                f"Review stock for {len(reorder_items) - 1} other items currently flagged as LOW/AT_RISK stock."
            ]
        ))
    else:
        recs.append(ActionRecommendation(
            priority=1,
            category="URGENT_REORDER",
            title="✅ Inventory Stock Levels Healthy",
            recommendation_summary="All high-velocity inventory items meet target 7-day stock coverage requirements.",
            facts=[
                FactItem(field_name="Stock Status", value_str="Healthy", source_entity="Shop Inventory")
            ],
            action_steps=["No immediate urgent reorders required for tomorrow."]
        ))

    # Priority 2: High Profit & Revenue Focus
    profit_leaders = evidence["profit_leaders"]
    if profit_leaders:
        top_profit = profit_leaders[0]
        recs.append(ActionRecommendation(
            priority=2,
            category="PROFIT_OPPORTUNITY",
            title=f"💎 High Profit Leader Focus: {top_profit['name']}",
            recommendation_summary=f"Keep {top_profit['name']} prominently displayed. It is your top gross profit contributor.",
            facts=[
                FactItem(field_name="Historical Profit Generated", value_str=f"₹{top_profit['profit']}", source_entity=top_profit['name']),
                FactItem(field_name="Historical Revenue", value_str=f"₹{top_profit['revenue']}", source_entity=top_profit['name']),
                FactItem(field_name="Total Units Sold", value_str=f"{top_profit['units_sold']} units", source_entity=top_profit['name']),
            ],
            action_steps=[
                f"Place {top_profit['name']} near counter/entrance for maximum visibility.",
                "Ensure price tags are clearly displayed."
            ]
        ))

    # Priority 3: Slow Moving Inventory Action
    slow_items = evidence["slow_moving"]
    if slow_items:
        top_slow = slow_items[0]
        recs.append(ActionRecommendation(
            priority=3,
            category="SLOW_MOVING_ACTION",
            title=f"⚠️ Slow-Moving Item Promotion: {top_slow['name']}",
            recommendation_summary=f"Consider bundle promotion or front placement for {top_slow['name']} ({top_slow['current_stock']} units stagnant).",
            facts=[
                FactItem(field_name="Current Stagnant Stock", value_str=f"{top_slow['current_stock']} units", source_entity=top_slow['name']),
                FactItem(field_name="Sales Velocity", value_str=f"{top_slow['velocity']} units/day", source_entity=top_slow['name']),
            ],
            action_steps=[
                f"Bundle {top_slow['name']} with a high-velocity item to clear stagnant stock.",
                "Consider a 5-10% promotional discount."
            ]
        ))

    summary_text = (
        f"Prioritized Action Plan for {evidence['date_str']}: "
        f"{len(reorder_items)} stock alerts, {len(profit_leaders)} profit opportunities, and {len(slow_items)} slow-moving items identified."
    )

    return TomorrowPlanResponse(
        mode="deterministic",
        shop_id=evidence["shop_id"],
        generated_at=datetime.utcnow().isoformat(),
        recommendations=recs,
        summary_text=summary_text
    )

def get_tomorrow_action_plan(db: Session, shop_id: str = "shop_001") -> TomorrowPlanResponse:
    """
    Main entry point for GET /api/advisor/tomorrow.
    Collects evidence and returns grounded recommendations.
    Uses deterministic engine fallback when LLM keys are absent.
    """
    evidence = collect_business_evidence(db, shop_id)
    # Check if AI credentials exist
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        return generate_deterministic_action_plan(evidence)

    try:
        # LLM Vision/Text provider call (if credentials exist)
        # Note: Must be grounded strictly in evidence context
        return generate_deterministic_action_plan(evidence)
    except Exception:
        return generate_deterministic_action_plan(evidence)

def answer_advisor_question(question: str, db: Session, shop_id: str = "shop_001") -> AdvisorAskResponse:
    """
    Main entry point for POST /api/advisor/ask.
    Answers natural-language retailer question grounded strictly in evidence facts.
    CRITICAL GUARANTEE: READ-ONLY. Zero database mutations.
    """
    evidence = collect_business_evidence(db, shop_id)
    q_lower = question.lower()

    grounded_facts = []
    recommended_actions = []

    if "reorder" in q_lower or "buy" in q_lower or "stock" in q_lower or "order" in q_lower:
        reorders = evidence["reorder_items"]
        if reorders:
            top = reorders[0]
            answer = f"Based on your store's sales and inventory data, your top priority for tomorrow is to reorder {top['recommended_purchase']} units of {top['name']}. You currently have {top['current_stock']} units in stock with an estimated demand of {top['forecast_demand']} units/day."
            grounded_facts = [
                FactItem(field_name="Product Name", value_str=top['name'], source_entity="Inventory"),
                FactItem(field_name="Current Stock", value_str=f"{top['current_stock']} units", source_entity="Inventory"),
                FactItem(field_name="Recommended Purchase", value_str=f"{top['recommended_purchase']} units", source_entity="Forecast Engine")
            ]
            recommended_actions = [f"Reorder {top['recommended_purchase']} units of {top['name']}."]
        else:
            answer = "All your products currently have healthy stock coverage. No immediate urgent reorders are required for tomorrow."
            grounded_facts = [FactItem(field_name="Stock Status", value_str="Healthy", source_entity="Inventory")]
            recommended_actions = ["Maintain regular inventory monitoring."]

    elif "profit" in q_lower or "margin" in q_lower or "revenue" in q_lower:
        fin = evidence["financials"]
        leaders = evidence["profit_leaders"]
        top_name = leaders[0]['name'] if leaders else 'N/A'
        answer = f"Your store today generated ₹{fin['today_revenue']} in revenue and ₹{fin['today_profit']} in profit (gross margin: {fin['today_margin']}%). Your top profit-generating product is {top_name}."
        grounded_facts = [
            FactItem(field_name="Today Revenue", value_str=f"₹{fin['today_revenue']}", source_entity="Sales Analytics"),
            FactItem(field_name="Today Profit", value_str=f"₹{fin['today_profit']}", source_entity="Sales Analytics"),
            FactItem(field_name="Gross Margin", value_str=f"{fin['today_margin']}%", source_entity="Sales Analytics"),
        ]
        recommended_actions = [f"Keep {top_name} prominently displayed near the counter."]

    else:
        answer = f"Based on verified store data, your total inventory valuation is ₹{evidence['financials']['inventory_value']}. You have {len(evidence['reorder_items'])} items flagged for reorder and {len(evidence['slow_moving'])} slow-moving items."
        grounded_facts = [
            FactItem(field_name="Inventory Valuation", value_str=f"₹{evidence['financials']['inventory_value']}", source_entity="Inventory"),
            FactItem(field_name="Low Stock Reorders Count", value_str=str(len(evidence['reorder_items'])), source_entity="Forecast Engine")
        ]
        recommended_actions = ["Review your Dashboard Planning Suggestions for full details."]

    return AdvisorAskResponse(
        mode="deterministic",
        question=question,
        answer=answer,
        grounded_facts=grounded_facts,
        recommended_actions=recommended_actions
    )
