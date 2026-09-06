from sqlalchemy import String, Boolean, DateTime, Numeric, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from app.database.base import Base, TimestampMixin
from app.utils.enums import RefundStatus, RefundType, CreditStatus
import uuid

class Refund(Base, TimestampMixin):
    __tablename__ = "refunds"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id: Mapped[str] = mapped_column(String, ForeignKey("bookings.id"), nullable=False, index=True)
    passenger_id: Mapped[str] = mapped_column(String, ForeignKey("booking_passengers.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    refund_type: Mapped[RefundType] = mapped_column(SQLEnum(RefundType), default=RefundType.FULL, nullable=False)
    status: Mapped[RefundStatus] = mapped_column(SQLEnum(RefundStatus), default=RefundStatus.PENDING, nullable=False, index=True)
    
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    escalation_reason: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="refunds")
    passenger: Mapped["BookingPassenger"] = relationship("BookingPassenger", foreign_keys=[passenger_id])
    approved_by: Mapped["User"] = relationship("User", foreign_keys=[approved_by_user_id])

class TravelCredit(Base, TimestampMixin):
    __tablename__ = "travel_credits"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    credit_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    passenger_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    original_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    balance_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[CreditStatus] = mapped_column(SQLEnum(CreditStatus), default=CreditStatus.ACTIVE, nullable=False, index=True)
    source_booking_id: Mapped[str] = mapped_column(String, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="travel_credits")
