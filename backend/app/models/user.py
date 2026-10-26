from sqlalchemy import Column, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    MANAGER = "MANAGER"

class User(BaseModel):
    __tablename__ = "users"
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ANALYST, nullable=False)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(ForeignKey("tenants.id"), nullable=True) # Nullable for global admins or during setup
