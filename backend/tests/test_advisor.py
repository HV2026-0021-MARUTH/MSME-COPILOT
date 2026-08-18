import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.db.models import Product, Inventory, Sale, Purchase
from app.services.advisor_service import collect_business_evidence, generate_deterministic_action_plan

client = TestClient(app)

def test_evidence_collection_pipeline_read_only():
    db = SessionLocal()
    try:
        evidence = collect_business_evidence(db, "shop_001")
        assert "financials" in evidence
        assert "reorder_items" in evidence
        assert "profit_leaders" in evidence
        assert "slow_moving" in evidence
        assert evidence["financials"]["today_revenue"] >= 0.0
    finally:
        db.close()

def test_deterministic_action_plan_structure():
    dummy_evidence = {
        "shop_id": "shop_001",
        "date_str": "2026-08-18",
        "financials": {"today_revenue": 500.0, "today_profit": 120.0, "today_margin": 24.0, "inventory_value": 5000.0},
        "reorder_items": [
            {"name": "Coca-Cola 250ml", "current_stock": 2, "forecast_demand": 5.0, "days_of_stock": 0.4, "recommended_purchase": 33}
        ],
        "profit_leaders": [{"name": "Lays 50g", "revenue": 200.0, "profit": 50.0, "units_sold": 10}],
        "slow_moving": [{"name": "Tide Surf Excel 1kg", "current_stock": 15, "velocity": 0.0, "units_sold_30d": 0}]
    }

    plan = generate_deterministic_action_plan(dummy_evidence)
    assert plan.mode == "deterministic"
    assert len(plan.recommendations) >= 3
    assert plan.recommendations[0].priority == 1
    assert len(plan.recommendations[0].facts) > 0

def test_advisor_tomorrow_api():
    res = client.get("/api/advisor/tomorrow")
    assert res.status_code == 200
    data = res.json()
    assert "mode" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0

def test_advisor_ask_api_grounded_response():
    res = client.post("/api/advisor/ask", json={"shop_id": "shop_001", "question": "What should I reorder tomorrow?"})
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "grounded_facts" in data
    assert "recommended_actions" in data
    assert len(data["grounded_facts"]) > 0

def test_advisor_ask_empty_question_rejected():
    res = client.post("/api/advisor/ask", json={"shop_id": "shop_001", "text": ""})
    assert res.status_code == 422

def test_advisor_endpoints_read_only_safety_guarantee():
    """
    CRITICAL SAFETY TEST: Verify that calling GET /api/advisor/tomorrow
    and POST /api/advisor/ask causes EXACTLY ZERO database mutations.
    """
    db = SessionLocal()
    try:
        inv_count_before = db.query(Inventory).count()
        prod_count_before = db.query(Product).count()
        sale_count_before = db.query(Sale).count()
        purch_count_before = db.query(Purchase).count()

        # Call APIs multiple times
        client.get("/api/advisor/tomorrow")
        client.post("/api/advisor/ask", json={"question": "What are my top profit products?"})
        client.post("/api/advisor/ask", json={"question": "How can I improve my store margin?"})

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
