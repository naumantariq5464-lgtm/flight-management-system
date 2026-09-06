from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database.base import Base, TimestampMixin
from app.utils.enums import SeatClass, SeatStatus
import uuid

class SeatMap(Base, TimestampMixin):
    __tablename__ = "seat_maps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flight_id: Mapped[str] = mapped_column(String, ForeignKey("flights.id", ondelete="CASCADE"), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    layout_config: Mapped[str] = mapped_column(String(50), default="3-3", nullable=False)  # e.g., "3-3", "2-4-2", "1-2-1"

    flight: Mapped["Flight"] = relationship("Flight", back_populates="seat_maps")

class Seat(Base, TimestampMixin):
    __tablename__ = "seats"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flight_id: Mapped[str] = mapped_column(String, ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True)
    seat_number: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g., "1A", "14C", "32F"
    row: Mapped[int] = mapped_column(Integer, nullable=False)
    column: Mapped[str] = mapped_column(String(5), nullable=False)
    seat_class: Mapped[SeatClass] = mapped_column(SQLEnum(SeatClass), nullable=False, index=True)
    status: Mapped[SeatStatus] = mapped_column(SQLEnum(SeatStatus), default=SeatStatus.AVAILABLE, nullable=False, index=True)
    
    extra_legroom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_exit_row: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("flight_id", "seat_number", name="unique_flight_seat_number"),
        Index("idx_seat_flight_status_class", "flight_id", "status", "seat_class")
    )

    # Relationships
    flight: Mapped["Flight"] = relationship("Flight", back_populates="seats")
    holds: Mapped[list["SeatHold"]] = relationship("SeatHold", back_populates="seat", cascade="all, delete-orphan")
    booking_seats: Mapped[list["BookingSeat"]] = relationship("BookingSeat", back_populates="seat")

class SeatHold(Base, TimestampMixin):
    __tablename__ = "seat_holds"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    seat_id: Mapped[str] = mapped_column(String, ForeignKey("seats.id", ondelete="CASCADE"), nullable=False, index=True)
    flight_id: Mapped[str] = mapped_column(String, ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    hold_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_released: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    seat: Mapped["Seat"] = relationship("Seat", back_populates="holds")
