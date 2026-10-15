from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    environment: str = Field("development", pattern="^(development|testing|staging|production)$")
    owner_team: str = Field(..., min_length=2, max_length=100)

class ServiceUpdate(BaseModel):
    description: Optional[str] = None
    owner_team: Optional[str] = None
    is_enabled: Optional[bool] = None

class IngestionKeyCreate(BaseModel):
    key_name: str = Field(..., min_length=2, max_length=100)

class IngestionKeyCreatedResponse(BaseModel):
    id: str
    service_id: str
    key_name: str
    key_prefix: str
    raw_key: str  # ONLY RETURNED ONCE UPON CREATION
    created_at: datetime

class IngestionKeyResponse(BaseModel):
    id: str
    service_id: str
    key_name: str
    key_prefix: str
    is_revoked: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ServiceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    environment: str
    owner_team: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_log_at: Optional[datetime]

    class Config:
        from_attributes = True

class ServiceWithStatsResponse(ServiceResponse):
    health_status: str  # HEALTHY, DEGRADED, CRITICAL, UNKNOWN
    active_incidents_count: int = 0
    recent_error_count: int = 0
    total_logs_count: int = 0
