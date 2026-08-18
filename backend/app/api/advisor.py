from app.api.deps import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.advisor import TomorrowPlanResponse, AdvisorAskRequest, AdvisorAskResponse
from app.services.advisor_service import get_tomorrow_action_plan, answer_advisor_question

router = APIRouter(prefix="/api/advisor", tags=["AI Business Advisor"], dependencies=[Depends(get_current_user)])

@router.get("/tomorrow", response_model=TomorrowPlanResponse)
def get_tomorrow_plan(shop_id: str = "shop_001", db: Session = Depends(get_db)):
    """
    Get prioritized action plan for tomorrow based on verified evidence pipeline.
    CRITICAL SAFETY GUARANTEE: READ-ONLY. Zero database mutations.
    """
    plan = get_tomorrow_action_plan(db, shop_id)
    return plan

@router.post("/ask", response_model=AdvisorAskResponse)
def ask_advisor(req: AdvisorAskRequest, db: Session = Depends(get_db)):
    """
    Ask a natural-language question to the AI Business Advisor.
    Returns grounded answer with cited facts from verified database evidence.
    CRITICAL SAFETY GUARANTEE: READ-ONLY. Zero database mutations.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    res = answer_advisor_question(req.question.strip(), db, req.shop_id)
    return res
