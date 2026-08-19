from app.api.deps import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Dict, Any

from app.db.database import get_db
from app.schemas.intelligence import LocalIntelligenceRequest, LocalIntelligenceResponse
from app.services.seasonal_service import (
    get_current_season, get_upcoming_festivals, get_category_seasonal_multipliers
)
from app.services.local_intelligence_service import generate_grounded_local_intelligence

router = APIRouter(prefix="/api/intelligence", tags=["Seasonal & Local Intelligence"], dependencies=[Depends(get_current_user)])

@router.get("/seasonal")
def get_seasonal_intelligence():
    """
    Get current season, upcoming festival drivers, and category demand multipliers.
    CRITICAL SAFETY GUARANTEE: READ-ONLY. Zero database mutations.
    """
    today = date.today()
    season = get_current_season(today)
    festivals = get_upcoming_festivals(today)
    multipliers = get_category_seasonal_multipliers(season, festivals)

    return {
        "current_season": season,
        "upcoming_festivals": [f["name"] for f in festivals],
        "category_multipliers": multipliers
    }

@router.post("/local", response_model=LocalIntelligenceResponse)
def get_local_intelligence(
    req: LocalIntelligenceRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    shop_id = current_user["shop_id"]
    """
    Get grounded 3-level evidence local intelligence recommendations based on 3-tier location fallback:
    Tier 1: Browser GPS
    Tier 2: Manual Locality Text Input
    Tier 3: Default Shop Location ("Ameerpet, Hyderabad")

    CRITICAL SAFETY GUARANTEE: READ-ONLY. Zero database mutations.
    """
    res = generate_grounded_local_intelligence(
        db=db,
        shop_id=shop_id,
        lat=req.latitude,
        lon=req.longitude,
        locality_input=req.locality_input
    )
    return res
