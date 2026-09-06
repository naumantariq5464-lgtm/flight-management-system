from sqlalchemy import String, Integer, DateTime, Numeric, ForeignKey, CheckConstraint, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from app.database.base import Base, TimestampMixin
from app.utils.enums import FlightStatus, OverbookingPolicy
import uuid

class Aircraft(Base, TimestampMixin):
    __tablename__ = "aircraft"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., Boeing 777-300ER, Airbus A350
    tail_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    total_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    first_class_capacity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    business_class_capacity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    economy_class_capacity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    flights: Mapped[list["Flight"]] = relationship("Flight", back_populates="aircraft")

class Flight(Base, TimestampMixin):
    __tablename__ = "flights"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flight_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    origin: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # e.g. LHR, DXB, JFK, LHE
    origin_name: Mapped[str] = mapped_column(String(100), nullable=True)
    destination: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    destination_name: Mapped[str] = mapped_column(String(100), nullable=True)
    
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    arrival_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    status: Mapped[FlightStatus] = mapped_column(SQLEnum(FlightStatus), default=FlightStatus.SCHEDULED, nullable=False, index=True)
    
    aircraft_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    first_class_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    business_class_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    economy_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Base prices per class
    base_price_economy: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    base_price_business: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    base_price_first: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    overbooking_policy: Mapped[OverbookingPolicy] = mapped_column(
        SQLEnum(OverbookingPolicy), 
        default=OverbookingPolicy.HARD_NEVER_OVERSELL, 
        nullable=False
    )
    overbooking_buffer_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    aircraft_id: Mapped[str] = mapped_column(String, ForeignKey("aircraft.id"), nullable=True)

    # Database Table Constraints
    __table_args__ = (
        CheckConstraint("arrival_time > departure_time", name="check_arrival_after_departure"),
        CheckConstraint("aircraft_capacity > 0", name="check_positive_capacity"),
        CheckConstraint("first_class_seats >= 0", name="check_first_seats_non_negative"),
        CheckConstraint("business_class_seats >= 0", name="check_business_seats_non_negative"),
        CheckConstraint("economy_seats >= 0", name="check_economy_seats_non_negative"),
        CheckConstraint(
            "first_class_seats + business_class_seats + economy_seats = aircraft_capacity",
            name="check_seats_sum_equals_capacity"
        ),
        UniqueConstraint("flight_number", "departure_time", name="unique_flight_number_departure")
    )

    # Relationships
    aircraft: Mapped["Aircraft"] = relationship("Aircraft", back_populates="flights")
    seat_maps: Mapped[list["SeatMap"]] = relationship("SeatMap", back_populates="flight", cascade="all, delete-orphan")
    seats: Mapped[list["Seat"]] = relationship("Seat", back_populates="flight", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="flight")
    waitlists: Mapped[list["Waitlist"]] = relationship("Waitlist", back_populates="flight")
    fares: Mapped[list["Fare"]] = relationship("Fare", back_populates="flight", cascade="all, delete-orphan")
    schedule_changes: Mapped[list["ScheduleChange"]] = relationship("ScheduleChange", back_populates="flight")
