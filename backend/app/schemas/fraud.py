from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.utils.enums import RiskLevel, FraudStatus

class FraudScoreOut(BaseModel):
    id: str
    booking_id: str
    user_id: Optional[str] = None
    score: int
    risk_level: RiskLevel
    reasons: str
    status: FraudStatus
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FraudReviewRequest(BaseModel):
    status: FraudStatus = Field(..., description="APPROVED, FLAGGED, or BLOCKED")
    review_notes: Optional[str] = None
