from typing import Any
from fastapi import APIRouter, Depends
from app.api import deps
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_user),
    current_tenant: Any = Depends(deps.get_current_tenant)
) -> Any:
    return current_user
