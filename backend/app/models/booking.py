from sqlalchemy import String, Boolean, DateTime, Numeric, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from app.database.base import Base, TimestampMixin
from app.utils.enums import BookingStatus, FareType, SeatClass
import uuid

class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pnr: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    flight_id: Mapped[str] = mapped_column(String, ForeignKey("flights.id"), nullable=False, index=True)
    
    fare_type: Mapped[FareType] = mapped_column(SQLEnum(FareType), nullable=False)
    seat_class: Mapped[SeatClass] = mapped_column(SQLEnum(SeatClass), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(SQLEnum(BookingStatus), default=BookingStatus.CONFIRMED, nullable=False, index=True)
    
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_phone: Mapped[str] = mapped_column(String(30), nullable=True)
    
    payment_reference: Mapped[str] = mapped_column(String(100), nullable=True)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bookings")
    flight: Mapped["Flight"] = relationship("Flight", back_populates="bookings")
    passengers: Mapped[list["BookingPassenger"]] = relationship("BookingPassenger", back_populates="booking", cascade="all, delete-orphan")
    seats: Mapped[list["BookingSeat"]] = relationship("BookingSeat", back_populates="booking", cascade="all, delete-orphan")
    refunds: Mapped[list["Refund"]] = relationship("Refund", back_populates="booking")

class BookingPassenger(Base, TimestampMixin):
    __tablename__ = "booking_passengers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id: Mapped[str] = mapped_column(String, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(20), nullable=True)
    passport_number: Mapped[str] = mapped_column(String(50), nullable=True)
    nationality: Mapped[str] = mapped_column(String(50), nullable=True)
    e_ticket_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    
    # Partial cancellation support
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="passengers")
    booking_seat: Mapped["BookingSeat"] = relationship("BookingSeat", back_populates="passenger", uselist=False)

class BookingSeat(Base, TimestampMixin):
    __tablename__ = "booking_seats"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id: Mapped[str] = mapped_column(String, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    passenger_id: Mapped[str] = mapped_column(String, ForeignKey("booking_passengers.id", ondelete="CASCADE"), nullable=False, index=True)
    seat_id: Mapped[str] = mapped_column(String, ForeignKey("seats.id"), nullable=False, index=True)
    seat_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="seats")
    passenger: Mapped["BookingPassenger"] = relationship("BookingPassenger", back_populates="booking_seat")
    seat: Mapped["Seat"] = relationship("Seat", back_populates="booking_seats")
