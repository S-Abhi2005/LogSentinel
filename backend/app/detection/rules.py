from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.rule import IncidentRule, RuleType
from app.models.service import Service
from app.models.log import LogEntry, LogSeverity
from app.detection.deduplication import process_incident_deduplication
from app.models.incident import Incident

def evaluate_error_threshold_rule(
    db: Session,
    rule: IncidentRule,
    service: Service,
    environment: str,
    ingested_logs: List[LogEntry],
    reference_time: datetime
) -> Optional[tuple[Incident, bool]]:
    """Rule 1: Error Threshold (e.g. >= 10 ERROR logs in 5 minutes)"""
    window_start = reference_time - timedelta(seconds=rule.time_window_seconds)
    
    # Query database for matching error logs in time window
    error_logs = db.query(LogEntry).filter(
        LogEntry.service_id == service.id,
        LogEntry.environment == environment,
        LogEntry.severity.in_([LogSeverity.ERROR, LogSeverity.CRITICAL]),
        LogEntry.timestamp >= window_start,
        LogEntry.timestamp <= reference_time
    ).order_by(LogEntry.timestamp.desc()).all()

    if len(error_logs) >= int(rule.threshold):
        title = f"High Error Count on {service.name}: {len(error_logs)} errors detected"
        description = (
            f"Service '{service.name}' exceeded error threshold rule '{rule.name}'. "
            f"Observed {len(error_logs)} error/critical events within {rule.time_window_seconds}s "
            f"(threshold: {rule.threshold})."
        )
        return process_incident_deduplication(
            db=db,
            rule=rule,
            service_id=service.id,
            service_name=service.name,
            environment=environment,
            title=title,
            description=description,
            severity=rule.severity,
            error_signature=f"error_threshold_exceeded_{rule.id}",
            triggering_logs=error_logs[:20],  # link recent triggering logs
            event_timestamp=reference_time
        )
    return None

def evaluate_critical_log_rule(
    db: Session,
    rule: IncidentRule,
    service: Service,
    environment: str,
    ingested_logs: List[LogEntry],
    reference_time: datetime
) -> Optional[tuple[Incident, bool]]:
    """Rule 2: Critical Log (Immediate trigger on CRITICAL severity)"""
    critical_logs = [
        log for log in ingested_logs 
        if log.severity == LogSeverity.CRITICAL 
        and log.environment == environment
    ]
    
    if critical_logs:
        triggering = critical_logs[0]
        title = f"CRITICAL Log Detected on {service.name}: {triggering.message[:80]}"
        description = (
            f"Rule '{rule.name}' triggered immediately upon receiving a CRITICAL severity log: "
            f"'{triggering.message}' (trace: {triggering.trace_id or 'none'})"
        )
        return process_incident_deduplication(
            db=db,
            rule=rule,
            service_id=service.id,
            service_name=service.name,
            environment=environment,
            title=title,
            description=description,
            severity=rule.severity,
            error_signature=f"critical_log_{triggering.source or 'default'}",
            triggering_logs=critical_logs,
            event_timestamp=triggering.timestamp or reference_time
        )
    return None

def evaluate_repeated_failure_rule(
    db: Session,
    rule: IncidentRule,
    service: Service,
    environment: str,
    ingested_logs: List[LogEntry],
    reference_time: datetime
) -> Optional[tuple[Incident, bool]]:
    """Rule 3: Repeated Failure with matching signature or pattern"""
    window_start = reference_time - timedelta(seconds=rule.time_window_seconds)
    
    query = db.query(LogEntry).filter(
        LogEntry.service_id == service.id,
        LogEntry.environment == environment,
        LogEntry.severity.in_([LogSeverity.ERROR, LogSeverity.CRITICAL]),
        LogEntry.timestamp >= window_start,
        LogEntry.timestamp <= reference_time
    )

    if rule.error_signature_pattern:
        query = query.filter(LogEntry.message.ilike(f"%{rule.error_signature_pattern}%"))
    
    matching_logs = query.order_by(LogEntry.timestamp.desc()).all()

    if len(matching_logs) >= int(rule.threshold):
        sig = rule.error_signature_pattern or (matching_logs[0].message[:50] if matching_logs else "repeated_failure")
        title = f"Repeated Failure on {service.name} [{sig[:40]}]"
        description = (
            f"Rule '{rule.name}' detected {len(matching_logs)} repeated failures "
            f"matching signature pattern '{sig}' within {rule.time_window_seconds}s."
        )
        return process_incident_deduplication(
            db=db,
            rule=rule,
            service_id=service.id,
            service_name=service.name,
            environment=environment,
            title=title,
            description=description,
            severity=rule.severity,
            error_signature=f"repeated_{sig}",
            triggering_logs=matching_logs[:20],
            event_timestamp=reference_time
        )
    return None

