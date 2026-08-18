import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.services.analytics import (
    calculate_item_financials,
    calculate_batch_financials,
    update_inventory_on_purchase,
    update_inventory_on_sale,
    determine_stock_status,
    calculate_inventory_value
)
from app.services.forecasting import calculate_stockout_risk

client = TestClient(app)

# 1. Pure Function & Unit Tests
def test_financial_calculations():
    res = calculate_item_financials(3, 20.00, 15.00)
    assert res["revenue"] == 60.00
    assert res["cogs"] == 45.00
    assert res["gross_profit"] == 15.00
    assert res["margin_pct"] == 25.00

def test_batch_financials():
    items = [
        {"quantity": 3, "selling_price": 20.00, "purchase_price": 15.00},
        {"quantity": 2, "selling_price": 27.00, "purchase_price": 24.00},
    ]
    batch = calculate_batch_financials(items)
    assert batch["revenue"] == 114.00
    assert batch["cogs"] == 93.00
    assert batch["gross_profit"] == 21.00
    assert round(batch["margin_pct"], 2) == 18.42

def test_purchase_increases_inventory_unit():
    assert update_inventory_on_purchase(10, 50) == 60

def test_sale_decreases_inventory_unit():
    assert update_inventory_on_sale(20, 5) == 15

def test_negative_inventory_prevention_unit():
    with pytest.raises(ValueError) as exc_info:
        update_inventory_on_sale(5, 10)
    assert "Insufficient stock" in str(exc_info.value)

def test_stockout_risk_unit():
    res = calculate_stockout_risk(6, 18.0)
    assert res["days_of_stock"] == 0.3
    assert res["risk_level"] == "HIGH"

def test_low_stock_calculation():
    assert determine_stock_status(8, 10) == "LOW_STOCK"
    assert determine_stock_status(10, 10) == "LOW_STOCK"

def test_out_of_stock_calculation():
    assert determine_stock_status(0, 10) == "OUT_OF_STOCK"
    assert determine_stock_status(-2, 10) == "OUT_OF_STOCK"
    assert determine_stock_status(15, 10) == "HEALTHY"

def test_inventory_value_calculation():
    assert calculate_inventory_value(10, 25.50) == 255.00
    assert calculate_inventory_value(0, 50.00) == 0.00


# 2. Integration Tests via API Client (Products, Inventory, Purchases, Dashboard)

def test_create_and_retrieve_product():
    payload = {
        "name": "Test Orange Juice 1L",
        "category": "Beverages",
        "brand": "Tropicana",
        "unit": "pack",
        "purchase_price": 45.00,
        "selling_price": 60.00,
        "reorder_level": 15
    }
    res = client.post("/api/products", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Test Orange Juice 1L"
    prod_id = data["id"]

    res_list = client.get("/api/products")
    assert res_list.status_code == 200
    products = res_list.json()
    assert any(p["id"] == prod_id for p in products)

    res_single = client.get(f"/api/products/{prod_id}")
    assert res_single.status_code == 200
    assert res_single.json()["name"] == "Test Orange Juice 1L"

def test_update_product():
    payload = {
        "name": "Test Biscuit Pack",
        "category": "Snacks",
        "purchase_price": 10.00,
        "selling_price": 15.00,
        "reorder_level": 5
    }
    res = client.post("/api/products", json=payload)
    prod_id = res.json()["id"]

    update_payload = {
        "name": "Test Premium Biscuit Pack",
        "selling_price": 18.00
    }
    res_up = client.put(f"/api/products/{prod_id}", json=update_payload)
    assert res_up.status_code == 200
    updated_data = res_up.json()
    assert updated_data["name"] == "Test Premium Biscuit Pack"
    assert updated_data["selling_price"] == 18.00

def test_manual_purchase_increases_inventory_and_creates_records():
    inv_before = client.get("/api/inventory").json()
    item_before = next(i for i in inv_before if i["product_id"] == "prod_001")
    qty_before = item_before["quantity"]

    unique_inv_num = f"INV-MANUAL-{uuid.uuid4().hex[:6].upper()}"

    purchase_payload = {
        "shop_id": "shop_001",
        "supplier_name": "Test Supplier",
        "invoice_number": unique_inv_num,
        "items": [
            {
                "product_id": "prod_001",
                "quantity": 20,
                "unit_cost": 15.00
            }
        ]
    }

    res_purch = client.post("/api/purchases/manual", json=purchase_payload)
    assert res_purch.status_code in [200, 201]
    purch_data = res_purch.json()
    assert purch_data["status"] == "confirmed"

    inv_after = client.get("/api/inventory").json()
    item_after = next(i for i in inv_after if i["product_id"] == "prod_001")
    assert item_after["quantity"] == qty_before + 20

def test_purchase_transactional_rollback_on_invalid_item():
    purchase_payload = {
        "shop_id": "shop_001",
        "items": [
            {"product_id": "prod_002", "quantity": 10, "unit_cost": 16.00},
            {"product_id": "NON_EXISTENT_PROD_ID", "quantity": 5, "unit_cost": 10.00}
        ]
    }

    inv_before = client.get("/api/inventory").json()
    qty_before = next(i for i in inv_before if i["product_id"] == "prod_002")["quantity"]

    res_fail = client.post("/api/purchases/manual", json=purchase_payload)
    assert res_fail.status_code in [400, 404]

    inv_after = client.get("/api/inventory").json()
    qty_after = next(i for i in inv_after if i["product_id"] == "prod_002")["quantity"]
    assert qty_after == qty_before

def test_invalid_purchase_quantity_rejected():
    payload = {
        "shop_id": "shop_001",
        "items": [{"product_id": "prod_001", "quantity": -5, "unit_cost": 15.00}]
    }
    res = client.post("/api/purchases/manual", json=payload)
    assert res.status_code in [400, 422]

def test_dashboard_values_database_backed():
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    dash = res.json()

    assert "today_sales" in dash
    assert "today_profit" in dash
    assert "today_margin" in dash
    assert "inventory_value" in dash
    assert "total_products" in dash
    assert "low_stock_count" in dash
    assert "out_of_stock_count" in dash
    assert isinstance(dash["total_products"], int)
    assert dash["total_products"] > 0
    assert dash["inventory_value"] > 0
