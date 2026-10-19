from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: Optional[str]
    title: str
    message: str
    severity: str
    is_read: bool
    created_at: datetime

class AlertListResponse(BaseModel):
    items: List[AlertResponse]
    unread_count: int
    total: int
