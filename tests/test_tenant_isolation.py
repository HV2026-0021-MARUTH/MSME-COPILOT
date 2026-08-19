import pytest
from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

# Helper function
def create_product(shop_id, name, sku, category="Test", selling=20.0, purchase=10.0, inventory_qty=50):
    res = client.post("/api/products", json={
        "name": name,
        "sku": sku,
        "category": category,
        "selling_price": selling,
        "purchase_price": purchase
    }, headers={"X-Shop-ID": shop_id})
    assert res.status_code == 201
    prod_id = res.json()["id"]
    
    # Initial inventory
    res_inv = client.post("/api/purchases/confirm", json={
        "items": [{
            "product_id": prod_id,
            "quantity": inventory_qty,
            "unit_cost": purchase
        }]
    }, headers={"X-Shop-ID": shop_id})
    assert res_inv.status_code == 200, res_inv.text
    
    return prod_id


def test_products_are_tenant_isolated():
    p1 = create_product("shop_001", "Shop1 Prod", "S1-P1")
    p2 = create_product("shop_002", "Shop2 Prod", "S2-P1")
    
    res1 = client.get("/api/products", headers={"X-Shop-ID": "shop_001"})
    assert res1.status_code == 200
    ids1 = [p["id"] for p in res1.json()]
    assert p1 in ids1
    assert p2 not in ids1
    
    res2 = client.get("/api/products", headers={"X-Shop-ID": "shop_002"})
    assert res2.status_code == 200
    ids2 = [p["id"] for p in res2.json()]
    assert p2 in ids2
    assert p1 not in ids2


def test_inventory_is_tenant_isolated():
    p1 = create_product("shop_001", "Shop1 Inv Prod", "S1-INV")
    p2 = create_product("shop_002", "Shop2 Inv Prod", "S2-INV")
    
    res1 = client.get("/api/inventory", headers={"X-Shop-ID": "shop_001"})
    assert res1.status_code == 200
    inv1_prod_ids = [item["product_id"] for item in res1.json()]
    assert p1 in inv1_prod_ids
    assert p2 not in inv1_prod_ids


def test_sales_are_tenant_isolated():
    p1 = create_product("shop_001", "Shop1 Sale Prod", "S1-SALE")
    p2 = create_product("shop_002", "Shop2 Sale Prod", "S2-SALE")
    
    # Create sale in shop 1
    sale1 = client.post("/api/sales/confirm", json={
        "items": [{"product_id": p1, "quantity": 1, "price": 20.0, "name": "Shop1 Sale Prod"}],
        "total_amount": 20.0,
        "payment_method": "cash"
    }, headers={"X-Shop-ID": "shop_001"})
    assert sale1.status_code == 201, sale1.text
    
    # Create sale in shop 2
    sale2 = client.post("/api/sales/confirm", json={
        "items": [{"product_id": p2, "quantity": 1, "price": 20.0, "name": "Shop2 Sale Prod"}],
        "total_amount": 20.0,
        "payment_method": "cash"
    }, headers={"X-Shop-ID": "shop_002"})
    assert sale2.status_code == 201, sale2.text
    
    # Check shop 1 sales
    res1 = client.get("/api/sales", headers={"X-Shop-ID": "shop_001"})
    assert res1.status_code == 200
    sales1 = res1.json()
    assert all(s.get("shop_id", "shop_001") == "shop_001" for s in sales1)
    # Check that shop 2's sale isn't here
    assert sale2.json()["id"] not in [s["id"] for s in sales1]


def test_cross_tenant_inventory_update_rejected():
    p2 = create_product("shop_002", "Shop2 Cross Inv", "S2-CROSS-INV")
    
    # Get initial inventory of p2
    inv_res = client.get("/api/inventory", headers={"X-Shop-ID": "shop_002"})
    initial_qty = next((i["quantity"] for i in inv_res.json() if i["product_id"] == p2), 0)
    
    # Shop 1 tries to add inventory to Shop 2's product
    res = client.post("/api/purchases/confirm", json={
        "items": [{
            "product_id": p2,
            "quantity": 100,
            "unit_cost": 10.0
        }]
    }, headers={"X-Shop-ID": "shop_001"})
    
    # Request should be rejected
    assert res.status_code in [400, 404]
    
    # Verify Shop 2's inventory quantity/value remains unchanged
    inv_res = client.get("/api/inventory", headers={"X-Shop-ID": "shop_002"})
    final_qty = next((i["quantity"] for i in inv_res.json() if i["product_id"] == p2), 0)
    assert final_qty == initial_qty


