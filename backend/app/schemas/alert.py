from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class AlertResponse(BaseModel):
    id: str
    incident_id: Optional[str]
    title: str
    message: str
    severity: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AlertListResponse(BaseModel):
    items: List[AlertResponse]
    unread_count: int
    total: int
