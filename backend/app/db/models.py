from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, Numeric, DateTime, Text, ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Shop(Base):
    __tablename__ = "shops"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    owner_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    locality = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    inventory_items = relationship("Inventory", back_populates="shop", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="shop", cascade="all, delete-orphan")
    purchases = relationship("Purchase", back_populates="shop", cascade="all, delete-orphan")
    insights = relationship("BusinessInsight", back_populates="shop", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True)
    shop_id = Column(String(36), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    sku = Column(String(100), nullable=True)
    name = Column(String(255), nullable=False)
    aliases = Column(String(500), nullable=True)
    category = Column(String(100), nullable=False)
    brand = Column(String(100), nullable=True)
    unit = Column(String(50), default="unit")
    purchase_price = Column(Numeric(12, 2), nullable=False, default=0.00)
    selling_price = Column(Numeric(12, 2), nullable=False, default=0.00)
    reorder_level = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("shop_id", "sku", name="unique_shop_sku"),
    )

    shop = relationship("Shop", back_populates="products")
    inventory_items = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(String(36), primary_key=True)
    shop_id = Column(String(36), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("shop_id", "product_id", name="unique_shop_product"),
        CheckConstraint("quantity >= 0", name="chk_quantity_non_negative"),
    )

    shop = relationship("Shop", back_populates="inventory_items")
    product = relationship("Product", back_populates="inventory_items")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(String(36), primary_key=True)
    shop_id = Column(String(36), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    total_cost = Column(Numeric(12, 2), nullable=False, default=0.00)
    profit = Column(Numeric(12, 2), nullable=False, default=0.00)
    source = Column(String(50), nullable=False, default="voice_text")
    created_at = Column(DateTime, default=datetime.utcnow)

    shop = relationship("Shop", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(String(36), primary_key=True)
    sale_id = Column(String(36), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0.00)
    unit_cost = Column(Numeric(12, 2), nullable=False, default=0.00)
    profit = Column(Numeric(12, 2), nullable=False, default=0.00)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(String(36), primary_key=True)
    shop_id = Column(String(36), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    supplier_name = Column(String(255), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    invoice_image_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    shop = relationship("Shop", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(String(36), primary_key=True)
    purchase_id = Column(String(36), ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_cost = Column(Numeric(12, 2), nullable=False, default=0.00)

    purchase = relationship("Purchase", back_populates="items")
    product = relationship("Product")


class BusinessInsight(Base):
    __tablename__ = "business_insights"

    id = Column(String(36), primary_key=True)
    shop_id = Column(String(36), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False, default="info")
    confidence = Column(String(50), nullable=False, default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)

    shop = relationship("Shop", back_populates="insights")
