from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.utils.enums import NotificationType, NotificationStatus, AuditSource

class NotificationOut(BaseModel):
    id: str
    recipient_email: str
    recipient_phone: Optional[str] = None
    title: str
    message: str
    notification_type: NotificationType
    status: NotificationStatus
    source: AuditSource
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PriceAlertCreate(BaseModel):
    origin: str
    destination: str
    target_price: Decimal

class PriceAlertOut(BaseModel):
    id: str
    email: str
    origin: str
    destination: str
    target_price: Decimal
    initial_price: Decimal
    current_price: Decimal
    is_active: bool
    last_notified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
