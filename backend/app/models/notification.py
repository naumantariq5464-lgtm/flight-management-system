from sqlalchemy import String, Boolean, DateTime, Numeric, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from app.database.base import Base, TimestampMixin
from app.utils.enums import NotificationType, NotificationStatus, AuditSource
import uuid

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    recipient_phone: Mapped[str] = mapped_column(String(30), nullable=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(2000), nullable=False)
    
    notification_type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType), default=NotificationType.EMAIL, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True)
    source: Mapped[AuditSource] = mapped_column(SQLEnum(AuditSource), default=AuditSource.FASTAPI, nullable=False)
    
    flight_id: Mapped[str] = mapped_column(String, ForeignKey("flights.id", ondelete="SET NULL"), nullable=True)
    booking_id: Mapped[str] = mapped_column(String, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str] = mapped_column(String(500), nullable=True)

class PriceAlert(Base, TimestampMixin):
    __tablename__ = "price_alerts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    origin: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    destination: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    target_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    initial_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_notified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="price_alerts")
