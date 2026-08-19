import pytest
from app.services.sales_parser import find_candidate_products, parse_sales_text

class DummyProduct:
    def __init__(self, id, name, selling_price, category):
        self.id = id
        self.name = name
        self.selling_price = selling_price
        self.category = category

db_products = [
    DummyProduct("prod_1", "Thums Up 750ml", 40.0, "Beverages"),
    DummyProduct("prod_2", "Dairy Milk Silk 60g", 80.0, "Snacks"),
    DummyProduct("prod_3", "Amul Taaza Milk 500ml", 25.0, "Dairy"),
    DummyProduct("prod_4", "Lays Magic Masala Blue", 10.0, "Snacks"),
    DummyProduct("prod_5", "Lays Blue 50g", 20.0, "Snacks"),
    DummyProduct("prod_6", "Coca-Cola 250ml", 20.0, "Beverages")
]

def test_exact_match():
    # 1. Exact match should score 1.0 and match status EXACT
    res = parse_sales_text("sold 2 Thums Up 750ml", db_products)
    item = res["items"][0]
    assert item["match_status"] == "EXACT"
    assert item["matched_product_id"] == "prod_1"
    assert item["confidence"] == 1.0

def test_strong_fuzzy_match_no_competition():
    # 2. Strong fuzzy match (e.g. coke matches coca-cola)
    res = parse_sales_text("sold 1 coke", db_products)
    item = res["items"][0]
    # "coke" maps to "coca cola" in query_variants, which exactly matches "coca-cola" in normalized string
    assert item["match_status"] in ["EXACT", "MATCHED"]
    assert item["matched_product_id"] == "prod_6"
    
    # Substring match "lays blue" -> "lays blue 50g"
    res2 = parse_sales_text("sold 2 lays blue", db_products)
    item2 = res2["items"][0]
    assert item2["match_status"] == "AMBIGUOUS"
    # Wait, 'lays blue' matches 'Lays Blue 50g' (score 0.85) and 'Lays Magic Masala Blue' (token score 0.75)
    # 0.85 - 0.75 = 0.10 < 0.15 margin, so it might be AMBIGUOUS!
    # Let's check what it actually outputs.

def test_dairy_milk_safety():
    # 3. "dairy milk" should NOT auto match "Thums Up 750ml"
    # It should match Dairy Milk Silk 60g (Substring: 0.85).
    # Since there are no other close ones (Amul Milk gets 0.375 token score).
    res = parse_sales_text("sold 1 dairy milk", db_products)
    item = res["items"][0]
    assert item["match_status"] == "MATCHED"
    assert item["matched_product_id"] == "prod_2"
    
def test_no_match():
    # 4. Nonsense should be NEEDS_MATCH
    res = parse_sales_text("sold 1 xyzrandomthing", db_products)
    item = res["items"][0]
    assert item["match_status"] == "NEEDS_MATCH"
    assert item["matched_product_id"] is None
