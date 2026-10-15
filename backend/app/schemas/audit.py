from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class AuditLogResponse(BaseModel):
    id: str
    actor_email: str
    actor_role: str
    action: str
    target_type: str
    target_id: Optional[str]
    correlation_id: Optional[str]
    details_json: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
