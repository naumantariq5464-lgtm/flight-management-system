from sqlalchemy import String, Integer, Boolean, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from app.database.base import Base, TimestampMixin
from app.utils.enums import FareType, SeatClass
import uuid

class FareRule(Base, TimestampMixin):
    __tablename__ = "fare_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    fare_type: Mapped[FareType] = mapped_column(SQLEnum(FareType), unique=True, nullable=False, index=True)
    is_refundable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_changeable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancellation_fee_percent: Mapped[int] = mapped_column(Integer, default=100, nullable=False)  # 100% means non-refundable
    change_fee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    seat_selection_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    baggage_allowance_kg: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)

    fares: Mapped[list["Fare"]] = relationship("Fare", back_populates="fare_rule")

class Fare(Base, TimestampMixin):
    __tablename__ = "fares"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flight_id: Mapped[str] = mapped_column(String, ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True)
    seat_class: Mapped[SeatClass] = mapped_column(SQLEnum(SeatClass), nullable=False)
    fare_type: Mapped[FareType] = mapped_column(SQLEnum(FareType), nullable=False)
    fare_rule_id: Mapped[str] = mapped_column(String, ForeignKey("fare_rules.id"), nullable=False)
    
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    flight: Mapped["Flight"] = relationship("Flight", back_populates="fares")
    fare_rule: Mapped["FareRule"] = relationship("FareRule", back_populates="fares")
