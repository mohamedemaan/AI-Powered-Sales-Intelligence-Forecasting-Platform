from sqlalchemy import Column, String, Numeric, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class Order(BaseModel):
    __tablename__ = "orders"
    user_id = Column(ForeignKey("users.id"))
    status = Column(String(50), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    items = relationship("OrderItem", back_populates="order")
    user = relationship("User")

class OrderItem(BaseModel):
    __tablename__ = "order_items"
    order_id = Column(ForeignKey("orders.id"))
    variant_id = Column(ForeignKey("product_variants.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    order = relationship("Order", back_populates="items")
    variant = relationship("ProductVariant")
