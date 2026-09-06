from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database.base import Base, TimestampMixin
from app.utils.enums import RagApprovalStatus
import uuid

class PolicyDocument(Base, TimestampMixin):
    __tablename__ = "policy_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # CANCELLATION, BAGGAGE, REFUND, SCHEDULE_CHANGE, SEATING
    file_name: Mapped[str] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    vector_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)  # Pinecone index ID
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

class RagApproval(Base, TimestampMixin):
    __tablename__ = "rag_approvals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_query: Mapped[str] = mapped_column(Text, nullable=False)
    booking_id: Mapped[str] = mapped_column(String, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    retrieved_context: Mapped[str] = mapped_column(Text, nullable=True)
    draft_response: Mapped[str] = mapped_column(Text, nullable=False)
    final_approved_response: Mapped[str] = mapped_column(Text, nullable=True)
    
    status: Mapped[RagApprovalStatus] = mapped_column(SQLEnum(RagApprovalStatus), default=RagApprovalStatus.PENDING, nullable=False, index=True)
    
    reviewed_by_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str] = mapped_column(String(500), nullable=True)

    booking: Mapped["Booking"] = relationship("Booking")
    reviewed_by: Mapped["User"] = relationship("User", foreign_keys=[reviewed_by_user_id])
