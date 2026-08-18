from typing import List, Dict, Any

def determine_stock_status(quantity: int, reorder_level: int) -> str:
    """
    Stock Status Rules:
    quantity <= 0 -> OUT_OF_STOCK
    quantity <= reorder_level -> LOW_STOCK
    otherwise -> HEALTHY
    """
    if quantity <= 0:
        return "OUT_OF_STOCK"
    elif quantity <= reorder_level:
        return "LOW_STOCK"
    else:
        return "HEALTHY"

def calculate_inventory_value(quantity: int, purchase_price: float) -> float:
    """
    Inventory Value = quantity * purchase_price
    """
    if quantity < 0 or purchase_price < 0:
        raise ValueError("Quantity and purchase price must be non-negative")
    return round(quantity * purchase_price, 2)

def calculate_item_financials(quantity: int, selling_price: float, purchase_price: float) -> Dict[str, float]:
    """
    Calculate financial metrics for a single item sale:
    Revenue = quantity * selling_price
    COGS = quantity * purchase_price
    Gross Profit = Revenue - COGS
    Margin % = (Gross Profit / Revenue * 100) if Revenue > 0 else 0.0
    """
    if quantity < 0:
        raise ValueError("Quantity cannot be negative")
    if selling_price < 0 or purchase_price < 0:
        raise ValueError("Prices cannot be negative")

    revenue = round(quantity * selling_price, 2)
    cogs = round(quantity * purchase_price, 2)
    gross_profit = round(revenue - cogs, 2)
    margin_pct = round((gross_profit / revenue * 100), 2) if revenue > 0 else 0.0

    return {
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "margin_pct": margin_pct
    }

def calculate_batch_financials(items: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate summary financials over a list of items.
    Each item is expected to have: quantity, selling_price, purchase_price.
    """
    total_revenue = 0.0
    total_cogs = 0.0

    for item in items:
        qty = item.get("quantity", 0)
        sp = item.get("selling_price", 0.0)
        cp = item.get("purchase_price", 0.0)

        res = calculate_item_financials(qty, sp, cp)
        total_revenue += res["revenue"]
        total_cogs += res["cogs"]

    total_revenue = round(total_revenue, 2)
    total_cogs = round(total_cogs, 2)
    gross_profit = round(total_revenue - total_cogs, 2)
    margin_pct = round((gross_profit / total_revenue * 100), 2) if total_revenue > 0 else 0.0

    return {
        "revenue": total_revenue,
        "cogs": total_cogs,
        "gross_profit": gross_profit,
        "margin_pct": margin_pct
    }

def update_inventory_on_purchase(current_quantity: int, purchased_quantity: int) -> int:
    """
    Purchase: inventory.quantity += purchased_quantity
    """
    if purchased_quantity <= 0:
        raise ValueError("Purchased quantity must be positive")
    return current_quantity + purchased_quantity

def update_inventory_on_sale(current_quantity: int, sold_quantity: int) -> int:
    """
    Sale: inventory.quantity -= sold_quantity
    Never allow negative inventory.
    """
    if sold_quantity <= 0:
        raise ValueError("Sold quantity must be positive")
    if sold_quantity > current_quantity:
        raise ValueError(f"Insufficient stock. Available: {current_quantity}, Requested: {sold_quantity}")
    return current_quantity - sold_quantity
