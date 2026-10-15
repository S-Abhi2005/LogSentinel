from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class IncidentCommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=5000)

class IncidentCommentResponse(BaseModel):
    id: str
    incident_id: str
    user_id: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True

class IncidentEventResponse(BaseModel):
    id: str
    incident_id: str
    event_type: str
    actor_id: Optional[str] = None
    actor_name: str
    details_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class IncidentAssignRequest(BaseModel):
    assigned_user_id: Optional[str] = None  # None unassigns

class IncidentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    severity: str
    status: str
    service_id: str
    service_name: Optional[str] = None
    environment: str
    rule_id: Optional[str]
    rule_name: Optional[str] = None
    fingerprint: str
    error_signature: Optional[str]
    first_detected_at: datetime
    last_detected_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    assigned_user_id: Optional[str]
    assigned_user_name: Optional[str] = None
    event_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class IncidentDetailResponse(IncidentResponse):
    comments: List[IncidentCommentResponse] = []
    timeline: List[IncidentEventResponse] = []
    related_logs: List[Dict[str, Any]] = []

class IncidentListResponse(BaseModel):
    items: List[IncidentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
