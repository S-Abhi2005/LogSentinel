from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class RuleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    rule_type: str = Field(..., pattern="^(error_threshold|critical_log|repeated_failure|error_rate|service_inactivity)$")
    severity: str = Field("HIGH", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    service_id: Optional[str] = None
    environment: Optional[str] = Field(None, pattern="^(development|testing|staging|production)$")
    threshold: float = Field(10.0, ge=0.01)
    time_window_seconds: int = Field(300, ge=10, le=86400)
    cooldown_seconds: int = Field(600, ge=0, le=86400)
    error_signature_pattern: Optional[str] = None
    is_enabled: bool = True

class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    threshold: Optional[float] = None
    time_window_seconds: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    error_signature_pattern: Optional[str] = None
    is_enabled: Optional[bool] = None

class RuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    rule_type: str
    severity: str
    service_id: Optional[str]
    environment: Optional[str]
    threshold: float
    time_window_seconds: int
    cooldown_seconds: int
    error_signature_pattern: Optional[str]
    is_enabled: bool
    created_by_id: Optional[str]
    created_at: datetime
    updated_at: datetime
