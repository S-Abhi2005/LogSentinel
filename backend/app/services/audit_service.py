from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

def log_audit_event(
    db: Session,
    actor_email: str,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> AuditLog:
    """Creates a persistent, append-only audit log entry."""
    entry = AuditLog(
        actor_email=actor_email,
        actor_role=actor_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        correlation_id=correlation_id,
        details_json=details,
        ip_address=ip_address,
        created_at=datetime.now(timezone.utc)
    )
    db.add(entry)
    db.flush()
    return entry
