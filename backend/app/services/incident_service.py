from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.models.incident import Incident, IncidentStatus, IncidentComment, IncidentEvent, IncidentLog
from app.models.user import User
from app.models.log import LogEntry
from app.core.errors import NotFoundException, BadRequestException
from app.services.audit_service import log_audit_event

def get_incident_or_404(db: Session, incident_id: str) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise NotFoundException("Incident", incident_id)
    return incident

def transition_incident_status(
    db: Session,
    incident_id: str,
    target_status: str,
    actor: User,
    reason: Optional[str] = None
) -> Incident:
    """Executes validated incident state transitions with timeline events."""
    incident = get_incident_or_404(db, incident_id)
    current_status = incident.status

    allowed_targets = IncidentStatus.TRANSITIONS.get(current_status, [])
    if target_status not in allowed_targets:
        raise BadRequestException(
            f"Invalid status transition from '{current_status}' to '{target_status}'. "
            f"Allowed transitions: {allowed_targets}"
        )

    now = datetime.now(timezone.utc)
    incident.status = target_status
    incident.updated_at = now

    event_type = target_status
    if target_status == IncidentStatus.ACKNOWLEDGED:
        incident.acknowledged_at = now
    elif target_status == IncidentStatus.RESOLVED:
        incident.resolved_at = now
    elif target_status == IncidentStatus.OPEN and current_status == IncidentStatus.RESOLVED:
        event_type = "REOPENED"
        incident.resolved_at = None

    # Record Timeline Event
    event = IncidentEvent(
        incident_id=incident.id,
        event_type=event_type,
        actor_id=actor.id,
        actor_name=actor.full_name,
        details_json={
            "previous_status": current_status,
            "new_status": target_status,
            "reason": reason or "Status updated by user"
        },
        created_at=now
    )
    db.add(event)

    # Record Audit Log
    log_audit_event(
        db=db,
        actor_email=actor.email,
        actor_role=actor.role,
        action=f"INCIDENT_STATUS_{target_status}",
        target_type="incident",
        target_id=incident.id,
        details={"previous": current_status, "new": target_status, "reason": reason}
    )

    db.commit()
    db.refresh(incident)
    return incident

def assign_incident(
    db: Session,
    incident_id: str,
    assigned_user_id: Optional[str],
    actor: User
) -> Incident:
    incident = get_incident_or_404(db, incident_id)
    assigned_user_name = "Unassigned"
    
    if assigned_user_id:
        target_user = db.query(User).filter(User.id == assigned_user_id).first()
        if not target_user:
            raise NotFoundException("User to assign", assigned_user_id)
        assigned_user_name = target_user.full_name

    incident.assigned_user_id = assigned_user_id
    incident.updated_at = datetime.now(timezone.utc)

    db.add(IncidentEvent(
        incident_id=incident.id,
        event_type="ASSIGNED",
        actor_id=actor.id,
        actor_name=actor.full_name,
        details_json={"assigned_user_id": assigned_user_id, "assigned_to": assigned_user_name},
        created_at=datetime.now(timezone.utc)
    ))

    log_audit_event(
        db=db,
        actor_email=actor.email,
        actor_role=actor.role,
        action="INCIDENT_ASSIGN",
        target_type="incident",
        target_id=incident.id,
        details={"assigned_to": assigned_user_name}
    )

    db.commit()
    db.refresh(incident)
    return incident

def add_incident_comment(
    db: Session,
    incident_id: str,
    comment_text: str,
    actor: User
) -> IncidentComment:
    incident = get_incident_or_404(db, incident_id)
    
    comment = IncidentComment(
        incident_id=incident.id,
        user_id=actor.id,
        comment=comment_text,
        created_at=datetime.now(timezone.utc)
    )
    db.add(comment)
    db.flush()

    db.add(IncidentEvent(
        incident_id=incident.id,
        event_type="COMMENTED",
        actor_id=actor.id,
        actor_name=actor.full_name,
        details_json={"comment_id": comment.id, "preview": comment_text[:80]},
        created_at=datetime.now(timezone.utc)
    ))

    db.commit()
    db.refresh(comment)
    return comment

def get_incident_details(db: Session, incident_id: str) -> dict:
    """Returns complete incident detail bundle with timeline, comments, and related logs."""
    incident = get_incident_or_404(db, incident_id)

    # Fetch related logs through IncidentLog
    related_logs_entries = db.query(LogEntry).join(
        IncidentLog, IncidentLog.log_id == LogEntry.id
    ).filter(
        IncidentLog.incident_id == incident.id
    ).order_by(desc(LogEntry.timestamp)).limit(50).all()

    related_logs = [
        {
            "id": l.id,
            "timestamp": l.timestamp.isoformat(),
            "service_name": l.service_name,
            "environment": l.environment,
            "severity": l.severity,
            "message": l.message,
            "trace_id": l.trace_id,
            "metadata": l.metadata_json
        }
        for l in related_logs_entries
    ]

    return {
        "incident": incident,
        "comments": incident.comments,
        "timeline": incident.timeline_events,
        "related_logs": related_logs
    }
