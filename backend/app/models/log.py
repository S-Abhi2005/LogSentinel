import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class LogSeverity:
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    ALL = [DEBUG, INFO, WARNING, ERROR, CRITICAL]

class LogEntry(Base):
    __tablename__ = "logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_id = Column(String(36), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    environment = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(100), nullable=True)
    trace_id = Column(String(100), nullable=True, index=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_logs_service_env_timestamp", "service_name", "environment", "timestamp"),
        Index("ix_logs_severity_timestamp", "severity", "timestamp"),
    )

    service = relationship("Service", back_populates="logs")
    incident_associations = relationship("IncidentLog", back_populates="log", cascade="all, delete-orphan")
