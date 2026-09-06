from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database.base import Base, TimestampMixin
import uuid

class ScheduleChange(Base, TimestampMixin):
    __tablename__ = "schedule_changes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flight_id: Mapped[str] = mapped_column(String, ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True)
    
    old_departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    new_departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    old_arrival_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    new_arrival_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    old_origin: Mapped[str] = mapped_column(String(10), nullable=True)
    new_origin: Mapped[str] = mapped_column(String(10), nullable=True)
    old_destination: Mapped[str] = mapped_column(String(10), nullable=True)
    new_destination: Mapped[str] = mapped_column(String(10), nullable=True)
    
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    affected_bookings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PROCESSED", nullable=False)
    
    initiated_by_admin_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    flight: Mapped["Flight"] = relationship("Flight", back_populates="schedule_changes")
    initiated_by: Mapped["User"] = relationship("User", foreign_keys=[initiated_by_admin_id])
