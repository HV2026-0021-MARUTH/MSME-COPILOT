import pytest
from fastapi.testclient import TestClient
from app.main import app
import pandas as pd
import io

client = TestClient(app)

def test_import_preview_csv():
    # Create dummy CSV
    csv_data = "Date,Product,Quantity,Price\n2026-08-01,Coca-Cola 250ml,10,20.00\n2026-08-01,New Product X,5,15.00"
    
    file_bytes = csv_data.encode('utf-8')
    response = client.post(
        "/api/import/preview",
        files={"file": ("test.csv", file_bytes, "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 2
    assert data["valid_rows"] == 2
    assert len(data["new_products"]) == 1
    assert data["new_products"][0] == "New Product X"
    
def test_import_preview_invalid_row():
    # Missing date and negative qty
    csv_data = "Date,Product,Quantity,Price\n,Coca-Cola 250ml,-5,20.00\n"
    
    file_bytes = csv_data.encode('utf-8')
    response = client.post(
        "/api/import/preview",
        files={"file": ("test2.csv", file_bytes, "text/csv")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 1
    assert data["invalid_rows"] == 1
    # Check errors
    errors = data["rows"][0]["errors"]
    assert any("Date is required" in e for e in errors)
    assert any("Quantity must be greater than zero" in e for e in errors)

def test_import_confirm():
    csv_data = "Date,Product,Quantity,Price\n2026-08-01,Coca-Cola 250ml,10,20.00\n2026-08-01,New Product Y,5,15.00"
    file_bytes = csv_data.encode('utf-8')
    preview_res = client.post(
        "/api/import/preview",
        files={"file": ("test3.csv", file_bytes, "text/csv")}
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    
    file_id = preview_data["file_id"]
    mapping = preview_data["mapped_columns"]
    
    payload = {
        "shop_id": "shop_001",
        "file_id": file_id,
        "mapping": mapping,
        "create_new_products": True,
        "new_products_info": [
            {
                "name": "New Product Y",
                "category": "Uncategorized",
                "selling_price": 15.0,
                "purchase_price": 10.0,
                "unit": "unit"
            }
        ]
    }
    
    confirm_res = client.post("/api/import/confirm", json=payload)
    if confirm_res.status_code != 200:
        print(confirm_res.json())
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    
    assert confirm_data["status"] == "success"
    assert confirm_data["imported_sales"] == 2
    assert confirm_data["products_created"] == 1
    