def evaluate_error_rate_rule(
    db: Session,
    rule: IncidentRule,
    service: Service,
    environment: str,
    ingested_logs: List[LogEntry],
    reference_time: datetime
) -> Optional[tuple[Incident, bool]]:
    """Rule 4: Service Error Rate (errors / total logs over time window)"""
    window_start = reference_time - timedelta(seconds=rule.time_window_seconds)

    total_count = db.query(func.count(LogEntry.id)).filter(
        LogEntry.service_id == service.id,
        LogEntry.environment == environment,
        LogEntry.timestamp >= window_start,
        LogEntry.timestamp <= reference_time
    ).scalar() or 0

    # Enforce minimum event count (5) to avoid false positives
    if total_count < 5:
        return None

    error_logs = db.query(LogEntry).filter(
        LogEntry.service_id == service.id,
        LogEntry.environment == environment,
        LogEntry.severity.in_([LogSeverity.ERROR, LogSeverity.CRITICAL]),
        LogEntry.timestamp >= window_start,
        LogEntry.timestamp <= reference_time
    ).order_by(LogEntry.timestamp.desc()).all()

    error_count = len(error_logs)
    error_rate = error_count / total_count

    # rule.threshold is e.g. 0.20 for 20% error rate
    threshold = rule.threshold if rule.threshold <= 1.0 else (rule.threshold / 100.0)

    if error_rate >= threshold:
        pct = round(error_rate * 100, 1)
        title = f"Elevated Error Rate ({pct}%) on {service.name}"
        description = (
            f"Service '{service.name}' exceeded error rate threshold rule '{rule.name}'. "
            f"Current error rate: {pct}% ({error_count} errors out of {total_count} total logs in {rule.time_window_seconds}s)."
        )
        return process_incident_deduplication(
            db=db,
            rule=rule,
            service_id=service.id,
            service_name=service.name,
            environment=environment,
            title=title,
            description=description,
            severity=rule.severity,
            error_signature=f"error_rate_exceeded_{rule.id}",
            triggering_logs=error_logs[:15],
            event_timestamp=reference_time
        )
    return None

def evaluate_service_inactivity_rule(
    db: Session,
    rule: IncidentRule,
    service: Service,
    reference_time: datetime
) -> Optional[tuple[Incident, bool]]:
    """Rule 5: Service Inactivity (Missing expected telemetry)"""
    # Only active, non-disabled services that have produced logs previously
    if not service.is_enabled or not service.last_log_at:
        return None

    inactivity_seconds = (reference_time - service.last_log_at).total_seconds()
    if inactivity_seconds >= rule.time_window_seconds:
        title = f"Telemetry Inactivity Alert: {service.name} is silent"
        description = (
            f"Service '{service.name}' has not produced any logs for {int(inactivity_seconds)}s "
            f"(configured inactivity limit: {rule.time_window_seconds}s). Last received log at {service.last_log_at.isoformat()}."
        )
        return process_incident_deduplication(
            db=db,
            rule=rule,
            service_id=service.id,
            service_name=service.name,
            environment=service.environment,
            title=title,
            description=description,
            severity=rule.severity,
            error_signature=f"service_inactivity_{service.id}",
            triggering_logs=[],
            event_timestamp=reference_time
        )
    return None
