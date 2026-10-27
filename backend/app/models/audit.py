from sqlalchemy import Column, String, ForeignKey, JSON, Uuid, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import BaseModel

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_email = Column(String(255), nullable=True)
    event_type = Column(String(100), nullable=False, index=True)
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(100), nullable=True)
    outcome = Column(String(20), default="SUCCESS", nullable=False)
    ip_address = Column(String(50), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    tenant = relationship("Tenant")
    actor = relationship("User", foreign_keys=[actor_id])

