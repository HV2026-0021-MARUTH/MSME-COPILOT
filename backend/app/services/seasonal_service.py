from datetime import date
from typing import Dict, Any, List

PRACTICAL_FESTIVALS = [
    {"name": "Sankranti / Pongal", "month": 1, "categories": ["Beverages", "Sweets & Bakery", "Staples"]},
    {"name": "Holi Festival of Colors", "month": 3, "categories": ["Beverages", "Snacks & Munchies", "Dairy"]},
    {"name": "Ramzan / Eid-ul-Fitr", "month": 4, "categories": ["Dairy", "Staples", "Beverages"]},
    {"name": "Raksha Bandhan / Independence Day", "month": 8, "categories": ["Chocolates & Sweets", "Snacks & Munchies"]},
    {"name": "Ganesh Chaturthi", "month": 8, "categories": ["Dairy", "Chocolates & Sweets", "Beverages"]},
    {"name": "Diwali / Dussehra", "month": 10, "categories": ["Chocolates & Sweets", "Beverages", "Snacks & Munchies", "Staples"]},
    {"name": "Christmas / New Year", "month": 12, "categories": ["Beverages", "Chocolates & Sweets"]}
]

def get_current_season(current_date: date) -> str:
    m = current_date.month
    if 3 <= m <= 6:
        return "Summer Season"
    elif 7 <= m <= 10:
        return "Monsoon Season"
    else:
        return "Winter Season"

def get_upcoming_festivals(current_date: date) -> List[Dict[str, Any]]:
    m = current_date.month
    upcoming = []
    for fest in PRACTICAL_FESTIVALS:
        if fest["month"] == m or fest["month"] == (m % 12) + 1:
            upcoming.append(fest)
    if not upcoming:
        # Default fallback festival driver
        upcoming.append({"name": "Regional Cultural Festival", "month": m, "categories": ["Beverages", "Snacks & Munchies"]})
    return upcoming

def get_category_seasonal_multipliers(season: str, festivals: List[Dict[str, Any]]) -> Dict[str, float]:
    multipliers = {
        "Beverages": 1.0,
        "Snacks & Munchies": 1.0,
        "Dairy": 1.0,
        "Chocolates & Sweets": 1.0,
        "Staples": 1.0,
        "Personal Care": 1.0,
        "Household Care": 1.0
    }

    if season == "Summer Season":
        multipliers["Beverages"] = 1.5
        multipliers["Dairy"] = 1.3
    elif season == "Monsoon Season":
        multipliers["Household Care"] = 1.4
        multipliers["Snacks & Munchies"] = 1.3
        multipliers["Personal Care"] = 1.2
    elif season == "Winter Season":
        multipliers["Staples"] = 1.3
        multipliers["Dairy"] = 1.2

    for f in festivals:
        for cat in f["categories"]:
            if cat in multipliers:
                multipliers[cat] = max(multipliers[cat], 1.4)

    return multipliers
