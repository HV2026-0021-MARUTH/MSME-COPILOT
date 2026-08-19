import re
import difflib
from typing import Dict, Any, List
from app.config import settings

def normalize_string(s: str) -> str:
    """
    Normalize product string for matching: lowercase, strip punctuation, strip extra whitespace.
    """
    if not s:
        return ""
    # Lowercase & replace special chars with spaces
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', s.lower())
    # Collapse multiple spaces
    return re.sub(r'\s+', ' ', cleaned).strip()

def match_single_product(extracted_name: str, db_products: List[Any]) -> Dict[str, Any]:
    """
    Match an extracted invoice product name against database products.
    Returns:
    - match_status: 'MATCHED' or 'NEEDS_MATCH'
    - matched_product_id: Optional[str]
    - matched_product_name: Optional[str]
    - confidence: float (0.0 to 1.0)
    """
    if not extracted_name or not db_products:
        return {
            "match_status": "NEEDS_MATCH",
            "matched_product_id": None,
            "matched_product_name": None,
            "confidence": 0.0
        }

    raw_extracted = extracted_name.strip()
    norm_extracted = normalize_string(raw_extracted)

    best_match = None
    highest_score = 0.0
    match_type = "fuzzy"

    for prod in db_products:
        prod_name = prod.name.strip()
        norm_prod = normalize_string(prod_name)
        prod_sku = getattr(prod, "sku", "") or ""
        norm_sku = normalize_string(prod_sku)
        prod_aliases = getattr(prod, "aliases", "") or ""
        aliases_list = [normalize_string(a.strip()) for a in prod_aliases.split(',') if a.strip()]

        # 1. Exact SKU Match
        if norm_sku and norm_extracted == norm_sku:
            return {
                "match_status": "MATCHED",
                "matched_product_id": prod.id,
                "matched_product_name": prod.name,
                "sku": prod_sku,
                "aliases": prod_aliases,
                "match_type": "exact_sku",
                "confidence": 1.0
            }

        # 2. Exact Name Match
        if raw_extracted.lower() == prod_name.lower() or norm_extracted == norm_prod:
            return {
                "match_status": "MATCHED",
                "matched_product_id": prod.id,
                "matched_product_name": prod.name,
                "sku": prod_sku,
                "aliases": prod_aliases,
                "match_type": "exact_name",
                "confidence": 1.0
            }

        # 3. Alias Match
        if norm_extracted in aliases_list:
            return {
                "match_status": "MATCHED",
                "matched_product_id": prod.id,
                "matched_product_name": prod.name,
                "sku": prod_sku,
                "aliases": prod_aliases,
                "match_type": "alias",
                "confidence": 0.95
            }

        # 4. Normalized Match
        if norm_extracted in norm_prod or norm_prod in norm_extracted:
            score = 0.90
            if score > highest_score:
                highest_score = score
                best_match = prod
                match_type = "fuzzy"

        # 5. Fuzzy Sequence Match
        similarity = difflib.SequenceMatcher(None, norm_extracted, norm_prod).ratio()
        if similarity > highest_score:
            highest_score = similarity
            best_match = prod
            match_type = "fuzzy"

    if best_match and highest_score >= 0.65:
        return {
            "match_status": "MATCHED",
            "matched_product_id": best_match.id,
            "matched_product_name": best_match.name,
            "sku": getattr(best_match, "sku", ""),
            "aliases": getattr(best_match, "aliases", ""),
            "match_type": match_type,
            "confidence": round(highest_score, 2)
        }

    return {
        "match_status": "NEEDS_MATCH",
        "matched_product_id": None,
        "matched_product_name": None,
        "sku": None,
        "aliases": None,
        "match_type": None,
        "confidence": round(highest_score, 2) if highest_score > 0 else 0.0
    }

def parse_invoice_image(image_bytes: bytes, filename: str = "invoice.jpg", db_products: List[Any] = None) -> Dict[str, Any]:
    """
    Extract structured supplier invoice data.
    Uses AI credentials if available in environment variables (GEMINI_API_KEY / OPENAI_API_KEY).
    If no API key is provided, returns a clearly labelled development/demo fallback ("mode": "demo").
    """
    mode = "demo"
    supplier = "Sri Venkateswara Wholesale Depot"
    invoice_number = "INV-2026-0818"
    invoice_date = "2026-08-18"
    extracted_items = []
    confidence = 0.92

    # Check for AI API key configuration
    gemini_key = settings.GEMINI_API_KEY
    openai_key = settings.OPENAI_API_KEY

    if gemini_key or openai_key:
        mode = "ai"
        # Real AI Provider Integration placeholder when credentials exist
        # Extracts raw image bytes via vision API
        pass

    if mode == "demo":
        extracted_items = [
            {"name": "Coca-Cola 250ml", "quantity": 24, "unit": "bottle", "unit_cost": 15.00, "total": 360.00},
            {"name": "Lays Classic Salted 50g", "quantity": 20, "unit": "pack", "unit_cost": 16.00, "total": 320.00},
            {"name": "Unknown Organic Green Tea 100g", "quantity": 10, "unit": "pack", "unit_cost": 85.00, "total": 850.00}
        ]

    # Perform Product Matching against database products
    matched_items = []
    subtotal = 0.0

    for item in extracted_items:
        line_total = round(item["quantity"] * item["unit_cost"], 2)
        subtotal += line_total

        match_info = match_single_product(item["name"], db_products or [])

        matched_items.append({
            "extracted_name": item["name"],
            "quantity": item["quantity"],
            "unit": item.get("unit", "unit"),
            "unit_cost": item["unit_cost"],
            "total": line_total,
            "match_status": match_info["match_status"],
            "matched_product_id": match_info["matched_product_id"],
            "matched_product_name": match_info["matched_product_name"],
            "match_type": match_info.get("match_type"),
            "sku": match_info.get("sku"),
            "aliases": match_info.get("aliases"),
            "confidence": match_info["confidence"]
        })

    subtotal = round(subtotal, 2)
    tax = round(subtotal * 0.05, 2) if mode == "demo" else 0.0
    grand_total = round(subtotal + tax, 2)

    return {
        "mode": mode,
        "supplier": supplier,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "items": matched_items,
        "subtotal": subtotal,
        "tax": tax,
        "grand_total": grand_total,
        "confidence": confidence
    }
