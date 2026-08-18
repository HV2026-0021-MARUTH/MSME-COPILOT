from typing import List, Dict, Any

def get_seasonal_intelligence() -> List[Dict[str, Any]]:
    """
    Extensible seasonal intelligence service.
    Phase 1 returning base seasonal signals.
    """
    return [
        {
            "event": "Summer Season",
            "impacted_categories": ["Beverages", "Ice Creams"],
            "recommendation": "Maintain higher inventory for soft drinks and packaged juices."
        }
    ]
