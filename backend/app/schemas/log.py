from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field, field_validator

class LogIngestRequest(BaseModel):
    service_name: str = Field(..., min_length=1, max_length=100)
    environment: str = Field("development", pattern="^(development|testing|staging|production)$")
    severity: str = Field(..., pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    message: str = Field(..., min_length=1, max_length=32768)
    timestamp: Optional[datetime] = None
    source: Optional[str] = Field(None, max_length=100)
    trace_id: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def normalize_utc_timestamp(cls, v: Any) -> datetime:
        if v is None:
            return datetime.now(timezone.utc)
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        if isinstance(v, datetime):
            return v.astimezone(timezone.utc) if v.tzinfo else v.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc)

class LogBatchIngestRequest(BaseModel):
    events: List[LogIngestRequest] = Field(..., min_length=1, max_length=500)

class LogBatchIngestResponse(BaseModel):
    accepted: int
    failed: int
    errors: List[str] = []
    correlation_id: str
    incident_triggered: bool = False
    triggered_incident_ids: List[str] = []

class LogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    service_id: str
    service_name: str
    environment: str
    severity: str
    message: str
    timestamp: datetime
    source: Optional[str]
    trace_id: Optional[str]
    metadata_json: Optional[Dict[str, Any]]
    created_at: datetime

class LogListResponse(BaseModel):
    items: List[LogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
