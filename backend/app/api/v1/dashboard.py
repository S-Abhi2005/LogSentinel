from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummary, LogVolumePoint, SeverityBreakdown,
    IncidentTrendPoint, ServiceIncidentCount, ServiceHealthStatus, DashboardData
)
from app.security.rbac import require_viewer_or_above
from app.services.dashboard_service import (
    get_dashboard_summary, get_log_trends, get_severity_breakdown,
    get_incident_trends, get_incidents_by_service, get_services_health_summary
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Metrics"])

@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    return get_dashboard_summary(db)

@router.get("/log-trends", response_model=List[LogVolumePoint])
def dashboard_log_trends(
    hours: int = 24,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    return get_log_trends(db, hours)

@router.get("/severity-breakdown", response_model=List[SeverityBreakdown])
def dashboard_severity_breakdown(
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    return get_severity_breakdown(db)

@router.get("/incident-trends", response_model=List[IncidentTrendPoint])
def dashboard_incident_trends(
    days: int = 7,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    return get_incident_trends(db, days)

@router.get("/service-health", response_model=List[ServiceHealthStatus])
def dashboard_service_health(
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    return get_services_health_summary(db)

@router.get("/all", response_model=DashboardData)
def dashboard_all_data(
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    """High-performance consolidated dashboard endpoint."""
    return DashboardData(
        summary=get_dashboard_summary(db),
        log_volume=get_log_trends(db, 24),
        severity_breakdown=get_severity_breakdown(db),
        incident_trends=get_incident_trends(db, 7),
        incidents_by_service=get_incidents_by_service(db),
        service_health=get_services_health_summary(db)
    )
