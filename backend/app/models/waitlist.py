from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database.base import Base, TimestampMixin
from app.utils.enums import WaitlistStatus, SeatClass, FareType
import uuid

class Waitlist(Base, TimestampMixin):
    __tablename__ = "waitlists"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flight_id: Mapped[str] = mapped_column(String, ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    passenger_first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    passenger_last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_phone: Mapped[str] = mapped_column(String(30), nullable=True)
    
    seat_class: Mapped[SeatClass] = mapped_column(SQLEnum(SeatClass), nullable=False, index=True)
    fare_type: Mapped[FareType] = mapped_column(SQLEnum(FareType), default=FareType.FLEXIBLE, nullable=False)
    loyalty_tier: Mapped[str] = mapped_column(String(50), default="STANDARD", nullable=False)
    
    # Priority score: Higher number = higher priority
    # Standard formula: Tier Points (Platinum=3000, Gold=2000, Silver=1000, Standard=0) + Fare (Flex=500) + Joined Timestamp rank
    priority_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    
    status: Mapped[WaitlistStatus] = mapped_column(SQLEnum(WaitlistStatus), default=WaitlistStatus.WAITING, nullable=False, index=True)
    
    promoted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    claim_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    promoted_seat_id: Mapped[str] = mapped_column(String, ForeignKey("seats.id", ondelete="SET NULL"), nullable=True)
    claim_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=True, index=True)

    __table_args__ = (
        Index("idx_waitlist_flight_status_prio", "flight_id", "status", "priority_score"),
    )

    flight: Mapped["Flight"] = relationship("Flight", back_populates="waitlists")
    promoted_seat: Mapped["Seat"] = relationship("Seat", foreign_keys=[promoted_seat_id])
