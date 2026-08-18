import pytest
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal
from app.db.models import Product, Inventory, Sale, Purchase
from app.services.seasonal_service import (
    get_current_season, get_upcoming_festivals, get_category_seasonal_multipliers
)
from app.services.local_intelligence_service import resolve_location_3tier

client = TestClient(app)

# 1. Pure Unit Tests for Seasonal & Location Services

def test_get_current_season():
    assert get_current_season(date(2026, 5, 15)) == "Summer Season"
    assert get_current_season(date(2026, 8, 18)) == "Monsoon Season"
    assert get_current_season(date(2026, 12, 25)) == "Winter Season"

def test_get_upcoming_festivals():
    fests = get_upcoming_festivals(date(2026, 8, 18))
    assert isinstance(fests, list)
    assert len(fests) > 0
    assert any("Raksha Bandhan" in f["name"] or "Ganesh" in f["name"] or "Regional" in f["name"] for f in fests)

def test_category_seasonal_multipliers():
    mults = get_category_seasonal_multipliers("Summer Season", [])
    assert mults["Beverages"] == 1.5

def test_resolve_location_3tier_gps():
    loc = resolve_location_3tier(lat=17.4375, lon=78.4482, locality_input=None)
    assert loc["source"] == "GPS"
    assert "GPS:" in loc["name"]

def test_resolve_location_3tier_manual():
    loc = resolve_location_3tier(lat=None, lon=None, locality_input="Koramangala, Bengaluru")
    assert loc["source"] == "MANUAL"
    assert "Koramangala, Bengaluru" in loc["name"]

def test_resolve_location_3tier_default_fallback():
    loc = resolve_location_3tier(lat=None, lon=None, locality_input=None)
    assert loc["source"] == "DEFAULT_SHOP_LOCATION"
    assert "Ameerpet, Hyderabad" in loc["name"]


# 2. Integration Tests via API Client

def test_seasonal_intelligence_api():
    res = client.get("/api/intelligence/seasonal")
    assert res.status_code == 200
    data = res.json()
    assert "current_season" in data
    assert "upcoming_festivals" in data
    assert "category_multipliers" in data

def test_local_intelligence_api_3tier_fallback():
    # 1. Tier 1 GPS Test
    res_gps = client.post("/api/intelligence/local", json={"latitude": 17.43, "longitude": 78.44})
    assert res_gps.status_code == 200
    assert res_gps.json()["location_source"] == "GPS"

    # 2. Tier 2 Manual Locality Test
    res_man = client.post("/api/intelligence/local", json={"locality_input": "Banjara Hills, Hyderabad"})
    assert res_man.status_code == 200
    assert res_man.json()["location_source"] == "MANUAL"

    # 3. Tier 3 Default Fallback Test
    res_def = client.post("/api/intelligence/local", json={})
    assert res_def.status_code == 200
    assert res_def.json()["location_source"] == "DEFAULT_SHOP_LOCATION"

def test_intelligence_3level_evidence_structure():
    res = client.post("/api/intelligence/local", json={"locality_input": "Ameerpet, Hyderabad"})
    assert res.status_code == 200
    data = res.json()
    assert "recommendations" in data
    recs = data["recommendations"]
    assert len(recs) > 0
    first = recs[0]
    assert "title" in first
    assert "category" in first
    assert "recommendation_summary" in first
    assert "why_reason" in first
    assert len(first["facts"]) > 0
    assert len(first["signals"]) > 0
    assert first["facts"][0]["fact_type"] == "FACT"
    assert first["signals"][0]["signal_type"] == "SIGNAL"

def test_intelligence_read_only_safety_guarantee():
    """
    CRITICAL SAFETY TEST: Verify that calling GET /api/intelligence/seasonal
    and POST /api/intelligence/local causes EXACTLY ZERO database mutations.
    """
    db = SessionLocal()
    try:
        inv_count_before = db.query(Inventory).count()
        prod_count_before = db.query(Product).count()
        sale_count_before = db.query(Sale).count()
        purch_count_before = db.query(Purchase).count()

        # Call intelligence endpoints multiple times
        client.get("/api/intelligence/seasonal")
        client.post("/api/intelligence/local", json={"locality_input": "Test Locality"})
        client.post("/api/intelligence/local", json={"latitude": 17.4, "longitude": 78.4})

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
