from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database.base import Base, TimestampMixin
from app.utils.enums import RiskLevel, FraudStatus
import uuid

class FraudScore(Base, TimestampMixin):
    __tablename__ = "fraud_scores"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id: Mapped[str] = mapped_column(String, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 0 to 100
    risk_level: Mapped[RiskLevel] = mapped_column(SQLEnum(RiskLevel), default=RiskLevel.LOW, nullable=False, index=True)
    reasons: Mapped[str] = mapped_column(Text, nullable=False)  # JSON or semicolon separated string of heuristic triggers
    
    status: Mapped[FraudStatus] = mapped_column(SQLEnum(FraudStatus), default=FraudStatus.PENDING_REVIEW, nullable=False, index=True)
    reviewed_by_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str] = mapped_column(String(500), nullable=True)

    booking: Mapped["Booking"] = relationship("Booking")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    reviewed_by: Mapped["User"] = relationship("User", foreign_keys=[reviewed_by_user_id])
