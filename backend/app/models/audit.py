from sqlalchemy import String, Text, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin
from app.utils.enums import AuditSource
import uuid

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    actor_role: Mapped[str] = mapped_column(String(50), nullable=True)
    
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., FLIGHT_CANCELLED, BOOKING_REFUNDED
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # Flight, Booking, Seat, Waitlist, Refund
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    old_values: Mapped[str] = mapped_column(Text, nullable=True)  # JSON representation of before state
    new_values: Mapped[str] = mapped_column(Text, nullable=True)  # JSON representation of after state
    
    source: Mapped[AuditSource] = mapped_column(SQLEnum(AuditSource), default=AuditSource.FASTAPI, nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    request_id: Mapped[str] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_action_time", "action", "created_at"),
    )
