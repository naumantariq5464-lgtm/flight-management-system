from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.utils.enums import RagApprovalStatus

class PolicyDocumentCreate(BaseModel):
    title: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    content: str = Field(..., min_length=10)
    file_name: Optional[str] = None

class PolicyDocumentOut(BaseModel):
    id: str
    title: str
    category: str
    file_name: Optional[str] = None
    content: str
    vector_id: Optional[str] = None
    is_active: bool
    version: int
    created_at: datetime

    class Config:
        from_attributes = True

class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Customer question regarding flight policies or cancellation")
    booking_id: Optional[str] = Field(None, description="Optional booking ID / PNR to make response booking-aware")
    recipient_email: EmailStr

class RagQueryResponse(BaseModel):
    approval_id: str
    draft_response: str
    is_booking_aware: bool
    policy_category_matched: Optional[str] = None
    status: RagApprovalStatus
    message: str = "Response generated and queued for mandatory human supervisor review."

class RagApprovalAction(BaseModel):
    status: RagApprovalStatus = Field(..., description="APPROVED, REJECTED, or EDITED")
    final_approved_response: Optional[str] = None
    review_notes: Optional[str] = None

class RagApprovalOut(BaseModel):
    id: str
    customer_query: str
    booking_id: Optional[str] = None
    recipient_email: str
    retrieved_context: Optional[str] = None
    draft_response: str
    final_approved_response: Optional[str] = None
    status: RagApprovalStatus
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
