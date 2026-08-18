import re
import difflib
from typing import Dict, Any, List
from app.services.invoice_parser import normalize_string

NUMBER_WORDS = {
    "zero": 0, "one": 1, "a": 1, "an": 1, "two": 2, "three": 3,
    "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "twenty": 20
}

def parse_number_from_token(token: str) -> int:
    token_lower = token.lower().strip()
    if token_lower.isdigit():
        return int(token_lower)
    if token_lower in NUMBER_WORDS:
        return NUMBER_WORDS[token_lower]
    return None

def find_candidate_products(query: str, db_products: List[Any]) -> List[Dict[str, Any]]:
    """
    Find candidate DB products matching a query string (handles exact, substring, prefix, and fuzzy/colloquial matching).
    """
    norm_query = normalize_string(query)
    if not norm_query or not db_products:
        return []

    # Map colloquial shortcuts
    if norm_query == "coke":
        query_variants = ["coke", "coca", "coca cola"]
    else:
        query_variants = [norm_query]

    candidates = []
    seen_ids = set()

    for prod in db_products:
        prod_id = getattr(prod, 'id', None) or getattr(prod, 'product_id', str(prod))
        prod_name = prod.name
        norm_prod = normalize_string(prod_name)

        matched = False
        score = 0.0

        for q in query_variants:
            # 1. Exact Match
            if q == norm_prod:
                score = 1.0
                matched = True
                break

            # 2. Substring Match
            if q in norm_prod or norm_prod in q:
                score = max(score, 0.85)
                matched = True

            # 3. Partial Token Match (e.g., 'coke' matching 'coca-cola')
            q_tokens = q.split()
            p_tokens = norm_prod.split()
            for qt in q_tokens:
                for pt in p_tokens:
                    if len(qt) >= 3 and len(pt) >= 3 and (qt in pt or pt in qt or qt[:3] == pt[:3]):
                        score = max(score, 0.70)
                        matched = True

            # 4. Fuzzy Sequence Match
            ratio = difflib.SequenceMatcher(None, q, norm_prod).ratio()
            if ratio >= 0.45:
                score = max(score, ratio)
                matched = True

        if matched and prod_id not in seen_ids:
            seen_ids.add(prod_id)
            candidates.append({"product": prod, "score": round(score, 2)})

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates

def parse_sales_text(text: str, db_products: List[Any]) -> Dict[str, Any]:
    """
    Parse natural-language sale text (e.g., 'Sold 3 Coke and 2 Lays').
    Extracts quantities and product matches.
    CRITICAL SAFETY GUARANTEE: Does NOT modify database or inventory.
    """
    if not text or not text.strip():
        return {
            "mode": "text",
            "items": [],
            "estimated_total": 0.0,
            "estimated_profit": 0.0,
            "requires_review": False
        }

    raw_text = text.strip()
    cleaned = re.sub(r'(?i)\b(sold|sale|of|and|\&)\b', ',', raw_text)
    segments = [s.strip() for s in cleaned.split(',') if s.strip()]

    parsed_items = []
    estimated_total = 0.0
    estimated_profit = 0.0
    requires_review = False

    for seg in segments:
        tokens = seg.split()
        if not tokens:
            continue

        quantity = 1
        product_name_parts = []

        for token in tokens:
            parsed_qty = parse_number_from_token(token)
            if parsed_qty is not None and len(product_name_parts) == 0:
                quantity = parsed_qty
            else:
                product_name_parts.append(token)

        extracted_name = " ".join(product_name_parts).strip()
        if not extracted_name and len(tokens) == 1 and parse_number_from_token(tokens[0]) is not None:
            continue
        if not extracted_name:
            extracted_name = seg

        candidates = find_candidate_products(extracted_name, db_products or [])

        match_status = "NEEDS_MATCH"
        matched_prod_id = None
        matched_prod_name = None
        unit_sp = 0.0
        unit_cp = 0.0
        confidence = 0.0
        candidate_list = []

        if len(candidates) == 1 and candidates[0]["score"] >= 0.85:
            top = candidates[0]
            match_status = "MATCHED"
            matched_prod_id = top["product"].id
            matched_prod_name = top["product"].name
            unit_sp = float(top["product"].selling_price)
            unit_cp = float(top["product"].purchase_price)
            confidence = round(top["score"], 2)
        elif len(candidates) >= 1:
            # Ambiguous or multiple candidate matches -> Requires user resolution
            match_status = "AMBIGUOUS" if len(candidates) > 1 else "MATCHED"
            if len(candidates) == 1:
                top = candidates[0]
                matched_prod_id = top["product"].id
                matched_prod_name = top["product"].name
                unit_sp = float(top["product"].selling_price)
                unit_cp = float(top["product"].purchase_price)
                confidence = round(top["score"], 2)
            else:
                requires_review = True
                confidence = round(candidates[0]["score"], 2)

            candidate_list = [
                {
                    "product_id": c["product"].id,
                    "name": c["product"].name,
                    "category": c["product"].category,
                    "selling_price": float(c["product"].selling_price)
                }
                for c in candidates[:5]
            ]
        else:
            match_status = "NEEDS_MATCH"
            requires_review = True
            confidence = 0.0

        line_total = round(quantity * unit_sp, 2)
        line_profit = round(quantity * (unit_sp - unit_cp), 2)

        estimated_total += line_total
        estimated_profit += line_profit

        parsed_items.append({
            "raw_segment": seg,
            "extracted_name": extracted_name,
            "quantity": quantity,
            "match_status": match_status,
            "matched_product_id": matched_prod_id,
            "matched_product_name": matched_prod_name,
            "selling_price": unit_sp,
            "purchase_price": unit_cp,
            "line_total": line_total,
            "confidence": confidence,
            "candidates": candidate_list
        })

    estimated_total = round(estimated_total, 2)
    estimated_profit = round(estimated_profit, 2)

    return {
        "mode": "text",
        "raw_text": raw_text,
        "items": parsed_items,
        "estimated_total": estimated_total,
        "estimated_profit": estimated_profit,
        "requires_review": requires_review or any(i["match_status"] != "MATCHED" for i in parsed_items)
    }
