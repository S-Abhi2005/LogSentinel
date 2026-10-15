from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.service import Service, ServiceIngestionKey
from app.models.incident import Incident, IncidentStatus, IncidentSeverity
from app.models.log import LogEntry, LogSeverity
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.core.errors import ConflictException, NotFoundException, BadRequestException
from app.security.hashing import generate_ingestion_key

def create_service(db: Session, data: ServiceCreate) -> Service:
    existing = db.query(Service).filter(
        Service.name == data.name,
        Service.environment == data.environment
    ).first()
    if existing:
        raise ConflictException(f"Service with name '{data.name}' already exists in environment '{data.environment}'")
    
    service = Service(
        name=data.name,
        description=data.description,
        environment=data.environment,
        owner_team=data.owner_team,
        is_enabled=True,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

def update_service(db: Session, service_id: str, data: ServiceUpdate) -> Service:
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise NotFoundException("Service", service_id)
    
    if data.description is not None:
        service.description = data.description
    if data.owner_team is not None:
        service.owner_team = data.owner_team
    if data.is_enabled is not None:
        service.is_enabled = data.is_enabled
    
    db.commit()
    db.refresh(service)
    return service

def issue_service_key(db: Session, service_id: str, key_name: str) -> tuple[ServiceIngestionKey, str]:
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise NotFoundException("Service", service_id)
    
    raw_key, prefix, key_hash = generate_ingestion_key()
    
    key_entry = ServiceIngestionKey(
        service_id=service.id,
        key_name=key_name,
        key_prefix=prefix,
        key_hash=key_hash,
        is_revoked=False
    )
    db.add(key_entry)
    db.commit()
    db.refresh(key_entry)
    
    return key_entry, raw_key

def revoke_service_key(db: Session, service_id: str, key_id: str) -> ServiceIngestionKey:
    key_entry = db.query(ServiceIngestionKey).filter(
        ServiceIngestionKey.id == key_id,
        ServiceIngestionKey.service_id == service_id
    ).first()
    if not key_entry:
        raise NotFoundException("Ingestion Key", key_id)
    
    key_entry.is_revoked = True
    db.commit()
    db.refresh(key_entry)
    return key_entry

def compute_service_health(db: Session, service: Service) -> dict:
    """Computes service health: HEALTHY, DEGRADED, CRITICAL, or UNKNOWN."""
    now = datetime.now(timezone.utc)
    
    # Check for active incidents
    active_incidents = db.query(Incident).filter(
        Incident.service_id == service.id,
        Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED, IncidentStatus.INVESTIGATING])
    ).all()

    has_critical = any(inc.severity == IncidentSeverity.CRITICAL for inc in active_incidents)
    
    one_hour_ago = now - timedelta(hours=1)
    recent_errors = db.query(func.count(LogEntry.id)).filter(
        LogEntry.service_id == service.id,
        LogEntry.severity.in_([LogSeverity.ERROR, LogSeverity.CRITICAL]),
        LogEntry.timestamp >= one_hour_ago
    ).scalar() or 0

    total_logs = db.query(func.count(LogEntry.id)).filter(
        LogEntry.service_id == service.id
    ).scalar() or 0

    if not service.last_log_at:
        status = "UNKNOWN"
    elif has_critical:
        status = "CRITICAL"
    elif len(active_incidents) > 0 or recent_errors > 10:
        status = "DEGRADED"
    else:
        status = "HEALTHY"

    return {
        "status": status,
        "active_incidents_count": len(active_incidents),
        "recent_error_count": recent_errors,
        "total_logs_count": total_logs
    }
