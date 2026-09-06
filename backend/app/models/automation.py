from sqlalchemy import String, Integer, DateTime, Text, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database.base import Base, TimestampMixin
from app.utils.enums import AuditSource
import uuid

class AutomationJob(Base, TimestampMixin):
    __tablename__ = "automation_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="RUNNING", nullable=False, index=True)  # RUNNING, SUCCESS, FAILED
    items_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    execution_source: Mapped[AuditSource] = mapped_column(SQLEnum(AuditSource), default=AuditSource.N8N, nullable=False)

class ReconciliationLog(Base, TimestampMixin):
    __tablename__ = "reconciliation_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    check_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # ORPHAN_SEATS, EXPIRED_HOLDS, CANCELLED_FLIGHT_INCONSISTENCY
    anomalies_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)  # JSON summary of discrepancies
    status: Mapped[str] = mapped_column(String(50), default="DETECTED", nullable=False, index=True)  # DETECTED, AUTO_RESOLVED, FLAGGED_FOR_ADMIN
