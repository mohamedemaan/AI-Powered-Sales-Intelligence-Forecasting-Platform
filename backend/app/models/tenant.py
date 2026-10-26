import enum
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, JSON, Uuid, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class TenantMemberRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"
    MEMBER = "MEMBER"

class Tenant(BaseModel):
    __tablename__ = "tenants"
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=True)
    owner_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    stripe_customer_id = Column(String(255), unique=True, index=True)
    subscription_tier = Column(String(50), default="FREE") # FREE, PRO, BUSINESS, ENTERPRISE
    subscription_status = Column(String(50), default="ACTIVE")
    current_period_end = Column(String(50))
    api_calls_count = Column(Integer, default=0)
    forecasts_count = Column(Integer, default=0)

    # Relationships
    members = relationship("TenantMember", back_populates="tenant", cascade="all, delete-orphan")


class TenantMember(BaseModel):
    __tablename__ = "tenant_members"
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), default="MEMBER", nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user_membership"),
    )

    tenant = relationship("Tenant", back_populates="members")
    user = relationship("User", back_populates="memberships")


# Enterprise SaaS aliases
Organization = Tenant
OrganizationMember = TenantMember
OrganizationMemberRole = TenantMemberRole
