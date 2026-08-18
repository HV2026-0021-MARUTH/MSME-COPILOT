from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.models import Base, Shop, Product, Inventory, Purchase, PurchaseItem, Sale, SaleItem, BusinessInsight

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_sqlite_db_and_seed(db_engine=engine):
    """
    Automatic table creation and seed data are allowed ONLY for local SQLite development/testing.
    Never automatically create, drop, recreate, or seed a production PostgreSQL/Supabase database.
    """
    if db_engine.name != "sqlite":
        return

    Base.metadata.create_all(bind=db_engine)

    # Seed demo data if database is empty
    db = SessionLocal()
    try:
        shop_exists = db.query(Shop).filter(Shop.id == "shop_001").first()
        if not shop_exists:
            # Create shop
            shop = Shop(
                id="shop_001",
                name="Sri Lakshmi General Store",
                owner_name="Ramesh Kumar",
                phone="+91-9876543210",
                latitude=17.4399,
                longitude=78.4483,
                locality="Ameerpet",
                city="Hyderabad"
            )
            db.add(shop)

            # Create products
            products_data = [
                ("prod_001", "Coca-Cola 250ml", "Beverages", "Coca-Cola", "bottle", 15.00, 20.00, 15),
                ("prod_002", "Lays Classic Salted 50g", "Snacks", "Lays", "pack", 16.00, 20.00, 20),
                ("prod_003", "Amul Taaza Milk 500ml", "Dairy", "Amul", "packet", 24.00, 27.00, 10),
                ("prod_004", "Tata Salt 1kg", "Staples", "Tata", "pack", 22.00, 28.00, 10),
                ("prod_005", "Surf Excel Easy Wash 500g", "Personal & Home Care", "Unilever", "pack", 62.00, 72.00, 5),
                ("prod_006", "Thums Up 750ml", "Beverages", "Coca-Cola", "bottle", 32.00, 40.00, 12),
                ("prod_007", "Parle-G Gold 100g", "Snacks", "Parle", "pack", 8.50, 10.00, 25),
                ("prod_008", "Maggi 2-Min Noodles 70g", "Snacks", "Nestle", "pack", 11.50, 14.00, 20),
            ]
            for p_id, p_name, cat, brand, unit, p_price, s_price, reorder in products_data:
                db.add(Product(
                    id=p_id, name=p_name, category=cat, brand=brand, unit=unit,
                    purchase_price=p_price, selling_price=s_price, reorder_level=reorder
                ))

            # Initial inventory
            inventory_data = [
                ("inv_001", "prod_001", 6),
                ("inv_002", "prod_002", 45),
                ("inv_003", "prod_003", 8),
                ("inv_004", "prod_004", 30),
                ("inv_005", "prod_005", 4),
                ("inv_006", "prod_006", 22),
                ("inv_007", "prod_007", 80),
                ("inv_008", "prod_008", 50),
            ]
            for inv_id, prod_id, qty in inventory_data:
                db.add(Inventory(
                    id=inv_id, shop_id="shop_001", product_id=prod_id, quantity=qty
                ))

            # Historical purchase
            purch = Purchase(
                id="purch_001", shop_id="shop_001", supplier_name="Sri Venkateswara Wholesale Depot",
                invoice_number="INV-2026-0801", total_amount=4520.00
            )
            db.add(purch)
            db.add(PurchaseItem(id="pi_001", purchase_id="purch_001", product_id="prod_001", quantity=100, unit_cost=15.00))
            db.add(PurchaseItem(id="pi_002", purchase_id="purch_001", product_id="prod_002", quantity=100, unit_cost=16.00))
            db.add(PurchaseItem(id="pi_003", purchase_id="purch_001", product_id="prod_007", quantity=160, unit_cost=8.50))

            # Historical sales
            sale1 = Sale(id="sale_001", shop_id="shop_001", total_amount=100.00, total_cost=77.00, profit=23.00, source="voice_text")
            db.add(sale1)
            db.add(SaleItem(id="si_001", sale_id="sale_001", product_id="prod_001", quantity=3, unit_price=20.00, unit_cost=15.00, profit=15.00))
            db.add(SaleItem(id="si_002", sale_id="sale_001", product_id="prod_002", quantity=2, unit_price=20.00, unit_cost=16.00, profit=8.00))

            sale2 = Sale(id="sale_002", shop_id="shop_001", total_amount=78.00, total_cost=59.00, profit=19.00, source="voice_text")
            db.add(sale2)
            db.add(SaleItem(id="si_003", sale_id="sale_002", product_id="prod_003", quantity=2, unit_price=27.00, unit_cost=24.00, profit=6.00))
            db.add(SaleItem(id="si_004", sale_id="sale_002", product_id="prod_007", quantity=2, unit_price=10.00, unit_cost=8.50, profit=3.00))
            db.add(SaleItem(id="si_005", sale_id="sale_002", product_id="prod_008", quantity=1, unit_price=14.00, unit_cost=11.50, profit=2.50))

            # Insights
            db.add(BusinessInsight(
                id="ins_001", shop_id="shop_001", type="restock",
                title="RESTOCK: Coca-Cola 250ml", description="Current stock (6) is below reorder level (15).",
                severity="warning", confidence="high"
            ))

            db.commit()
    finally:
        db.close()
