from typing import Dict, Any

def get_local_intelligence(locality: str = None, latitude: float = None, longitude: float = None) -> Dict[str, Any]:
    """
    Local intelligence service abstraction.
    If reliable information is unavailable, explicitly return:
    "No reliable local demand signal found."
    """
    if not locality and (latitude is None or longitude is None):
        return {"status": "unavailable", "message": "No reliable local demand signal found."}

    return {
        "status": "available",
        "locality": locality or "Ameerpet",
        "signals": [
            {
                "type": "footfall",
                "message": "High morning footfall expected around Ameerpet metro junction."
            }
        ]
    }
