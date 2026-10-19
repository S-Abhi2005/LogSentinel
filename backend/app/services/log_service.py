import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_

from app.models.log import LogEntry, LogSeverity
from app.models.service import Service
from app.schemas.log import LogIngestRequest, LogBatchIngestRequest, LogBatchIngestResponse
from app.core.config import settings
from app.core.errors import BadRequestException, NotFoundException
from app.detection.engine import detection_engine

def validate_log_payload(event: LogIngestRequest):
    """Enforces payload byte limits and validation."""
    if len(event.message.encode("utf-8")) > settings.MAX_LOG_MESSAGE_BYTES:
        raise BadRequestException(f"Log message exceeds maximum allowed size of {settings.MAX_LOG_MESSAGE_BYTES} bytes")
    
    if event.metadata:
        metadata_bytes = len(json.dumps(event.metadata).encode("utf-8"))
        if metadata_bytes > settings.MAX_METADATA_BYTES:
            raise BadRequestException(f"Log metadata exceeds maximum allowed size of {settings.MAX_METADATA_BYTES} bytes")

def ingest_single_log(
    db: Session,
    authenticated_service: Service,
    event: LogIngestRequest,
    correlation_id: str
) -> Tuple[LogEntry, List[str]]:
    """Ingests a single log, saves to DB, evaluates detection rules, and returns triggered incidents."""
    validate_log_payload(event)
    
    # Ensure service name matches authenticated service
    if event.service_name != authenticated_service.name:
        raise BadRequestException(
            f"Ingestion key authorized for service '{authenticated_service.name}', but event specifies '{event.service_name}'"
        )

    ts = event.timestamp or datetime.now(timezone.utc)

    log_entry = LogEntry(
        service_id=authenticated_service.id,
        service_name=authenticated_service.name,
        environment=event.environment,
        severity=event.severity,
        message=event.message,
        timestamp=ts,
        source=event.source,
        trace_id=event.trace_id,
        metadata_json=event.metadata
    )
    db.add(log_entry)
    
    # Update service last_log_at
    authenticated_service.last_log_at = max(authenticated_service.last_log_at or ts, ts)
    db.flush()

    # Trigger detection engine
    triggered_incidents = detection_engine.evaluate_ingested_logs(
        db=db,
        service=authenticated_service,
        logs=[log_entry]
    )

    db.commit()
    db.refresh(log_entry)

    triggered_ids = [inc.id for inc in triggered_incidents]
    return log_entry, triggered_ids

def ingest_batch_logs(
    db: Session,
    authenticated_service: Service,
    batch: LogBatchIngestRequest,
    correlation_id: str
) -> LogBatchIngestResponse:
    """Ingests a batch of logs with partial failure tolerance."""
    if len(batch.events) > settings.MAX_BATCH_SIZE:
        raise BadRequestException(f"Batch size {len(batch.events)} exceeds limit of {settings.MAX_BATCH_SIZE}")

    accepted_logs: List[LogEntry] = []
    errors: List[str] = []

    latest_ts = authenticated_service.last_log_at

    for idx, event in enumerate(batch.events):
        try:
            validate_log_payload(event)
            if event.service_name != authenticated_service.name:
                errors.append(f"Event #{idx}: service_name '{event.service_name}' does not match key service '{authenticated_service.name}'")
                continue

            ts = event.timestamp or datetime.now(timezone.utc)
            if not latest_ts or ts > latest_ts:
                latest_ts = ts

            log_entry = LogEntry(
                service_id=authenticated_service.id,
                service_name=authenticated_service.name,
                environment=event.environment,
                severity=event.severity,
                message=event.message,
                timestamp=ts,
                source=event.source,
                trace_id=event.trace_id,
                metadata_json=event.metadata
            )
            db.add(log_entry)
            accepted_logs.append(log_entry)
        except Exception as e:
            errors.append(f"Event #{idx}: {str(e)}")

    if accepted_logs:
        authenticated_service.last_log_at = latest_ts
        db.flush()

        # Run detection engine on accepted logs
        triggered_incidents = detection_engine.evaluate_ingested_logs(
            db=db,
            service=authenticated_service,
            logs=accepted_logs
        )
        db.commit()
        triggered_ids = [inc.id for inc in triggered_incidents]
    else:
        db.rollback()
        triggered_ids = []

    return LogBatchIngestResponse(
        accepted=len(accepted_logs),
        failed=len(errors),
        errors=errors,
        correlation_id=correlation_id,
        incident_triggered=len(triggered_ids) > 0,
        triggered_incident_ids=triggered_ids
    )

def query_logs(
    db: Session,
    service_id: Optional[str] = None,
    service_name: Optional[str] = None,
    environment: Optional[str] = None,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    trace_id: Optional[str] = None,
    search: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
    sort_order: str = "desc"
) -> Tuple[List[LogEntry], int]:
    """Indexed search and pagination for Logs Explorer."""
    query = db.query(LogEntry)

    if service_id:
        query = query.filter(LogEntry.service_id == service_id)
    if service_name:
        query = query.filter(LogEntry.service_name == service_name)
    if environment:
        query = query.filter(LogEntry.environment == environment)
    if severity:
        query = query.filter(LogEntry.severity == severity)
    if source:
        query = query.filter(LogEntry.source == source)
    if trace_id:
        query = query.filter(LogEntry.trace_id == trace_id)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                LogEntry.message.ilike(search_pattern),
                LogEntry.service_name.ilike(search_pattern),
                LogEntry.trace_id.ilike(search_pattern),
                LogEntry.source.ilike(search_pattern)
            )
        )
    if start_time:
        query = query.filter(LogEntry.timestamp >= start_time)
    if end_time:
        query = query.filter(LogEntry.timestamp <= end_time)

    total = query.count()

    if sort_order == "asc":
        query = query.order_by(asc(LogEntry.timestamp))
    else:
        query = query.order_by(desc(LogEntry.timestamp))

    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return items, total

def export_logs_csv(
    db: Session,
    service_id: Optional[str] = None,
    service_name: Optional[str] = None,
    environment: Optional[str] = None,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    trace_id: Optional[str] = None,
    search: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 2000
) -> str:
    """Exports filtered logs into CSV formatted string."""
    items, _ = query_logs(
        db=db,
        service_id=service_id,
        service_name=service_name,
        environment=environment,
        severity=severity,
        source=source,
        trace_id=trace_id,
        search=search,
        start_time=start_time,
        end_time=end_time,
        page=1,
        page_size=limit,
        sort_order="desc"
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp (UTC)", "Service", "Environment", "Severity", "Message", "Source", "Trace ID"])

    for log in items:
        writer.writerow([
            log.id,
            log.timestamp.isoformat(),
            log.service_name,
            log.environment,
            log.severity,
            log.message.replace("\n", " "),
            log.source or "",
            log.trace_id or ""
        ])

    return output.getvalue()
