import math
from datetime import date, timedelta
from typing import Dict, Any, List, Optional

def calculate_stockout_risk(current_stock: int, forecast_demand: float, days_threshold: int = 7) -> Dict[str, Any]:
    """
    Legacy helper for calculating stockout risk based on inventory and demand.
    Preserved for Phase 1 backwards compatibility.
    """
    if forecast_demand <= 0:
        return {
            "days_of_stock": None,
            "stockout_risk": "UNKNOWN" if current_stock > 0 else "OUT_OF_STOCK",
            "risk_level": "UNKNOWN" if current_stock > 0 else "OUT_OF_STOCK"
        }

    days_of_stock = round(current_stock / forecast_demand, 1)
    if current_stock == 0:
        risk = "OUT_OF_STOCK"
    elif days_of_stock < 3.0:
        risk = "HIGH"
    elif days_of_stock <= days_threshold:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return {
        "days_of_stock": days_of_stock,
        "stockout_risk": risk,
        "risk_level": risk
    }

def calculate_forecast_for_product(
    daily_sales: Dict[date, int],
    current_stock: int,
    reorder_level: int = 10,
    target_days: int = 7,
    today: Optional[date] = None
) -> Dict[str, Any]:
    """
    Pure, deterministic baseline demand forecasting engine.
    Calculates weighted moving average demand:
      forecast = 0.5 * 7d_avg + 0.3 * prev_7d_avg + 0.2 * 30d_avg

    CRITICAL RULE: Only uses historical windows that actually have recorded data.
    If historical data is sparse (< 2 days of records and total sales < 3), returns INSUFFICIENT_DATA.
    """
    if today is None:
        today = date.today()

    total_data_points = len(daily_sales)

    if not daily_sales or total_data_points == 0:
        if current_stock == 0:
            stock_status = "OUT_OF_STOCK"
        elif current_stock <= reorder_level:
            stock_status = "LOW_STOCK"
        else:
            stock_status = "NO_FORECAST"

        return {
            "forecast_status": "INSUFFICIENT_DATA",
            "reason": "No historical sales data available for this product.",
            "forecast_daily_demand": 0.0,
            "days_of_stock": None,
            "stock_status": stock_status,
            "planning_suggestion": {
                "title": "Planning Suggestion",
                "target_days": target_days,
                "target_stock": 0,
                "recommended_purchase": 0 if current_stock > reorder_level else reorder_level,
                "reason": "Insufficient sales history to calculate forecast. Reorder level fallback applies."
            },
            "explanation": {
                "recent_7d_avg": 0.0,
                "prev_7d_avg": 0.0,
                "recent_30d_avg": 0.0,
                "formula": "0.5 * 7d_avg + 0.3 * prev_7d_avg + 0.2 * 30d_avg",
                "data_points_count": 0
            }
        }

    # Sum sales across historical windows
    # Window 1: Recent 7 days (today - 6 days to today)
    r7_start = today - timedelta(days=6)
    r7_sales = [qty for d, qty in daily_sales.items() if r7_start <= d <= today]
    r7_avg = sum(r7_sales) / 7.0 if r7_sales else 0.0

    # Window 2: Previous 7 days (today - 13 days to today - 7 days)
    p7_start = today - timedelta(days=13)
    p7_end = today - timedelta(days=7)
    p7_sales = [qty for d, qty in daily_sales.items() if p7_start <= d <= p7_end]
    p7_avg = sum(p7_sales) / 7.0 if p7_sales else 0.0

    # Window 3: Recent 30 days (today - 29 days to today)
    r30_start = today - timedelta(days=29)
    r30_sales = [qty for d, qty in daily_sales.items() if r30_start <= d <= today]
    r30_avg = sum(r30_sales) / 30.0 if r30_sales else 0.0

    if total_data_points < 2 and sum(daily_sales.values()) < 3:
        forecast_status = "INSUFFICIENT_DATA"
        reason = f"Only {total_data_points} sales data point(s) recorded. Minimum 2 required for reliable forecast."
        forecast_daily_demand = round(r30_avg or r7_avg, 2)
    else:
        forecast_status = "CALCULATED"
        reason = "Sufficient historical data for weighted moving average forecast."
        forecast_daily_demand = round((0.5 * r7_avg) + (0.3 * p7_avg) + (0.2 * r30_avg), 2)

    # 1. Days of stock calculation
    if forecast_daily_demand == 0.0:
        days_of_stock = None
    else:
        days_of_stock = round(current_stock / forecast_daily_demand, 2)

    # 2. Stock risk classification
    if current_stock == 0:
        stock_status = "OUT_OF_STOCK"
    elif current_stock <= reorder_level:
        stock_status = "LOW_STOCK"
    elif days_of_stock is not None and days_of_stock < 3.0:
        stock_status = "AT_RISK"
    elif days_of_stock is not None:
        stock_status = "HEALTHY"
    else:
        stock_status = "NO_FORECAST"

    # 3. Deterministic Planning Suggestion
    target_stock = int(math.ceil(forecast_daily_demand * target_days))
    if forecast_status == "INSUFFICIENT_DATA" and target_stock == 0:
        target_stock = reorder_level

    recommended_purchase = max(0, target_stock - current_stock)

    planning_suggestion = {
        "title": "Planning Suggestion",
        "target_days": target_days,
        "target_stock": target_stock,
        "recommended_purchase": recommended_purchase,
        "reason": f"To maintain {target_days} days of stock coverage (target: {target_stock} units), purchase {recommended_purchase} units." if recommended_purchase > 0 else f"Current stock ({current_stock} units) satisfies target {target_days}-day demand."
    }

    return {
        "forecast_status": forecast_status,
        "reason": reason,
        "forecast_daily_demand": forecast_daily_demand,
        "days_of_stock": days_of_stock,
        "stock_status": stock_status,
        "planning_suggestion": planning_suggestion,
        "explanation": {
            "recent_7d_avg": round(r7_avg, 2),
            "prev_7d_avg": round(p7_avg, 2),
            "recent_30d_avg": round(r30_avg, 2),
            "formula": "0.5 * 7d_avg + 0.3 * prev_7d_avg + 0.2 * 30d_avg",
            "data_points_count": total_data_points
        }
    }
