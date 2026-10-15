from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.db.session import get_db
from app.models.user import User
from app.models.service import Service
from app.models.incident import Incident, IncidentStatus, IncidentComment, IncidentEvent
from app.schemas.incident import (
    IncidentResponse, IncidentDetailResponse, IncidentCommentCreate,
    IncidentCommentResponse, IncidentAssignRequest, IncidentListResponse
)
from app.security.rbac import require_viewer_or_above, require_engineer_or_admin
from app.services.incident_service import (
    transition_incident_status, assign_incident, add_incident_comment, get_incident_details
)
from app.core.errors import NotFoundException

router = APIRouter(prefix="/incidents", tags=["Incident Management"])

@router.get("", response_model=IncidentListResponse)
def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    service_id: Optional[str] = None,
    environment: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    query = db.query(Incident)

    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
    if service_id:
        query = query.filter(Incident.service_id == service_id)
    if environment:
        query = query.filter(Incident.environment == environment)
    if search:
        query = query.filter(Incident.title.ilike(f"%{search}%"))

    total = query.count()
    offset = (page - 1) * page_size
    incidents = query.order_by(desc(Incident.last_detected_at)).offset(offset).limit(page_size).all()

    items = []
    for inc in incidents:
        items.append(IncidentResponse(
            id=inc.id,
            title=inc.title,
            description=inc.description,
            severity=inc.severity,
            status=inc.status,
            service_id=inc.service_id,
            service_name=inc.service.name if inc.service else "Unknown",
            environment=inc.environment,
            rule_id=inc.rule_id,
            rule_name=inc.rule.name if inc.rule else None,
            fingerprint=inc.fingerprint,
            error_signature=inc.error_signature,
            first_detected_at=inc.first_detected_at,
            last_detected_at=inc.last_detected_at,
            acknowledged_at=inc.acknowledged_at,
            resolved_at=inc.resolved_at,
            assigned_user_id=inc.assigned_user_id,
            assigned_user_name=inc.assigned_user.full_name if inc.assigned_user else None,
            event_count=inc.event_count,
            created_at=inc.created_at,
            updated_at=inc.updated_at
        ))

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return IncidentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident(
    incident_id: str,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    bundle = get_incident_details(db, incident_id)
    inc = bundle["incident"]
    
    comments_resp = [
        IncidentCommentResponse(
            id=c.id,
            incident_id=c.incident_id,
            user_id=c.user_id,
            user_name=c.user.full_name if c.user else "Unknown",
            user_email=c.user.email if c.user else "",
            comment=c.comment,
            created_at=c.created_at
        )
        for c in bundle["comments"]
    ]

    return IncidentDetailResponse(
        id=inc.id,
        title=inc.title,
        description=inc.description,
        severity=inc.severity,
        status=inc.status,
        service_id=inc.service_id,
        service_name=inc.service.name if inc.service else "Unknown",
        environment=inc.environment,
        rule_id=inc.rule_id,
        rule_name=inc.rule.name if inc.rule else None,
        fingerprint=inc.fingerprint,
        error_signature=inc.error_signature,
        first_detected_at=inc.first_detected_at,
        last_detected_at=inc.last_detected_at,
        acknowledged_at=inc.acknowledged_at,
        resolved_at=inc.resolved_at,
        assigned_user_id=inc.assigned_user_id,
        assigned_user_name=inc.assigned_user.full_name if inc.assigned_user else None,
        event_count=inc.event_count,
        created_at=inc.created_at,
        updated_at=inc.updated_at,
        comments=comments_resp,
        timeline=bundle["timeline"],
        related_logs=bundle["related_logs"]
    )

@router.post("/{incident_id}/acknowledge", response_model=IncidentResponse)
def acknowledge_incident(
    incident_id: str,
    current_user: User = Depends(require_engineer_or_admin),
    db: Session = Depends(get_db)
):
    inc = transition_incident_status(
        db=db,
        incident_id=incident_id,
        target_status=IncidentStatus.ACKNOWLEDGED,
        actor=current_user,
        reason="Incident acknowledged by on-call engineer"
    )
    return inc

@router.post("/{incident_id}/investigate", response_model=IncidentResponse)
def investigate_incident(
    incident_id: str,
    current_user: User = Depends(require_engineer_or_admin),
    db: Session = Depends(get_db)
):
    inc = transition_incident_status(
        db=db,
        incident_id=incident_id,
        target_status=IncidentStatus.INVESTIGATING,
        actor=current_user,
        reason="Investigation in progress"
    )
    return inc

@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
def resolve_incident(
    incident_id: str,
    reason: Optional[str] = "Incident resolved",
    current_user: User = Depends(require_engineer_or_admin),
    db: Session = Depends(get_db)
):
    inc = transition_incident_status(
        db=db,
        incident_id=incident_id,
        target_status=IncidentStatus.RESOLVED,
        actor=current_user,
        reason=reason
    )
    return inc

@router.post("/{incident_id}/reopen", response_model=IncidentResponse)
def reopen_incident(
    incident_id: str,
    reason: Optional[str] = "Incident reopened for further investigation",
    current_user: User = Depends(require_engineer_or_admin),
    db: Session = Depends(get_db)
):
    inc = transition_incident_status(
        db=db,
        incident_id=incident_id,
        target_status=IncidentStatus.OPEN,
        actor=current_user,
        reason=reason
    )
    return inc

@router.post("/{incident_id}/assign", response_model=IncidentResponse)
def assign_incident_route(
    incident_id: str,
    data: IncidentAssignRequest,
    current_user: User = Depends(require_engineer_or_admin),
    db: Session = Depends(get_db)
):
    inc = assign_incident(
        db=db,
        incident_id=incident_id,
        assigned_user_id=data.assigned_user_id,
        actor=current_user
    )
    return inc

@router.post("/{incident_id}/comments", response_model=IncidentCommentResponse, status_code=status.HTTP_201_CREATED)
def post_incident_comment(
    incident_id: str,
    data: IncidentCommentCreate,
    current_user: User = Depends(require_engineer_or_admin),
    db: Session = Depends(get_db)
):
    comment = add_incident_comment(
        db=db,
        incident_id=incident_id,
        comment_text=data.comment,
        actor=current_user
    )
    return IncidentCommentResponse(
        id=comment.id,
        incident_id=comment.incident_id,
        user_id=comment.user_id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        comment=comment.comment,
        created_at=comment.created_at
    )