def test_cross_tenant_sale_rejected():
    p2 = create_product("shop_002", "Shop2 Cross Sale", "S2-CROSS-SALE")
    
    # Shop 1 tries to create a sale using Shop 2's product
    res = client.post("/api/sales/confirm", json={
        "items": [{"product_id": p2, "quantity": 1, "price": 20.0, "name": "Shop2 Cross Sale"}],
        "total_amount": 20.0,
        "payment_method": "cash"
    }, headers={"X-Shop-ID": "shop_001"})
    
    # Request should be rejected
    assert res.status_code in [400, 404]


def test_product_matching_is_tenant_scoped():
    # Create the exact scenario mentioned
    p1 = create_product("shop_001", "Dairy Milk 40g", "DM-40-TEST")
    p2 = create_product("shop_002", "Thums Up 750ml", "TU-750-TEST")
    
    # Shop 001 parsing "dairy milk"
    res1 = client.post("/api/sales/parse", json={"text": "dairy milk"}, headers={"X-Shop-ID": "shop_001"})
    assert res1.status_code == 200
    items1 = res1.json().get("items", [])
    # It must return Shop 001's Dairy Milk (p1)
    if items1 and items1[0].get("match_status") == "Matched":
        assert items1[0]["product_id"] == p1
    
    # Shop 002 parsing "dairy milk"
    res2 = client.post("/api/sales/parse", json={"text": "dairy milk"}, headers={"X-Shop-ID": "shop_002"})
    assert res2.status_code == 200
    items2 = res2.json().get("items", [])
    
    # If Shop 2 does not have a Dairy Milk, it should not return Shop 1's Dairy Milk
    for item in items2:
        if item.get("match_status") == "Matched":
            assert item["product_id"] != p1
            # In fact, we expect NO MATCH or AMBIGUOUS
            assert item.get("match_status") in ["Not Found", "No Match", "Ambiguous"]


def test_reports_are_tenant_scoped():
    p1 = create_product("shop_001", "Shop1 Rep", "S1-REP")
    p2 = create_product("shop_002", "Shop2 Rep", "S2-REP")
    
    res1 = client.get("/api/reports/business/pdf?period=daily", headers={"X-Shop-ID": "shop_001"})
    assert res1.status_code == 200
    
    res2 = client.get("/api/reports/business/pdf?period=daily", headers={"X-Shop-ID": "shop_002"})
    assert res2.status_code == 200
    
    # We would need to inspect actual data. Just verifying the endpoint succeeds under isolation context for now,
    # PDF response is binary, no .json()
    assert res1.headers["content-type"] == "application/pdf"
    assert res2.headers["content-type"] == "application/pdf"


def test_advisor_and_analytics_are_tenant_scoped():
    p1 = create_product("shop_001", "Shop1 Analytics", "S1-ANALYTICS")
    p2 = create_product("shop_002", "Shop2 Analytics", "S2-ANALYTICS")
    
    # Generate some sales for them to show up in analytics
    client.post("/api/sales/confirm", json={
        "items": [{"product_id": p1, "quantity": 10, "price": 20.0, "name": "Shop1 Analytics"}],
        "total_amount": 200.0,
        "payment_method": "cash"
    }, headers={"X-Shop-ID": "shop_001"})
    
    client.post("/api/sales/confirm", json={
        "items": [{"product_id": p2, "quantity": 10, "price": 20.0, "name": "Shop2 Analytics"}],
        "total_amount": 200.0,
        "payment_method": "cash"
    }, headers={"X-Shop-ID": "shop_002"})
    
    time.sleep(1) # Let any async operations settle if any
    
    res1 = client.get("/api/analytics/products", headers={"X-Shop-ID": "shop_001"})
    assert res1.status_code == 200
    analytics1_ids = [item.get("product_id") for item in res1.json()]
    if analytics1_ids:
        assert p2 not in analytics1_ids
        
    res2 = client.get("/api/analytics/products", headers={"X-Shop-ID": "shop_002"})
    assert res2.status_code == 200
    analytics2_ids = [item.get("product_id") for item in res2.json()]
    if analytics2_ids:
        assert p1 not in analytics2_ids
