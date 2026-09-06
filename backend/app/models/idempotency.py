from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database.base import Base, TimestampMixin
import uuid

class IdempotencyKey(Base, TimestampMixin):
    __tablename__ = "idempotency_keys"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    request_path: Mapped[str] = mapped_column(String(255), nullable=False)
    request_payload_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    
    response_code: Mapped[int] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str] = mapped_column(Text, nullable=True)
    
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
