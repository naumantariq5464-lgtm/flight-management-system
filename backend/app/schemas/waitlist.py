from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.utils.enums import WaitlistStatus, SeatClass, FareType
from app.schemas.flight import FlightOut

class WaitlistJoinRequest(BaseModel):
    flight_id: str
    passenger_first_name: str = Field(..., min_length=1)
    passenger_last_name: str = Field(..., min_length=1)
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    seat_class: SeatClass
    fare_type: FareType = FareType.FLEXIBLE

class WaitlistClaimRequest(BaseModel):
    claim_token: str

class WaitlistOut(BaseModel):
    id: str
    flight_id: str
    flight: Optional[FlightOut] = None
    passenger_first_name: str
    passenger_last_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    seat_class: SeatClass
    fare_type: FareType
    loyalty_tier: str
    priority_score: int
    status: WaitlistStatus
    promoted_at: Optional[datetime] = None
    claim_expires_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None
    claim_token: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
