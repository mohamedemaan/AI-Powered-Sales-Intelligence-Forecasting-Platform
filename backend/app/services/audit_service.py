import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {
    "password", "token", "token_hash", "raw_token", "secret",
    "authorization", "api_key", "password_hash", "access_token",
    "refresh_token", "cookie"
}

def sanitize_metadata(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Recursively strips or masks any sensitive authentication tokens,
    passwords, hashes, or secret keys from contextual metadata.
    """
    if not data or not isinstance(data, dict):
        return None

    clean = {}
    for k, v in data.items():
        lower_k = str(k).lower()
        if any(sensitive in lower_k for sensitive in SENSITIVE_KEYS):
            clean[k] = "[REDACTED]"
        elif isinstance(v, dict):
            clean[k] = sanitize_metadata(v)
        elif isinstance(v, (str, int, float, bool)) or v is None:
            clean[k] = v
        else:
            clean[k] = str(v)
    return clean

def log_audit_event(
    db: Session,
    tenant_id: UUID,
    actor_id: Optional[UUID],
    actor_email: Optional[str],
    event_type: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    outcome: str = "SUCCESS",
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[AuditLog]:
    """
    Emits an organization-scoped audit log entry.
    Guarantees that sensitive credentials are never stored.
    Non-blocking: catches internal errors so core business flow is not interrupted.
    """
    try:
        clean_meta = sanitize_metadata(metadata)
        entry = AuditLog(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_email=actor_email,
            event_type=event_type,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            outcome=outcome,
            ip_address=ip_address,
            metadata_json=clean_meta,
            created_at=datetime.utcnow()
        )
        db.add(entry)
        db.flush()
        return entry
    except Exception as e:
        logger.warning(f"Could not record audit event '{event_type}': {e}")
        return None

