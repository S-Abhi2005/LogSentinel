import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.service import Service
from app.models.log import LogEntry
from app.schemas.log import (
    LogIngestRequest, LogBatchIngestRequest, LogBatchIngestResponse,
    LogResponse, LogListResponse
)
from app.security.rbac import validate_ingestion_api_key, require_viewer_or_above
from app.services.log_service import (
    ingest_single_log, ingest_batch_logs, query_logs, export_logs_csv
)
from app.core.errors import NotFoundException

router = APIRouter(prefix="/logs", tags=["Log Ingestion & Explorer"])

@router.post("/ingest", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
def ingest_log_event(
    event: LogIngestRequest,
    authenticated_service: Service = Depends(validate_ingestion_api_key),
    db: Session = Depends(get_db)
):
    correlation_id = f"corr-{uuid.uuid4().hex[:12]}"
    log_entry, _ = ingest_single_log(
        db=db,
        authenticated_service=authenticated_service,
        event=event,
        correlation_id=correlation_id
    )
    return log_entry

@router.post("/ingest/batch", response_model=LogBatchIngestResponse, status_code=status.HTTP_202_ACCEPTED)
def ingest_log_batch(
    batch: LogBatchIngestRequest,
    authenticated_service: Service = Depends(validate_ingestion_api_key),
    db: Session = Depends(get_db)
):
    correlation_id = f"corr-batch-{uuid.uuid4().hex[:12]}"
    response = ingest_batch_logs(
        db=db,
        authenticated_service=authenticated_service,
        batch=batch,
        correlation_id=correlation_id
    )
    return response

@router.get("", response_model=LogListResponse)
def list_logs(
    service_id: Optional[str] = None,
    service_name: Optional[str] = None,
    environment: Optional[str] = None,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    trace_id: Optional[str] = None,
    search: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    items, total = query_logs(
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
        page=page,
        page_size=page_size,
        sort_order=sort_order
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return LogListResponse(
        items=[LogResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/export")
def export_logs(
    service_id: Optional[str] = None,
    service_name: Optional[str] = None,
    environment: Optional[str] = None,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    trace_id: Optional[str] = None,
    search: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(1000, ge=1, le=5000),
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    csv_data = export_logs_csv(
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
        limit=limit
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=logsentinel_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@router.get("/{log_id}", response_model=LogResponse)
def get_log_by_id(
    log_id: str,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    log_entry = db.query(LogEntry).filter(LogEntry.id == log_id).first()
    if not log_entry:
        raise NotFoundException("Log entry", log_id)
    return log_entry

@router.get("/{log_id}/related", response_model=List[LogResponse])
def get_related_logs(
    log_id: str,
    current_user: User = Depends(require_viewer_or_above),
    db: Session = Depends(get_db)
):
    target = db.query(LogEntry).filter(LogEntry.id == log_id).first()
    if not target:
        raise NotFoundException("Log entry", log_id)
    
    # If trace_id exists, find all logs with identical trace_id
    if target.trace_id:
        related = db.query(LogEntry).filter(
            LogEntry.trace_id == target.trace_id
        ).order_by(LogEntry.timestamp.asc()).limit(50).all()
        return related
    
    # Otherwise return logs around this log timestamp for the same service
    from datetime import timedelta
    window_start = target.timestamp - timedelta(minutes=5)
    window_end = target.timestamp + timedelta(minutes=5)
    related = db.query(LogEntry).filter(
        LogEntry.service_id == target.service_id,
        LogEntry.timestamp >= window_start,
        LogEntry.timestamp <= window_end
    ).order_by(LogEntry.timestamp.asc()).limit(50).all()

    return related
