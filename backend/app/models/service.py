import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class ServiceEnvironment:
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ALL = [DEVELOPMENT, TESTING, STAGING, PRODUCTION]

class Service(Base):
    __tablename__ = "services"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), index=True, nullable=False)
    description = Column(Text, nullable=True)
    environment = Column(String(50), default=ServiceEnvironment.DEVELOPMENT, nullable=False)
    owner_team = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_log_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("name", "environment", name="uq_service_name_env"),
    )

    ingestion_keys = relationship("ServiceIngestionKey", back_populates="service", cascade="all, delete-orphan")
    logs = relationship("LogEntry", back_populates="service", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="service")


class ServiceIngestionKey(Base):
    __tablename__ = "service_ingestion_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_id = Column(String(36), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    key_name = Column(String(100), nullable=False)
    key_prefix = Column(String(32), nullable=False)  # e.g. ls_live_a1b2c3d4
    key_hash = Column(String(255), nullable=False)    # SHA-256 hash of raw key
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    service = relationship("Service", back_populates="ingestion_keys")
