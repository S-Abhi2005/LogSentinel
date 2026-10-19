from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.service import Service, ServiceIngestionKey
from app.models.incident import Incident
from app.schemas.service import (
    ServiceCreate, ServiceUpdate, ServiceResponse, ServiceWithStatsResponse,
    IngestionKeyCreate, IngestionKeyCreatedResponse, IngestionKeyResponse
)
from app.schemas.incident import IncidentResponse
from app.security.rbac import (
    require_viewer_or_above, require_engineer_or_admin, require_super_admin
)
from app.services.service_registry import (
    create_service, update_service, issue_service_key, revoke_service_key, compute_service_health
)
from app.core.errors import NotFoundException
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/services", tags=["Services Registry"])

@router.get("", response_model=List[ServiceWithStatsResponse])
def list_services(
    environment: Optional[str] = None,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    query = db.query(Service)
    if environment:
        query = query.filter(Service.environment == environment)
    services = query.order_by(Service.name.asc()).all()

    results = []
    for s in services:
        health = compute_service_health(db, s)
        results.append(ServiceWithStatsResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            environment=s.environment,
            owner_team=s.owner_team,
            is_enabled=s.is_enabled,
            created_at=s.created_at,
            updated_at=s.updated_at,
            last_log_at=s.last_log_at,
            health_status=health["status"],
            active_incidents_count=health["active_incidents_count"],
            recent_error_count=health["recent_error_count"],
            total_logs_count=health["total_logs_count"]
        ))
    return results

@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def register_service(
    data: ServiceCreate,
    current_user: User = Depends(require_engineer_or_admin),
    db: Session = Depends(get_db)
):
    service = create_service(db, data)
    log_audit_event(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="SERVICE_CREATED",
        target_type="service",
        target_id=service.id,
        details={"name": service.name, "environment": service.environment}
    )
    db.commit()
    return service

@router.get("/{service_id}", response_model=ServiceWithStatsResponse)
def get_service_details(
    service_id: str,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise NotFoundException("Service", service_id)
    
    health = compute_service_health(db, service)
    return ServiceWithStatsResponse(
        id=service.id,
        name=service.name,
        description=service.description,
        environment=service.environment,
        owner_team=service.owner_team,
        is_enabled=service.is_enabled,
        created_at=service.created_at,
        updated_at=service.updated_at,
        last_log_at=service.last_log_at,
        health_status=health["status"],
        active_incidents_count=health["active_incidents_count"],
        recent_error_count=health["recent_error_count"],
        total_logs_count=health["total_logs_count"]
    )

@router.patch("/{service_id}", response_model=ServiceResponse)
def modify_service(
    service_id: str,
    data: ServiceUpdate,
    current_user: User = Depends(require_engineer_or_admin),
    db: Session = Depends(get_db)
):
    service = update_service(db, service_id, data)
    log_audit_event(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="SERVICE_UPDATED",
        target_type="service",
        target_id=service.id,
        details=data.model_dump(exclude_unset=True)
    )
    db.commit()
    return service

@router.post("/{service_id}/keys", response_model=IngestionKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def issue_key(
    service_id: str,
    data: IngestionKeyCreate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    key_entry, raw_key = issue_service_key(db, service_id, data.key_name)
    log_audit_event(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="INGESTION_KEY_ISSUED",
        target_type="service_ingestion_key",
        target_id=key_entry.id,
        details={"key_name": key_entry.key_name, "key_prefix": key_entry.key_prefix}
    )
    db.commit()
    return IngestionKeyCreatedResponse(
        id=key_entry.id,
        service_id=key_entry.service_id,
        key_name=key_entry.key_name,
        key_prefix=key_entry.key_prefix,
        raw_key=raw_key,
        created_at=key_entry.created_at
    )

@router.get("/{service_id}/keys", response_model=List[IngestionKeyResponse])
def list_keys(
    service_id: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    return db.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.service_id == service_id
    ).order_by(ServiceIngestionKey.created_at.desc()).all()

@router.post("/{service_id}/keys/{key_id}/revoke", response_model=IngestionKeyResponse)
def revoke_key(
    service_id: str,
    key_id: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    key_entry = revoke_service_key(db, service_id, key_id)
    log_audit_event(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="INGESTION_KEY_REVOKED",
        target_type="service_ingestion_key",
        target_id=key_entry.id,
        details={"key_name": key_entry.key_name}
    )
    db.commit()
    return key_entry

@router.get("/{service_id}/incidents", response_model=List[IncidentResponse])
def get_service_incidents(
    service_id: str,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    return db.query(Incident).filter(
        Incident.service_id == service_id
    ).order_by(Incident.last_detected_at.desc()).all()
