from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderResponse
from app.models.user import User

router = APIRouter()

@router.post("", response_model=OrderResponse)
def create_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: OrderCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    db_order = Order(
        user_id=order_in.user_id,
        status=order_in.status,
        total_amount=order_in.total_amount
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    # Order items not processed for simplicity of the example
    return db_order

@router.get("", response_model=List[OrderResponse])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    # Allow admin to see all, normal user only their own
    if current_user.role == "ADMIN":
        orders = db.query(Order).offset(skip).limit(limit).all()
    else:
        orders = db.query(Order).filter(Order.user_id == current_user.id).offset(skip).limit(limit).all()
    return orders
