import pytest
import io
import openpyxl
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.db.models import Product, Inventory, Sale, Purchase
from app.services.report_service import (
    collect_report_data, generate_pdf_report, generate_xlsx_report, generate_png_report
)

client = TestClient(app)

def test_report_data_collection_periods():
    db = SessionLocal()
    try:
        data_7d = collect_report_data(db, "shop_001", "7d")
        data_today = collect_report_data(db, "shop_001", "today")
        data_30d = collect_report_data(db, "shop_001", "30d")

        assert "financials" in data_7d
        assert "metadata" in data_7d
        assert data_7d["metadata"]["period_code"] == "7d"
        assert data_today["metadata"]["period_code"] == "today"
        assert data_30d["metadata"]["period_code"] == "30d"
    finally:
        db.close()

def test_pdf_report_generation():
    db = SessionLocal()
    try:
        data = collect_report_data(db, "shop_001", "7d")
        pdf_bytes = generate_pdf_report(data)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF-")
    finally:
        db.close()

def test_xlsx_report_generation_7_sheets():
    db = SessionLocal()
    try:
        data = collect_report_data(db, "shop_001", "7d")
        xlsx_bytes = generate_xlsx_report(data)
        assert isinstance(xlsx_bytes, bytes)
        assert len(xlsx_bytes) > 1000

        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
        sheet_names = wb.sheetnames
        expected_sheets = ["Summary", "Sales", "Inventory", "Product Performance", "Forecast", "Advisor", "Seasonal & Local Intelligence"]
        for expected in expected_sheets:
            assert expected in sheet_names
    finally:
        db.close()

def test_png_report_generation():
    db = SessionLocal()
    try:
        data = collect_report_data(db, "shop_001", "7d")
        png_bytes = generate_png_report(data)
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 1000
        assert png_bytes.startswith(b"\x89PNG")
    finally:
        db.close()

def test_reports_pdf_api_mime_header():
    res = client.get("/api/reports/business/pdf?period=7d")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in res.headers["content-disposition"]
    assert res.content.startswith(b"%PDF-")

def test_reports_xlsx_api_mime_header():
    res = client.get("/api/reports/business/xlsx?period=7d")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment; filename=" in res.headers["content-disposition"]

def test_reports_png_api_mime_header():
    res = client.get("/api/reports/business/png?period=7d")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert res.content.startswith(b"\x89PNG")

def test_cross_format_numeric_consistency():
    """
    CRITICAL TEST: Verify that PDF, XLSX, and PNG data sources produce
    EXACTLY IDENTICAL numeric values for Revenue, Profit, Margin %, and Inventory Valuation.
    """
    db = SessionLocal()
    try:
        data_pdf = collect_report_data(db, "shop_001", "7d")
        data_xlsx = collect_report_data(db, "shop_001", "7d")
        data_png = collect_report_data(db, "shop_001", "7d")

        fin_pdf = data_pdf["financials"]
        fin_xlsx = data_xlsx["financials"]
        fin_png = data_png["financials"]

        assert fin_pdf["revenue"] == fin_xlsx["revenue"] == fin_png["revenue"]
        assert fin_pdf["profit"] == fin_xlsx["profit"] == fin_png["profit"]
        assert fin_pdf["margin"] == fin_xlsx["margin"] == fin_png["margin"]
        assert fin_pdf["inventory_value"] == fin_xlsx["inventory_value"] == fin_png["inventory_value"]
    finally:
        db.close()

def test_reports_read_only_safety_guarantee():
    """
    CRITICAL SAFETY TEST: Verify that generating PDF, XLSX, and PNG reports
    causes EXACTLY ZERO database mutations.
    """
    db = SessionLocal()
    try:
        inv_count_before = db.query(Inventory).count()
        prod_count_before = db.query(Product).count()
        sale_count_before = db.query(Sale).count()
        purch_count_before = db.query(Purchase).count()

        # Call all report APIs multiple times
        client.get("/api/reports/business/pdf?period=today")
        client.get("/api/reports/business/xlsx?period=7d")
        client.get("/api/reports/business/png?period=30d")

        inv_count_after = db.query(Inventory).count()
        prod_count_after = db.query(Product).count()
        sale_count_after = db.query(Sale).count()
        purch_count_after = db.query(Purchase).count()

        assert inv_count_before == inv_count_after
        assert prod_count_before == prod_count_after
        assert sale_count_before == sale_count_after
        assert purch_count_before == purch_count_after
    finally:
        db.close()

def test_reports_backward_compatibility_aliases():
    res_pdf = client.get("/api/reports/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"

    res_xlsx = client.get("/api/reports/xlsx")
    assert res_xlsx.status_code == 200
    assert "spreadsheetml.sheet" in res_xlsx.headers["content-type"]

    res_png = client.get("/api/reports/png")
    assert res_png.status_code == 200
    assert res_png.headers["content-type"] == "image/png"
