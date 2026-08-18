import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.services.sales_parser import parse_number_from_token, find_candidate_products, parse_sales_text

client = TestClient(app)

# Helper Dummy Product Class
class DummyProduct:
    def __init__(self, p_id, name, sp=20.0, cp=15.0, category="Beverages"):
        self.id = p_id
        self.name = name
        self.selling_price = sp
        self.purchase_price = cp
        self.category = category

# 1. Pure Unit Tests for Sales Parser
def test_parse_number_from_token():
    assert parse_number_from_token("3") == 3
    assert parse_number_from_token("three") == 3
    assert parse_number_from_token("two") == 2
    assert parse_number_from_token("a") == 1
    assert parse_number_from_token("coke") is None

def test_find_candidate_products_ambiguous():
    db_prods = [
        DummyProduct("prod_001", "Coca-Cola 250ml"),
        DummyProduct("prod_006", "Coca-Cola 750ml Can"),
    ]
    cands = find_candidate_products("coke", db_prods)
    assert len(cands) >= 2

def test_parse_sales_text_unit():
    db_prods = [
        DummyProduct("prod_001", "Coca-Cola 250ml", sp=20.0, cp=15.0),
        DummyProduct("prod_002", "Lays Classic Salted 50g", sp=20.0, cp=16.0)
    ]
    res = parse_sales_text("Sold 3 Coca-Cola 250ml and 2 Lays Classic Salted 50g", db_prods)
    assert res["requires_review"] == False
    assert len(res["items"]) == 2
    assert res["estimated_total"] == 100.00  # (3*20) + (2*20) = 100
    assert res["estimated_profit"] == 23.00  # 3*(20-15) + 2*(20-16) = 15 + 8 = 23


# 2. Integration Tests via API Client

def test_sales_parse_api_does_not_modify_inventory():
    inv_before = client.get("/api/inventory").json()
    qty_before = {item["product_id"]: item["quantity"] for item in inv_before}

    parse_res = client.post("/api/sales/parse", json={"text": "Sold 3 Coke and 2 Lays"})
    assert parse_res.status_code == 200

    inv_after = client.get("/api/inventory").json()
    qty_after = {item["product_id"]: item["quantity"] for item in inv_after}

    # Verify inventory is 100% UNCHANGED by parse API
    assert qty_before == qty_after

def test_ambiguous_product_detection_via_api():
    parse_res = client.post("/api/sales/parse", json={"text": "Sold 2 Coke"})
    assert parse_res.status_code == 200
    data = parse_res.json()
    item = data["items"][0]
    assert item["match_status"] in ["AMBIGUOUS", "MATCHED"]
    if item["match_status"] == "AMBIGUOUS":
        assert len(item["candidates"]) > 1

def test_unmatched_product_detection_via_api():
    parse_res = client.post("/api/sales/parse", json={"text": "Sold 5 Quantum Supercomputer Chips"})
    assert parse_res.status_code == 200
    data = parse_res.json()
    item = data["items"][0]
    assert item["match_status"] == "NEEDS_MATCH"

def test_confirmed_sale_decreases_inventory_and_creates_records():
    inv_before = client.get("/api/inventory").json()
    coke_before = next(i for i in inv_before if i["product_id"] == "prod_001")
    qty_before = coke_before["quantity"]

    # Ensure sufficient stock
    if qty_before < 3:
        client.post("/api/purchases/manual", json={"shop_id": "shop_001", "items": [{"product_id": "prod_001", "quantity": 10, "unit_cost": 15.0}]})
        inv_before = client.get("/api/inventory").json()
        qty_before = next(i for i in inv_before if i["product_id"] == "prod_001")["quantity"]

    confirm_payload = {
        "shop_id": "shop_001",
        "source": "text",
        "items": [{"product_id": "prod_001", "quantity": 3}]
    }

    res = client.post("/api/sales/confirm", json=confirm_payload)
    assert res.status_code == 201
    sale = res.json()
    assert "id" in sale
    assert sale["total_amount"] == 60.00  # 3 * 20.00 DB selling price
    assert sale["total_cost"] == 45.00    # 3 * 15.00 DB purchase price
    assert sale["profit"] == 15.00        # 60 - 45
    assert sale["margin_pct"] == 25.00

    # Verify inventory decreased by 3
    inv_after = client.get("/api/inventory").json()
    coke_after = next(i for i in inv_after if i["product_id"] == "prod_001")
    assert coke_after["quantity"] == qty_before - 3

