from sqlalchemy import Column, String, Integer, Numeric, Date, ForeignKey
from app.db.base import BaseModel

class RawSalesData(BaseModel):
    __tablename__ = "raw_sales_data"
    date = Column(Date, nullable=False, index=True)
    order_id = Column(String(100), nullable=True, index=True)
    sku = Column(String(100), nullable=False, index=True)
    product_name = Column(String(255), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    sub_category = Column(String(100), nullable=True, index=True)
    units_sold = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2))
    total_sales = Column(Numeric(12, 2), nullable=True)
    profit = Column(Numeric(12, 2), nullable=True)
    discount_pct = Column(Numeric(5, 2))
    available_stock = Column(Integer)
    holiday_flag = Column(Integer, default=0)
    festival_flag = Column(Integer, default=0)
    status = Column(String(50), default="PENDING") # PENDING, PROCESSED, ERROR
