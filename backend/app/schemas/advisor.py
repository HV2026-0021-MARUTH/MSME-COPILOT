from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FactItem(BaseModel):
    fact_type: str = "FACT"
    field_name: str
    value_str: str
    source_entity: str

class ActionRecommendation(BaseModel):
    priority: int = Field(..., ge=1, le=5, description="1 is highest priority")
    category: str  # "URGENT_REORDER", "PROFIT_OPPORTUNITY", "SLOW_MOVING_ACTION"
    title: str
    recommendation_summary: str
    facts: List[FactItem] = []
    action_steps: List[str] = []

class TomorrowPlanResponse(BaseModel):
    mode: str = "deterministic"  # "ai_grounded" or "deterministic"
    shop_id: str = "shop_001"
    generated_at: str
    recommendations: List[ActionRecommendation] = []
    summary_text: str

class AdvisorAskRequest(BaseModel):
    shop_id: str = "shop_001"
    question: str = Field(..., min_length=1, description="Retailer question is required")

class AdvisorAskResponse(BaseModel):
    mode: str = "deterministic"
    question: str
    answer: str
    grounded_facts: List[FactItem] = []
    recommended_actions: List[str] = []
