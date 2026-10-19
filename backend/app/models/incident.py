import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class IncidentStatus:
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    ALL = [OPEN, ACKNOWLEDGED, INVESTIGATING, RESOLVED]

    # Valid state transitions
    TRANSITIONS = {
        OPEN: [ACKNOWLEDGED, INVESTIGATING, RESOLVED],
        ACKNOWLEDGED: [INVESTIGATING, RESOLVED],
        INVESTIGATING: [RESOLVED],
        RESOLVED: [OPEN],  # Reopen allowed
    }

class IncidentSeverity:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    ALL = [LOW, MEDIUM, HIGH, CRITICAL]

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default=IncidentSeverity.HIGH, nullable=False, index=True)
    status = Column(String(20), default=IncidentStatus.OPEN, nullable=False, index=True)
    
    service_id = Column(String(36), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    environment = Column(String(50), nullable=False, index=True)
    rule_id = Column(String(36), ForeignKey("incident_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    
    fingerprint = Column(String(255), nullable=False, index=True)
    error_signature = Column(String(255), nullable=True)
    
    first_detected_at = Column(DateTime(timezone=True), nullable=False)
    last_detected_at = Column(DateTime(timezone=True), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    assigned_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_count = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    service = relationship("Service", back_populates="incidents")
    rule = relationship("IncidentRule", back_populates="incidents")
    assigned_user = relationship("User", back_populates="assigned_incidents", foreign_keys=[assigned_user_id])
    
    incident_logs = relationship("IncidentLog", back_populates="incident", cascade="all, delete-orphan")
    comments = relationship("IncidentComment", back_populates="incident", cascade="all, delete-orphan", order_by="IncidentComment.created_at.asc()")
    timeline_events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan", order_by="IncidentEvent.created_at.asc()")
    alerts = relationship("Alert", back_populates="incident", cascade="all, delete-orphan")

    @property
    def assigned_user_name(self) -> Optional[str]:
        return self.assigned_user.full_name if self.assigned_user else None

    @property
    def service_name(self) -> Optional[str]:
        return self.service.name if self.service else None

    @property
    def rule_name(self) -> Optional[str]:
        return self.rule.name if self.rule else None


class IncidentLog(Base):
    __tablename__ = "incident_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    log_id = Column(String(36), ForeignKey("logs.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("Incident", back_populates="incident_logs")
    log = relationship("LogEntry", back_populates="incident_associations")


class IncidentComment(Base):
    __tablename__ = "incident_comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("Incident", back_populates="comments")
    user = relationship("User", back_populates="comments")


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # CREATED, ACKNOWLEDGED, INVESTIGATING, RESOLVED, REOPENED, ASSIGNED, COMMENTED, REPEATED
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_name = Column(String(100), default="System", nullable=False)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("Incident", back_populates="timeline_events")
    actor = relationship("User")
