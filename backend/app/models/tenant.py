from sqlalchemy import Column, String, Integer, Boolean
from app.db.base import BaseModel

class Tenant(BaseModel):
    __tablename__ = "tenants"
    name = Column(String(255), nullable=False)
    stripe_customer_id = Column(String(255), unique=True, index=True)
    subscription_tier = Column(String(50), default="FREE") # FREE, PRO, BUSINESS, ENTERPRISE
    subscription_status = Column(String(50), default="ACTIVE")
    current_period_end = Column(String(50))
    api_calls_count = Column(Integer, default=0)
    forecasts_count = Column(Integer, default=0)
    
    # In a full implementation, all other models (User, Product, etc.) 
    # would receive a tenant_id = Column(UUID, ForeignKey("tenants.id"))
