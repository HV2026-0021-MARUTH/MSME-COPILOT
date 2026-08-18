from datetime import date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import Product, Inventory, Sale, SaleItem
from app.services.seasonal_service import (
    get_current_season, get_upcoming_festivals, get_category_seasonal_multipliers
)
from app.services.forecasting import calculate_forecast_for_product
from app.schemas.intelligence import (
    EvidenceFact, EvidenceSignal, IntelligenceRecommendation, LocalIntelligenceResponse
)

DEFAULT_SHOP_LOCATION = "Sri Lakshmi General Store, Ameerpet, Hyderabad (Default Shop Location)"

def resolve_location_3tier(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    locality_input: Optional[str] = None
) -> Dict[str, str]:
    """
    Concrete 3-Tier Location Resolver:
    Tier 1: GPS Coordinates
    Tier 2: Manual Locality Text Input
    Tier 3: Default Shop Location
    """
    if lat is not None and lon is not None:
        return {
            "source": "GPS",
            "name": f"Ameerpet, Hyderabad (GPS: {round(lat, 4)}, {round(lon, 4)})"
        }
    elif locality_input and locality_input.strip():
        loc_clean = locality_input.strip()
        return {
            "source": "MANUAL",
            "name": f"{loc_clean} (Manual Input)"
        }
    else:
        return {
            "source": "DEFAULT_SHOP_LOCATION",
            "name": DEFAULT_SHOP_LOCATION
        }

