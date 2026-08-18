from pydantic import BaseModel, Field
from typing import List, Optional

class EvidenceFact(BaseModel):
    fact_type: str = "FACT"
    field_name: str
    value_str: str
    source_entity: str

class EvidenceSignal(BaseModel):
    signal_type: str = "SIGNAL"
    category: str  # "FESTIVAL", "SEASON", "WEATHER", "LOCALITY"
    description: str
    source: str

class IntelligenceRecommendation(BaseModel):
    title: str
    category: str  # "SELL_MORE", "WHAT_TO_STOCK", "AVOID_OVERSTOCKING"
    recommendation_summary: str
    why_reason: str
    facts: List[EvidenceFact] = []
    signals: List[EvidenceSignal] = []
    action_steps: List[str] = []

class LocalIntelligenceRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    locality_input: Optional[str] = None

class LocalIntelligenceResponse(BaseModel):
    location_source: str  # "GPS", "MANUAL", "DEFAULT_SHOP_LOCATION"
    resolved_location_name: str
    current_season: str
    upcoming_festivals: List[str] = []
    recommendations: List[IntelligenceRecommendation] = []
