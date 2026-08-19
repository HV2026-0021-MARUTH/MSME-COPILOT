import pytest
import io
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.services.invoice_parser import normalize_string, match_single_product, parse_invoice_image

client = TestClient(app)

# Helper Dummy Product Class
class DummyProduct:
    def __init__(self, p_id, name):
        self.id = p_id
        self.name = name

# 1. Unit Tests for Product Matching Logic
def test_normalize_string():
    assert normalize_string("Coca Cola 250 ML") == "coca cola 250 ml"
    assert normalize_string("Surf-Excel (Easy Wash) 500g!!") == "surf excel easy wash 500g"

def test_exact_product_matching():
    products = [DummyProduct("prod_001", "Coca-Cola 250ml")]
    res = match_single_product("Coca-Cola 250ml", products)
    assert res["match_status"] == "MATCHED"
    assert res["matched_product_id"] == "prod_001"
    assert res["confidence"] == 1.0

def test_normalized_product_matching():
    products = [DummyProduct("prod_001", "Coca-Cola 250ml")]
    res = match_single_product("Coca Cola 250 ML", products)
    assert res["match_status"] == "MATCHED"
    assert res["matched_product_id"] == "prod_001"
    assert res["confidence"] >= 0.85

def test_unmatched_product_detection():
    products = [DummyProduct("prod_001", "Coca-Cola 250ml")]
    res = match_single_product("Unknown Organic Green Tea 100g", products)
    assert res["match_status"] == "NEEDS_MATCH"
    assert res["matched_product_id"] is None


# 2. Integration Tests via API Client

def test_valid_invoice_upload():
    # Valid JPEG image upload
    fake_image = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x60\x00\x60\x00\x00\xFF\xD9"
    files = {"file": ("test_invoice.jpg", fake_image, "image/jpeg")}

    res = client.post("/api/purchases/invoice", files=files)
    assert res.status_code == 200
    data = res.json()

    assert "supplier" in data
    assert "invoice_number" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["mode"] in ["ai", "demo"]

def test_invalid_file_type_rejected():
    fake_txt = b"Hello world this is not an image"
    files = {"file": ("document.txt", fake_txt, "text/plain")}

    res = client.post("/api/purchases/invoice", files=files)
    assert res.status_code == 400
    assert "Unsupported file type" in res.json()["detail"]

def test_oversized_file_rejected():
    oversized_bytes = b"0" * (11 * 1024 * 1024)  # 11 MB
    files = {"file": ("large_invoice.jpg", oversized_bytes, "image/jpeg")}

    res = client.post("/api/purchases/invoice", files=files)
    assert res.status_code == 400
    assert "File size exceeds" in res.json()["detail"]

def test_invoice_upload_does_not_modify_inventory():
    # Check inventory before upload
    inv_before = client.get("/api/inventory").json()
    qty_before = {item["product_id"]: item["quantity"] for item in inv_before}

    # Upload invoice
    fake_image = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x60\x00\x60\x00\x00\xFF\xD9"
    files = {"file": ("test_invoice.jpg", fake_image, "image/jpeg")}
    res = client.post("/api/purchases/invoice", files=files)
    assert res.status_code == 200

    # Verify inventory after upload remains 100% UNCHANGED
    inv_after = client.get("/api/inventory").json()
    qty_after = {item["product_id"]: item["quantity"] for item in inv_after}

    assert qty_before == qty_after

def test_confirmed_invoice_modifies_inventory_and_creates_purchase():
    inv_before = client.get("/api/inventory").json()
    coke_item_before = next(i for i in inv_before if i["product_id"] == "prod_001")
    qty_before = coke_item_before["quantity"]

    unique_inv = f"INV-CONFIRM-{uuid.uuid4().hex[:6].upper()}"

    confirm_payload = {
        "shop_id": "shop_001",
        "supplier_name": "Sri Venkateswara Wholesale Depot",
        "invoice_number": unique_inv,
        "items": [
            {
                "product_id": "prod_001",
                "quantity": 12,
                "unit_cost": 15.00
            }
        ]
    }

    res_confirm = client.post("/api/purchases/confirm", json=confirm_payload)
    assert res_confirm.status_code in [200, 201]
    res_data = res_confirm.json()
    assert res_data["status"] == "confirmed"
    assert "purchase_id" in res_data

    # Verify inventory increased by 12
    inv_after = client.get("/api/inventory").json()
    coke_item_after = next(i for i in inv_after if i["product_id"] == "prod_001")
    assert coke_item_after["quantity"] == qty_before + 12

def test_transactional_rollback_on_invalid_confirm_item():
    inv_before = client.get("/api/inventory").json()
    coke_item_before = next(i for i in inv_before if i["product_id"] == "prod_001")
    qty_before = coke_item_before["quantity"]

    confirm_payload = {
        "shop_id": "shop_001",
        "supplier_name": "Supplier",
        "invoice_number": f"INV-FAIL-{uuid.uuid4().hex[:6].upper()}",
        "items": [
            {"product_id": "prod_001", "quantity": 10, "unit_cost": 15.00},
            {"product_id": "NON_EXISTENT_PROD_ID", "quantity": 5, "unit_cost": 10.00}
        ]
    }

    res_fail = client.post("/api/purchases/confirm", json=confirm_payload)
    assert res_fail.status_code in [400, 404]

    # Verify prod_001 quantity was NOT incremented (rolled back transactionally)
    inv_after = client.get("/api/inventory").json()
    coke_item_after = next(i for i in inv_after if i["product_id"] == "prod_001")
    assert coke_item_after["quantity"] == qty_before

def test_duplicate_invoice_detection():
    dup_inv_num = f"INV-DUP-{uuid.uuid4().hex[:6].upper()}"

    # First confirmation
    confirm_payload = {
        "shop_id": "shop_001",
        "supplier_name": "Supplier",
        "invoice_number": dup_inv_num,
        "items": [{"product_id": "prod_001", "quantity": 1, "unit_cost": 15.00}]
    }
    res1 = client.post("/api/purchases/confirm", json=confirm_payload)
    assert res1.status_code in [200, 201]

    # Second confirmation with same invoice number -> duplicate protection error
    res2 = client.post("/api/purchases/confirm", json=confirm_payload)
    assert res2.status_code == 400
    assert "Duplicate Invoice Protection" in res2.json()["detail"]

def test_invalid_quantity_and_cost_rejected():
    payload_bad_qty = {
        "shop_id": "shop_001",
        "items": [{"product_id": "prod_001", "quantity": -10, "unit_cost": 15.00}]
    }
    res_qty = client.post("/api/purchases/confirm", json=payload_bad_qty)
    assert res_qty.status_code in [400, 422]

    payload_bad_cost = {
        "shop_id": "shop_001",
        "items": [{"product_id": "prod_001", "quantity": 5, "unit_cost": -50.00}]
    }
    res_cost = client.post("/api/purchases/confirm", json=payload_bad_cost)
    assert res_cost.status_code in [400, 422]
