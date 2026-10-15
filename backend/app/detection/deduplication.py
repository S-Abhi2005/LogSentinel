import hashlib
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.incident import Incident, IncidentStatus, IncidentLog, IncidentEvent
from app.models.alert import Alert
from app.models.log import LogEntry
from app.models.rule import IncidentRule

def compute_incident_fingerprint(
    rule_id: Optional[str],
    service_id: str,
    environment: str,
    error_signature: Optional[str] = None
) -> str:
    """
    Computes a deterministic SHA-256 fingerprint for deduplication.
    Incidents with identical rule, service, environment, and error signature share the same fingerprint.
    """
    raw_str = f"rule={rule_id or 'none'}|service={service_id}|env={environment}|sig={error_signature or 'none'}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

def process_incident_deduplication(
    db: Session,
    rule: Optional[IncidentRule],
    service_id: str,
    service_name: str,
    environment: str,
    title: str,
    description: str,
    severity: str,
    error_signature: Optional[str],
    triggering_logs: List[LogEntry],
    event_timestamp: datetime
) -> tuple[Incident, bool]:
    """
    Handles incident creation or deduplication.
    Returns: (incident, is_new_incident)
    """
    rule_id = rule.id if rule else None
    fingerprint = compute_incident_fingerprint(rule_id, service_id, environment, error_signature)

    # Check for an existing ACTIVE incident (OPEN, ACKNOWLEDGED, INVESTIGATING)
    active_incident = db.query(Incident).filter(
        Incident.fingerprint == fingerprint,
        Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED, IncidentStatus.INVESTIGATING])
    ).with_for_update().first()

    if active_incident:
        # Check cooldown if rule specified
        cooldown_seconds = rule.cooldown_seconds if rule else 600
        time_since_last = (event_timestamp - active_incident.last_detected_at).total_seconds()

        # Update last detected time and event count
        active_incident.last_detected_at = max(active_incident.last_detected_at, event_timestamp)
        active_incident.event_count += len(triggering_logs) if triggering_logs else 1

        # Link triggering logs that aren't already linked
        for log in triggering_logs:
            existing_link = db.query(IncidentLog).filter(
                IncidentLog.incident_id == active_incident.id,
                IncidentLog.log_id == log.id
            ).first()
            if not existing_link:
                db.add(IncidentLog(incident_id=active_incident.id, log_id=log.id))

        # Record timeline event if outside debounce (e.g. > 30s)
        if time_since_last > 30:
            db.add(IncidentEvent(
                incident_id=active_incident.id,
                event_type="REPEATED",
                actor_name="Detection Engine",
                details_json={
                    "message": f"Incident condition re-occurred (+{len(triggering_logs)} logs)",
                    "event_count": active_incident.event_count,
                    "last_detected_at": active_incident.last_detected_at.isoformat()
                }
            ))

        db.flush()
        return active_incident, False

    # Otherwise, create a brand-new Incident
    new_incident = Incident(
        title=title,
        description=description,
        severity=severity,
        status=IncidentStatus.OPEN,
        service_id=service_id,
        environment=environment,
        rule_id=rule_id,
        fingerprint=fingerprint,
        error_signature=error_signature,
        first_detected_at=event_timestamp,
        last_detected_at=event_timestamp,
        event_count=len(triggering_logs) if triggering_logs else 1
    )
    db.add(new_incident)
    db.flush()

    # Link triggering logs
    for log in triggering_logs:
        db.add(IncidentLog(incident_id=new_incident.id, log_id=log.id))

    # Add initial timeline event
    db.add(IncidentEvent(
        incident_id=new_incident.id,
        event_type="CREATED",
        actor_name="Detection Engine",
        details_json={
            "rule_name": rule.name if rule else "Manual/Direct Trigger",
            "rule_type": rule.rule_type if rule else "Unknown",
            "severity": severity,
            "trigger_logs_count": len(triggering_logs)
        }
    ))

    # Generate an in-app Alert
    alert = Alert(
        incident_id=new_incident.id,
        title=f"[{severity}] Incident Detected: {title}",
        message=description or f"Triggered by rule '{rule.name if rule else 'N/A'}' on service {service_name} ({environment})",
        severity=severity,
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(alert)
    db.flush()

    return new_incident, True
