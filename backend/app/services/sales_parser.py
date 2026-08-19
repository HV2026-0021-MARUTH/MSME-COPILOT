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

def get_prod_id(prod: Any) -> str:
    if isinstance(prod, dict):
        return prod.get("id") or prod.get("product_id")
    return getattr(prod, "id", None) or getattr(prod, "product_id", str(prod))

def get_prod_name(prod: Any) -> str:
    if isinstance(prod, dict):
        return prod.get("name") or prod.get("product_name", "")
    return getattr(prod, "name", None) or getattr(prod, "product_name", str(prod))

def get_prod_sp(prod: Any) -> float:
    if isinstance(prod, dict):
        return float(prod.get("selling_price", 0.0))
    return float(getattr(prod, "selling_price", 0.0))

def get_prod_cp(prod: Any) -> float:
    if isinstance(prod, dict):
        return float(prod.get("purchase_price", 0.0))
    return float(getattr(prod, "purchase_price", 0.0))

def get_prod_sku(prod: Any) -> str:
    if isinstance(prod, dict):
        return prod.get("sku", "")
    return getattr(prod, "sku", "") or ""

def get_prod_aliases(prod: Any) -> str:
    if isinstance(prod, dict):
        return prod.get("aliases", "")
    return getattr(prod, "aliases", "") or ""

def find_candidate_products(query: str, db_products: List[Any]) -> List[Dict[str, Any]]:
    """
    Find candidate DB products matching a query string (handles exact SKU, exact name, alias, and fuzzy).
    """
    norm_query = normalize_string(query)
    if not norm_query or not db_products:
        return []

    query_variants = [norm_query]
    # Keep colloquial shortcuts if needed, or rely on aliases
    if norm_query == "coke":
        query_variants.extend(["coca", "coca cola"])

    candidates = []
    seen_ids = set()

    for prod in db_products:
        prod_id = get_prod_id(prod)
        prod_name = get_prod_name(prod)
        prod_sku = get_prod_sku(prod)
        prod_aliases = get_prod_aliases(prod)
        
        norm_prod = normalize_string(prod_name)
        norm_sku = normalize_string(prod_sku)
        aliases_list = [normalize_string(a.strip()) for a in prod_aliases.split(',') if a.strip()]

        matched = False
        score = 0.0
        match_type = "fuzzy"

        for q in query_variants:
            # 1. Exact SKU Match (Highest priority)
            if norm_sku and q == norm_sku:
                score = 1.0
                matched = True
                match_type = "exact_sku"
                break
                
            # 2. Exact Product Name Match
            if q == norm_prod:
                score = 1.0
                matched = True
                match_type = "exact_name"
                break

            # 3. Alias Match
            if q in aliases_list:
                score = 0.95
                matched = True
                match_type = "alias"
                break

            # 4. Substring Match
            if q in norm_prod or norm_prod in q:
                if len(q) > 4:
                    if score < 0.85:
                        score = 0.85
                        match_type = "fuzzy"
                else:
                    if score < 0.60:
                        score = 0.60
                        match_type = "fuzzy"
                matched = True

            # 5. Partial Token Match
            q_tokens = q.split()
            p_tokens = norm_prod.split()
            
            matches = 0
            for qt in q_tokens:
                if len(qt) < 2:
                    continue
                for pt in p_tokens:
                    if len(pt) < 2:
                        continue
                    if qt == pt or qt in pt or pt in qt:
                        matches += 1
                        break
            
            if matches > 0 and len(q_tokens) > 0:
                token_score = (matches / len(q_tokens)) * 0.75
                if token_score > score:
                    score = token_score
                    match_type = "fuzzy"
                matched = True

            # 6. Fuzzy Sequence Match
            ratio = difflib.SequenceMatcher(None, q, norm_prod).ratio()
            if ratio >= 0.45:
                if ratio > score:
                    score = ratio
                    match_type = "fuzzy"
                matched = True

        if matched and prod_id not in seen_ids:
            seen_ids.add(prod_id)
            candidates.append({
                "product": prod, 
                "score": round(score, 2),
                "match_type": match_type
            })

    # Sort by score desc, then exact matches first
    candidates.sort(key=lambda x: (x["score"], 1 if x["match_type"] in ["exact_sku", "exact_name"] else 0), reverse=True)
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
            "raw_text": text or "",
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
        match_type = None
        sku = None
        aliases = None
        candidate_list = []

        if candidates:
            top = candidates[0]
            top_score = top["score"]

            candidate_list = [
                {
                    "product_id": get_prod_id(c["product"]),
                    "sku": get_prod_sku(c["product"]),
                    "name": get_prod_name(c["product"]),
                    "aliases": get_prod_aliases(c["product"]),
                    "category": getattr(c["product"], 'category', 'General') if not isinstance(c["product"], dict) else c["product"].get('category', 'General'),
                    "selling_price": get_prod_sp(c["product"]),
                    "match_type": c.get("match_type", "fuzzy")
                }
                for c in candidates[:5]
            ]

            # Check if top candidate is an EXACT or normalized exact match (score == 1.0)
            if top_score >= 0.99:
                match_status = "EXACT"
                matched_prod_id = get_prod_id(top["product"])
                matched_prod_name = get_prod_name(top["product"])
                sku = get_prod_sku(top["product"])
                aliases = get_prod_aliases(top["product"])
                match_type = top["match_type"]
                unit_sp = get_prod_sp(top["product"])
                unit_cp = get_prod_cp(top["product"])
                confidence = 1.0

            # Single high-confidence match (score >= 0.85 with no competing second candidate)
            elif top_score >= 0.85 and (len(candidates) == 1 or (top_score - candidates[1]["score"]) >= 0.15):
                match_status = "MATCHED"
                matched_prod_id = get_prod_id(top["product"])
                matched_prod_name = get_prod_name(top["product"])
                sku = get_prod_sku(top["product"])
                aliases = get_prod_aliases(top["product"])
                match_type = top["match_type"]
                unit_sp = get_prod_sp(top["product"])
                unit_cp = get_prod_cp(top["product"])
                confidence = round(top_score, 2)

            # Ambiguous match (multiple plausible candidates without a single clear winner)
            elif len(candidates) >= 1 and top_score >= 0.45:
                match_status = "AMBIGUOUS"
                matched_prod_id = get_prod_id(top["product"])
                matched_prod_name = get_prod_name(top["product"])
                sku = get_prod_sku(top["product"])
                aliases = get_prod_aliases(top["product"])
                match_type = top["match_type"]
                unit_sp = get_prod_sp(top["product"])
                unit_cp = get_prod_cp(top["product"])
                confidence = round(top_score, 2)
            else:
                match_status = "NEEDS_MATCH"
                confidence = round(top_score, 2) if top_score > 0 else 0.0
        else:
            match_status = "NEEDS_MATCH"
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
            "match_type": match_type,
            "sku": sku,
            "aliases": aliases,
            "selling_price": unit_sp,
            "purchase_price": unit_cp,
            "line_total": line_total,
            "confidence": confidence,
            "candidates": candidate_list
        })

    estimated_total = round(estimated_total, 2)
    estimated_profit = round(estimated_profit, 2)
    requires_review = any(i["match_status"] not in ["EXACT", "MATCHED"] for i in parsed_items)

    return {
        "mode": "text",
        "raw_text": raw_text,
        "items": parsed_items,
        "estimated_total": estimated_total,
        "estimated_profit": estimated_profit,
        "requires_review": requires_review
    }