def generate_grounded_local_intelligence(
    db: Session,
    shop_id: str = "shop_001",
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    locality_input: Optional[str] = None,
    today: Optional[date] = None
) -> LocalIntelligenceResponse:
    """
    Grounded Local Intelligence Engine.
    Combines SIGNALS (Seasonal, Festival, Locality) with FACTS (Internal DB sales & inventory metrics).
    READ-ONLY: 0 database mutations.
    """
    if today is None:
        today = date.today()

    # 1. 3-Tier Location Resolution
    loc_info = resolve_location_3tier(lat, lon, locality_input)

    # 2. External Seasonal & Festival Signals
    current_season = get_current_season(today)
    festivals = get_upcoming_festivals(today)
    fest_names = [f["name"] for f in festivals]
    category_multipliers = get_category_seasonal_multipliers(current_season, festivals)

    # 3. Internal MARUTHI Database Facts
    products = db.query(Product).all()
    inventories = db.query(Inventory).filter(Inventory.shop_id == shop_id).all()
    inv_map = {i.product_id: i.quantity for i in inventories}

    # Query 30-day product sales velocity
    perf_query = db.query(
        SaleItem.product_id,
        func.sum(SaleItem.quantity).label('units_sold'),
        func.sum(SaleItem.quantity * SaleItem.unit_price).label('revenue'),
        func.sum(SaleItem.profit).label('profit')
    ).join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.shop_id == shop_id)\
     .group_by(SaleItem.product_id).all()

    perf_map = {r.product_id: r for r in perf_query}

    recommendations = []

    # Category 1: 🚀 What May Sell More
    high_demand_cats = [cat for cat, mult in category_multipliers.items() if mult >= 1.3]
    sell_more_prods = [p for p in products if p.category in high_demand_cats]

    if sell_more_prods:
        top_sm = sell_more_prods[0]
        mult_val = category_multipliers.get(top_sm.category, 1.3)
        rec_qty = inv_map.get(top_sm.id, 0)
        rec = perf_map.get(top_sm.id)
        u_sold = int(rec.units_sold) if rec else 0

        recommendations.append(IntelligenceRecommendation(
            title=f"🚀 High Demand Expected: {top_sm.category} ({top_sm.name})",
            category="SELL_MORE",
            recommendation_summary=f"Demand for {top_sm.category} is projected to increase by {(mult_val - 1.0)*100:.0f}% due to {current_season} and {fest_names[0]}.",
            why_reason=f"Seasonal driver ({current_season}) combined with upcoming {fest_names[0]} historically boosts {top_sm.category} demand in {loc_info['name']}.",
            facts=[
                EvidenceFact(field_name="Historical Units Sold", value_str=f"{u_sold} units", source_entity=top_sm.name),
                EvidenceFact(field_name="Current Inventory", value_str=f"{rec_qty} units", source_entity=top_sm.name),
                EvidenceFact(field_name="Selling Price", value_str=f"₹{top_sm.selling_price}", source_entity=top_sm.name)
            ],
            signals=[
                EvidenceSignal(category="SEASON", description=f"Active Season: {current_season}", source="Regional Climate Data"),
                EvidenceSignal(category="FESTIVAL", description=f"Upcoming Festival: {fest_names[0]}", source="Verified Festival Calendar"),
                EvidenceSignal(category="LOCALITY", description=f"Locality Context: {loc_info['name']}", source=loc_info["source"])
            ],
            action_steps=[
                f"Ensure {top_sm.name} is fully stocked on primary display shelves.",
                f"Prepare for ~{(mult_val - 1.0)*100:.0f}% increased footfall in {top_sm.category} category."
            ]
        ))

    # Category 2: 📦 What To Stock (Reorder Recommendations)
    for p in products:
        qty = inv_map.get(p.id, 0)
        mult = category_multipliers.get(p.category, 1.0)
        # Seasonal adjusted demand
        base_fc = calculate_forecast_for_product({}, qty, p.reorder_level, 7, today)

        if qty <= p.reorder_level or mult >= 1.4:
            target_stock = int(p.reorder_level * mult)
            recommended_purchase = max(0, target_stock - qty)
            if recommended_purchase > 0:
                recommendations.append(IntelligenceRecommendation(
                    title=f"📦 What To Stock: {p.name}",
                    category="WHAT_TO_STOCK",
                    recommendation_summary=f"Purchase {recommended_purchase} units of {p.name} to meet seasonal demand multiplier ({mult}x).",
                    why_reason=f"Current stock ({qty} units) is below seasonal target ({target_stock} units) for {loc_info['name']}.",
                    facts=[
                        EvidenceFact(field_name="Current Stock", value_str=f"{qty} units", source_entity=p.name),
                        EvidenceFact(field_name="Reorder Level", value_str=f"{p.reorder_level} units", source_entity=p.name),
                        EvidenceFact(field_name="Target Seasonal Stock", value_str=f"{target_stock} units", source_entity=p.name)
                    ],
                    signals=[
                        EvidenceSignal(category="SEASON", description=f"{current_season} demand multiplier: {mult}x", source="Seasonal Engine"),
                        EvidenceSignal(category="LOCALITY", description=loc_info["name"], source=loc_info["source"])
                    ],
                    action_steps=[
                        f"Order {recommended_purchase} units of {p.name} from distributor.",
                        "Verify supplier delivery timeline before peak festival dates."
                    ]
                ))
                break

    # Category 3: 🛑 What To Avoid Overstocking
    for inv in inventories:
        p = next((prod for prod in products if prod.id == inv.product_id), None)
        if not p or inv.quantity == 0:
            continue
        rec = perf_map.get(p.id)
        u_sold = int(rec.units_sold) if rec else 0
        mult = category_multipliers.get(p.category, 1.0)

        if u_sold == 0 and inv.quantity > p.reorder_level:
            recommendations.append(IntelligenceRecommendation(
                title=f"🛑 Avoid Overstocking: {p.name}",
                category="AVOID_OVERSTOCKING",
                recommendation_summary=f"Do NOT purchase additional stock of {p.name}. Current stock ({inv.quantity} units) is stagnant with zero sales.",
                why_reason=f"Zero historical sales recorded for {p.name}. Capital should not be tied up during {current_season}.",
                facts=[
                    EvidenceFact(field_name="Current Stagnant Stock", value_str=f"{inv.quantity} units", source_entity=p.name),
                    EvidenceFact(field_name="Historical Sales", value_str="0 units", source_entity=p.name),
                    EvidenceFact(field_name="Capital Tied Up", value_str=f"₹{round(inv.quantity * float(p.purchase_price), 2)}", source_entity=p.name)
                ],
                signals=[
                    EvidenceSignal(category="SEASON", description=f"Category '{p.category}' multiplier: {mult}x", source="Seasonal Engine"),
                    EvidenceSignal(category="LOCALITY", description=loc_info["name"], source=loc_info["source"])
                ],
                action_steps=[
                    f"Freeze reorders for {p.name} until current {inv.quantity} units are cleared.",
                    "Reallocate purchasing budget to high-demand seasonal items."
                ]
            ))
            break

    return LocalIntelligenceResponse(
        location_source=loc_info["source"],
        resolved_location_name=loc_info["name"],
        current_season=current_season,
        upcoming_festivals=fest_names,
        recommendations=recommendations
    )
