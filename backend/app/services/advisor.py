from typing import List, Dict, Any

def generate_business_recommendations(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Phase 1 AI Advisor service interface.
    """
    return [
        {
            "action": "RESTOCK",
            "item": "Coca-Cola 250ml",
            "current_stock": 6,
            "forecast_demand": 18.0,
            "recommended_purchase": 24,
            "confidence": "High",
            "reason": "Current stock is below one day's forecast demand."
        }
    ]
