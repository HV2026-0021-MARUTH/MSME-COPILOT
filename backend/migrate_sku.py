import os
import sys
import uuid
import re
from sqlalchemy import text
from app.db.database import SessionLocal, engine
from app.db.models import Product

def generate_sku(name: str, existing_skus: set) -> str:
    # Basic rule: initials of the first few words + last number (if any)
    # E.g., Dairy Milk 40g -> DM-40g -> DM-40
    words = name.split()
    initials = ""
    number_part = ""
    
    for word in words:
        if any(char.isdigit() for char in word):
            match = re.search(r'(\d+)', word)
            if match:
                number_part = match.group(1)
        elif word[0].isalpha():
            initials += word[0].upper()
            
    if not initials:
        initials = "PRD"
        
    base_sku = f"{initials[:3]}-{number_part}" if number_part else f"{initials[:3]}"
    base_sku = base_sku.strip('-')
    
    sku = base_sku
    counter = 1
    while sku in existing_skus:
        sku = f"{base_sku}-{counter}"
        counter += 1
        
    return sku

def migrate():
    print("Starting SKU and Aliases migration...")
    
    # 1. Alter table
    with engine.connect() as conn:
        try:
            # SQLite does not support adding UNIQUE columns directly via ALTER TABLE
            conn.execute(text("ALTER TABLE products ADD COLUMN sku VARCHAR(100);"))
            print("Added 'sku' column.")
        except Exception as e:
            print(f"'sku' column might already exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN aliases VARCHAR(500);"))
            print("Added 'aliases' column.")
        except Exception as e:
            print(f"'aliases' column might already exist: {e}")
            
        try:
            conn.execute(text("CREATE UNIQUE INDEX ix_products_sku ON products (sku);"))
            print("Created unique index on 'sku'.")
        except Exception as e:
            print(f"Unique index on 'sku' might already exist: {e}")
        
        conn.commit()

    # 2. Populate missing SKUs
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        existing_skus = {p.sku for p in products if p.sku}
        
        updated_count = 0
        for p in products:
            if not p.sku:
                new_sku = generate_sku(p.name, existing_skus)
                p.sku = new_sku
                existing_skus.add(new_sku)
                updated_count += 1
                print(f"Generated SKU {new_sku} for '{p.name}'")
                
        if updated_count > 0:
            db.commit()
            print(f"Successfully assigned SKUs to {updated_count} products.")
        else:
            print("All products already have a SKU.")
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()
        
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
