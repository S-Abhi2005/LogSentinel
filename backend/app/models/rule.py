import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class RuleType:
    ERROR_THRESHOLD = "error_threshold"
    CRITICAL_LOG = "critical_log"
    REPEATED_FAILURE = "repeated_failure"
    ERROR_RATE = "error_rate"
    SERVICE_INACTIVITY = "service_inactivity"
    ALL = [ERROR_THRESHOLD, CRITICAL_LOG, REPEATED_FAILURE, ERROR_RATE, SERVICE_INACTIVITY]

class RuleSeverity:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    ALL = [LOW, MEDIUM, HIGH, CRITICAL]

class IncidentRule(Base):
    __tablename__ = "incident_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default=RuleSeverity.HIGH, nullable=False)
    
    # Optional scopes: NULL means applies globally across all services/environments
    service_id = Column(String(36), ForeignKey("services.id", ondelete="SET NULL"), nullable=True, index=True)
    environment = Column(String(50), nullable=True)
    
    threshold = Column(Float, default=10.0, nullable=False)
    time_window_seconds = Column(Integer, default=300, nullable=False)  # 5 minutes
    cooldown_seconds = Column(Integer, default=600, nullable=False)     # 10 minutes
    error_signature_pattern = Column(String(255), nullable=True)        # substring or regex for repeated failure
    is_enabled = Column(Boolean, default=True, nullable=False, index=True)
    
    created_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    service = relationship("Service")
    created_by = relationship("User")
    incidents = relationship("Incident", back_populates="rule")
