from sqlalchemy import Column, String, Text, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class Category(BaseModel):
    __tablename__ = "categories"
    name = Column(String(255), nullable=False)
    description = Column(Text)
    products = relationship("Product", back_populates="category")

class Product(BaseModel):
    __tablename__ = "products"
    category_id = Column(ForeignKey("categories.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    base_price = Column(Numeric(10, 2), nullable=False)
    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product")

class ProductVariant(BaseModel):
    __tablename__ = "product_variants"
    product_id = Column(ForeignKey("products.id"))
    sku = Column(String(100), unique=True, nullable=False)
    attributes = Column(JSON)
    price_adjustment = Column(Numeric(10, 2), default=0)
    product = relationship("Product", back_populates="variants")