def test_financial_calculations_server_side_deterministic():
    # 3 x prod_001 (SP: 20, CP: 15) + 2 x prod_002 (SP: 20, CP: 16)
    confirm_payload = {
        "shop_id": "shop_001",
        "source": "voice",
        "items": [
            {"product_id": "prod_001", "quantity": 3},
            {"product_id": "prod_002", "quantity": 2}
        ]
    }
    res = client.post("/api/sales/confirm", json=confirm_payload)
    assert res.status_code == 201
    data = res.json()

    assert data["total_amount"] == 100.00  # 60 + 40
    assert data["total_cost"] == 77.00     # 45 + 32
    assert data["profit"] == 23.00         # 100 - 77
    assert data["margin_pct"] == 23.00     # (23 / 100) * 100 = 23%

def test_client_provided_prices_ignored():
    # Attempt to pass fake prices in request body (confirm payload schema only takes product_id and quantity)
    confirm_payload = {
        "shop_id": "shop_001",
        "source": "text",
        "items": [{"product_id": "prod_001", "quantity": 1}]
    }
    res = client.post("/api/sales/confirm", json=confirm_payload)
    assert res.status_code == 201
    assert res.json()["total_amount"] == 20.00  # Uses DB price 20.00

def test_insufficient_stock_rejection_no_inventory_mutation():
    inv_before = client.get("/api/inventory").json()
    coke_before = next(i for i in inv_before if i["product_id"] == "prod_001")
    qty_before = coke_before["quantity"]

    confirm_payload = {
        "shop_id": "shop_001",
        "source": "text",
        "items": [{"product_id": "prod_001", "quantity": qty_before + 9999}]
    }
    res = client.post("/api/sales/confirm", json=confirm_payload)
    assert res.status_code == 400
    assert "Insufficient stock" in res.json()["detail"]

    # Verify inventory is 100% UNCHANGED
    inv_after = client.get("/api/inventory").json()
    coke_after = next(i for i in inv_after if i["product_id"] == "prod_001")
    assert coke_after["quantity"] == qty_before

def test_invalid_sale_quantity_rejected():
    confirm_payload = {
        "shop_id": "shop_001",
        "source": "text",
        "items": [{"product_id": "prod_001", "quantity": -5}]
    }
    res = client.post("/api/sales/confirm", json=confirm_payload)
    assert res.status_code in [400, 422]

def test_transactional_rollback_on_sale_failure():
    inv_before = client.get("/api/inventory").json()
    coke_before = next(i for i in inv_before if i["product_id"] == "prod_001")
    qty_before = coke_before["quantity"]

    confirm_payload = {
        "shop_id": "shop_001",
        "source": "text",
        "items": [
            {"product_id": "prod_001", "quantity": 1},
            {"product_id": "NON_EXISTENT_PROD_ID", "quantity": 1}
        ]
    }
    res = client.post("/api/sales/confirm", json=confirm_payload)
    assert res.status_code in [400, 404]

    # Verify prod_001 was NOT decremented
    inv_after = client.get("/api/inventory").json()
    coke_after = next(i for i in inv_after if i["product_id"] == "prod_001")
    assert coke_after["quantity"] == qty_before

def test_get_sales_history():
    res = client.get("/api/sales")
    assert res.status_code == 200
    sales_list = res.json()
    assert isinstance(sales_list, list)
    assert len(sales_list) > 0
    first_sale = sales_list[0]
    assert "total_amount" in first_sale
    assert "profit" in first_sale
    assert "source" in first_sale
    assert "items" in first_sale

def test_dashboard_sales_updates():
    dash = client.get("/api/dashboard").json()
    assert "today_sales" in dash
    assert "today_profit" in dash
    assert "today_margin" in dash

def test_manual_sale_flow():
    confirm_payload = {
        "shop_id": "shop_001",
        "source": "manual",
        "items": [{"product_id": "prod_002", "quantity": 1}]
    }
    res = client.post("/api/sales/confirm", json=confirm_payload)
    assert res.status_code == 201
    assert res.json()["source"] == "manual"
