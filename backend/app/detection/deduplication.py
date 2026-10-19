
import hashlib
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.incident import (
    Incident,
    IncidentStatus,
    IncidentLog,
    IncidentEvent,
)
from app.models.alert import Alert
from app.models.log import LogEntry
from app.models.rule import IncidentRule


def compute_incident_fingerprint(
    rule_id: Optional[str],
    service_id: str,
    environment: str,
    error_signature: Optional[str] = None,
) -> str:
    """
    Compute a deterministic SHA-256 fingerprint for incident deduplication.
    """
    raw_str = (
        f"rule={rule_id or 'none'}|service={service_id}"
        f"|env={environment}|sig={error_signature or 'none'}"
    )
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
    event_timestamp: datetime,
) -> tuple[Incident, bool]:
    """
    Create a new incident or update an existing active incident.
    Returns (incident, is_new_incident).
    """
    rule_id = rule.id if rule else None

    fingerprint = compute_incident_fingerprint(
        rule_id, service_id, environment, error_signature
    )

    active_incident = (
        db.query(Incident)
        .filter(
            Incident.fingerprint == fingerprint,
            Incident.status.in_(
                [
                    IncidentStatus.OPEN,
                    IncidentStatus.ACKNOWLEDGED,
                    IncidentStatus.INVESTIGATING,
                ]
            ),
        )
        .with_for_update()
        .first()
    )

    if active_incident:
        cooldown_seconds = rule.cooldown_seconds if rule else 600

        # Find the most recent repeated event.
        last_repeated_event = (
            db.query(IncidentEvent)
            .filter(
                IncidentEvent.incident_id == active_incident.id,
                IncidentEvent.event_type == "REPEATED",
            )
            .order_by(IncidentEvent.created_at.desc())
            .first()
        )

        # Use the actual detection timestamp when available.
        cooldown_reference_time = active_incident.first_detected_at

        if last_repeated_event:
            details = last_repeated_event.details_json or {}
            recorded_timestamp = details.get("detection_timestamp")

            if recorded_timestamp:
                cooldown_reference_time = datetime.fromisoformat(
                    recorded_timestamp
                )
            else:
                # Backward compatibility for older timeline events.
                cooldown_reference_time = last_repeated_event.created_at

        # Normalize timezone awareness before comparing timestamps.
        reference_time = cooldown_reference_time

        if reference_time.tzinfo is None and event_timestamp.tzinfo is not None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)
        elif reference_time.tzinfo is not None and event_timestamp.tzinfo is None:
            event_timestamp = event_timestamp.replace(tzinfo=timezone.utc)

        time_since_last = (
            event_timestamp - reference_time
        ).total_seconds()

        # Update incident detection metadata.
        active_incident.last_detected_at = max(
            active_incident.last_detected_at,
            event_timestamp,
        )

        active_incident.event_count += (
            len(triggering_logs) if triggering_logs else 1
        )

        # Link triggering logs without duplicate associations.
        for log in triggering_logs:
            existing_link = (
                db.query(IncidentLog)
                .filter(
                    IncidentLog.incident_id == active_incident.id,
                    IncidentLog.log_id == log.id,
                )
                .first()
            )

            if not existing_link:
                db.add(
                    IncidentLog(
                        incident_id=active_incident.id,
                        log_id=log.id,
                    )
                )

        # Create a REPEATED event only after the configured cooldown.
        if time_since_last >= cooldown_seconds:
            db.add(
                IncidentEvent(
                    incident_id=active_incident.id,
                    event_type="REPEATED",
                    actor_name="Detection Engine",
                    details_json={
                        "message": (
                            "Incident condition re-occurred "
                            f"(+{len(triggering_logs)} logs)"
                        ),
                        "event_count": active_incident.event_count,
                        "last_detected_at": (
                            active_incident.last_detected_at.isoformat()
                        ),
                        "detection_timestamp": event_timestamp.isoformat(),
                    },
                )
            )

        db.flush()
        return active_incident, False

    # No active incident exists: create a new incident.
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
        event_count=len(triggering_logs) if triggering_logs else 1,
    )

    db.add(new_incident)
    db.flush()

    # Link triggering logs.
    for log in triggering_logs:
        db.add(
            IncidentLog(
                incident_id=new_incident.id,
                log_id=log.id,
            )
        )

    # Record the initial timeline event.
    db.add(
        IncidentEvent(
            incident_id=new_incident.id,
            event_type="CREATED",
            actor_name="Detection Engine",
            details_json={
                "rule_name": rule.name if rule else "Manual/Direct Trigger",
                "rule_type": rule.rule_type if rule else "Unknown",
                "severity": severity,
                "trigger_logs_count": len(triggering_logs),
            },
        )
    )

    # Generate an in-app alert.
    alert = Alert(
        incident_id=new_incident.id,
        title=f"[{severity}] Incident Detected: {title}",
        message=(
            description
            or f"Triggered by rule '{rule.name if rule else 'N/A'}' "
            f"on service {service_name} ({environment})"
        ),
        severity=severity,
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )

    db.add(alert)
    db.flush()

    return new_incident, True
