from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float

class ProductCreate(ProductBase):
    category_id: Optional[UUID] = None

class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime
    class Config:
        from_attributes = True
