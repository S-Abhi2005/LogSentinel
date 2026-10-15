from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

from app.models.log import LogEntry, LogSeverity
from app.models.incident import Incident, IncidentStatus, IncidentSeverity
from app.models.service import Service
from app.models.alert import Alert
from app.services.service_registry import compute_service_health

def get_dashboard_summary(db: Session) -> Dict[str, Any]:
    """Retrieves high-level summary statistics using optimized SQL aggregations."""
    total_logs = db.query(func.count(LogEntry.id)).scalar() or 0
    error_logs = db.query(func.count(LogEntry.id)).filter(
        LogEntry.severity.in_([LogSeverity.ERROR, LogSeverity.CRITICAL])
    ).scalar() or 0

    active_incidents = db.query(func.count(Incident.id)).filter(
        Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED, IncidentStatus.INVESTIGATING])
    ).scalar() or 0

    critical_incidents = db.query(func.count(Incident.id)).filter(
        Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED, IncidentStatus.INVESTIGATING]),
        Incident.severity == IncidentSeverity.CRITICAL
    ).scalar() or 0

    services = db.query(Service).all()
    healthy_count = 0
    for s in services:
        h = compute_service_health(db, s)
        if h["status"] == "HEALTHY":
            healthy_count += 1

    unack_alerts = db.query(func.count(Alert.id)).filter(Alert.is_read == False).scalar() or 0

    return {
        "total_logs": total_logs,
        "error_logs": error_logs,
        "active_incidents": active_incidents,
        "critical_incidents": critical_incidents,
        "healthy_services": healthy_count,
        "total_services": len(services),
        "unacknowledged_alerts": unack_alerts,
    }

def get_log_trends(db: Session, hours: int = 24) -> List[Dict[str, Any]]:
    """Calculates log volume and error volume grouped into hourly time windows."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours)

    logs = db.query(
        LogEntry.timestamp,
        LogEntry.severity
    ).filter(
        LogEntry.timestamp >= start_time
    ).order_by(LogEntry.timestamp.asc()).all()

    # Bucket into hourly slots
    buckets: Dict[str, Dict[str, int]] = {}
    for i in range(hours):
        t = start_time + timedelta(hours=i)
        key = t.strftime("%H:00")
        buckets[key] = {"count": 0, "errors": 0}

    for log in logs:
        key = log.timestamp.strftime("%H:00")
        if key in buckets:
            buckets[key]["count"] += 1
            if log.severity in [LogSeverity.ERROR, LogSeverity.CRITICAL]:
                buckets[key]["errors"] += 1

    return [{"timestamp": k, "count": v["count"], "errors": v["errors"]} for k, v in buckets.items()]

def get_severity_breakdown(db: Session) -> List[Dict[str, Any]]:
    """Counts logs grouped by severity."""
    rows = db.query(
        LogEntry.severity,
        func.count(LogEntry.id)
    ).group_by(LogEntry.severity).all()

    counts = {r[0]: r[1] for r in rows}
    severities = [LogSeverity.CRITICAL, LogSeverity.ERROR, LogSeverity.WARNING, LogSeverity.INFO, LogSeverity.DEBUG]
    return [{"severity": s, "count": counts.get(s, 0)} for s in severities]

def get_incident_trends(db: Session, days: int = 7) -> List[Dict[str, Any]]:
    """Counts incidents created vs resolved over the past N days."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=days)

    incidents = db.query(Incident).filter(
        Incident.created_at >= start_time
    ).all()

    buckets: Dict[str, Dict[str, int]] = {}
    for i in range(days):
        d = (start_time + timedelta(days=i)).strftime("%b %d")
        buckets[d] = {"opened": 0, "resolved": 0}

    for inc in incidents:
        open_day = inc.first_detected_at.strftime("%b %d")
        if open_day in buckets:
            buckets[open_day]["opened"] += 1
        if inc.resolved_at:
            res_day = inc.resolved_at.strftime("%b %d")
            if res_day in buckets:
                buckets[res_day]["resolved"] += 1

    return [{"date": k, "opened": v["opened"], "resolved": v["resolved"]} for k, v in buckets.items()]

def get_incidents_by_service(db: Session) -> List[Dict[str, Any]]:
    """Calculates active incident count grouped by service."""
    rows = db.query(
        Service.name,
        func.count(Incident.id)
    ).join(
        Incident, Incident.service_id == Service.id
    ).group_by(Service.name).all()

    return [{"service_name": r[0], "incident_count": r[1]} for r in rows]

def get_services_health_summary(db: Session) -> List[Dict[str, Any]]:
    """Returns detailed health status list for all services."""
    services = db.query(Service).all()
    results = []
    for s in services:
        h = compute_service_health(db, s)
        results.append({
            "service_id": s.id,
            "service_name": s.name,
            "environment": s.environment,
            "status": h["status"],
            "active_incidents": h["active_incidents_count"],
            "error_count_last_hour": h["recent_error_count"],
            "last_log_at": s.last_log_at.isoformat() if s.last_log_at else None
        })
    return results
