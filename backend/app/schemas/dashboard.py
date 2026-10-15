from typing import List, Dict, Any
from pydantic import BaseModel

class DashboardSummary(BaseModel):
    total_logs: int
    error_logs: int
    active_incidents: int
    critical_incidents: int
    healthy_services: int
    total_services: int
    unacknowledged_alerts: int

class LogVolumePoint(BaseModel):
    timestamp: str
    count: int
    errors: int

class SeverityBreakdown(BaseModel):
    severity: str
    count: int

class IncidentTrendPoint(BaseModel):
    date: str
    opened: int
    resolved: int

class ServiceIncidentCount(BaseModel):
    service_name: str
    incident_count: int

class ServiceHealthStatus(BaseModel):
    service_id: str
    service_name: str
    environment: str
    status: str  # HEALTHY, DEGRADED, CRITICAL, UNKNOWN
    active_incidents: int
    error_count_last_hour: int
    last_log_at: Any = None

class DashboardData(BaseModel):
    summary: DashboardSummary
    log_volume: List[LogVolumePoint]
    severity_breakdown: List[SeverityBreakdown]
    incident_trends: List[IncidentTrendPoint]
    incidents_by_service: List[ServiceIncidentCount]
    service_health: List[ServiceHealthStatus]
