from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

class OrderItemCreate(BaseModel):
    variant_id: UUID
    quantity: int
    unit_price: float

class OrderCreate(BaseModel):
    user_id: UUID
    status: str
    total_amount: float
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: str
    total_amount: float
    created_at: datetime
    class Config:
        from_attributes = True
