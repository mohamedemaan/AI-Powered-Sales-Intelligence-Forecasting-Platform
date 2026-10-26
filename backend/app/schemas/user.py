from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.user import UserRole
import re

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    role: UserRole = UserRole.ANALYST
    tenant_id: Optional[UUID] = None

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def password_strong(cls, v):
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"[0-9]", v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r"[\W_]", v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
