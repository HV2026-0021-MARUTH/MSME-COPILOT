import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.services.forecasting import calculate_forecast_for_product

client = TestClient(app)

# 1. Pure Unit Tests for Deterministic Forecasting Engine

def test_forecasting_insufficient_data():
    daily_sales = {}  # No historical sales
    res = calculate_forecast_for_product(daily_sales, current_stock=10, reorder_level=5)
    assert res["forecast_status"] == "INSUFFICIENT_DATA"
    assert res["forecast_daily_demand"] == 0.0
    assert res["days_of_stock"] is None
    assert res["stock_status"] in ["NO_FORECAST", "HEALTHY"]
    assert res["planning_suggestion"]["title"] == "Planning Suggestion"

def test_forecasting_weighted_moving_average_calculation():
    today = date(2026, 8, 18)
    daily_sales = {}
    for i in range(30):
        d = today - timedelta(days=i)
        if i < 7:
            daily_sales[d] = 10
        elif i < 14:
            daily_sales[d] = 5
        else:
            daily_sales[d] = 2

    res = calculate_forecast_for_product(daily_sales, current_stock=15, reorder_level=5, today=today)
    assert res["forecast_status"] == "CALCULATED"
    assert res["forecast_daily_demand"] == 7.41
    assert res["days_of_stock"] == 2.02  # 15 / 7.41 = 2.02
    assert res["stock_status"] == "AT_RISK"  # days_of_stock < 3.0
    assert res["planning_suggestion"]["recommended_purchase"] > 0

def test_zero_demand_handling():
    today = date(2026, 8, 18)
    daily_sales = {today - timedelta(days=1): 0, today - timedelta(days=2): 0}
    res = calculate_forecast_for_product(daily_sales, current_stock=20, reorder_level=5, today=today)
    assert res["forecast_daily_demand"] == 0.0
    assert res["days_of_stock"] is None

def test_stock_risk_classification():
    today = date(2026, 8, 18)
    res_out = calculate_forecast_for_product({}, current_stock=0, reorder_level=5, today=today)
    assert res_out["stock_status"] == "OUT_OF_STOCK"

    res_low = calculate_forecast_for_product({}, current_stock=3, reorder_level=5, today=today)
    assert res_low["stock_status"] == "LOW_STOCK"

def test_planning_suggestion_reorder_calculation():
    today = date(2026, 8, 18)
    daily_sales = {today - timedelta(days=i): 10 for i in range(7)}
    res = calculate_forecast_for_product(daily_sales, current_stock=10, reorder_level=5, target_days=7, today=today)
    ps = res["planning_suggestion"]
    assert ps["title"] == "Planning Suggestion"
    assert ps["recommended_purchase"] > 0
    assert "reorder" in ps["reason"].lower() or "target" in ps["reason"].lower() or "purchase" in ps["reason"].lower()


# 2. Integration Tests via API Client

def test_dashboard_api_metrics():
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "today_sales" in data or "today_revenue" in data
    assert "today_profit" in data
    assert "inventory_value" in data
    assert "low_stock_count" in data
    assert "out_of_stock_count" in data
    assert "top_selling_products" in data
    assert "profit_leaders" in data

def test_sales_trend_api():
    res = client.get("/api/analytics/sales-trend?days=30")
    assert res.status_code == 200
    data = res.json()
    assert data["period_days"] == 30
    assert len(data["data"]) == 30
    assert "revenue" in data["data"][0]
    assert "profit" in data["data"][0]

def test_sales_trend_selectable_periods():
    for d in [7, 30, 90]:
        res = client.get(f"/api/analytics/sales-trend?days={d}")
        assert res.status_code == 200
        assert len(res.json()["data"]) == d

def test_product_performance_api():
    res = client.get("/api/analytics/products")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    assert len(items) > 0
    first = items[0]
    assert "units_sold" in first
    assert "revenue" in first
    assert "margin_pct" in first
    assert "stock_status" in first

def test_demand_forecast_api():
    res = client.get("/api/analytics/forecast")
    assert res.status_code == 200
    data = res.json()
    assert "forecasts" in data
    assert len(data["forecasts"]) > 0
    first_fc = data["forecasts"][0]
    assert "forecast_status" in first_fc
    assert "planning_suggestion" in first_fc

def test_product_detail_analytics_api():
    res = client.get("/api/analytics/products/prod_001")
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == "prod_001"
    assert "inventory_value" in data
    assert "margin_pct" in data
    assert "forecast" in data

def test_product_detail_analytics_not_found():
    res = client.get("/api/analytics/products/NON_EXISTENT_PRODUCT")
    assert res.status_code == 404

def test_slow_moving_products_in_dashboard():
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "slow_moving_products" in data
    assert isinstance(data["slow_moving_products"], list)
