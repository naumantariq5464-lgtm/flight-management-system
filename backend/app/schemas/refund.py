from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.utils.enums import RefundStatus, RefundType, CreditStatus

class RefundCreateRequest(BaseModel):
    booking_id: str
    passenger_id: Optional[str] = None
    reason: str = Field(..., min_length=3)
    refund_type: RefundType = RefundType.FULL

class RefundApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None

class RefundOut(BaseModel):
    id: str
    booking_id: str
    passenger_id: Optional[str] = None
    user_id: Optional[str] = None
    amount: Decimal
    currency: str
    reason: str
    refund_type: RefundType
    status: RefundStatus
    requires_human_approval: bool
    processed_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None
    escalation_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TravelCreditOut(BaseModel):
    id: str
    credit_code: str
    passenger_name: str
    original_amount: Decimal
    balance_amount: Decimal
    currency: str
    expires_at: datetime
    status: CreditStatus
    source_booking_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
