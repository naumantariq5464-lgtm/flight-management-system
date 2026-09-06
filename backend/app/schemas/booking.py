from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.utils.enums import BookingStatus, FareType, SeatClass
from app.schemas.flight import FlightOut

class PassengerInput(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[str] = "1990-01-01"
    passport_number: Optional[str] = "A12345678"
    nationality: Optional[str] = "PAK"
    seat_id: Optional[str] = None

class BookingCreateRequest(BaseModel):
    flight_id: str
    fare_type: FareType
    seat_class: SeatClass
    passengers: List[PassengerInput] = Field(..., min_length=1, max_length=9)
    contact_email: EmailStr
    contact_phone: Optional[str] = "+1234567890"
    hold_token: Optional[str] = None
    credit_code: Optional[str] = Field(None, description="Optional Travel Credit code to redeem against booking total")

class BookingPassengerOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    e_ticket_number: str
    is_cancelled: bool
    cancelled_at: Optional[datetime] = None
    seat_number: Optional[str] = None

    class Config:
        from_attributes = True

class BookingOut(BaseModel):
    id: str
    pnr: str
    user_id: Optional[str] = None
    flight_id: str
    flight: Optional[FlightOut] = None
    fare_type: FareType
    seat_class: SeatClass
    status: BookingStatus
    total_amount: Decimal
    currency: str
    contact_email: str
    contact_phone: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    passengers: List[BookingPassengerOut] = []
    created_at: datetime

    class Config:
        from_attributes = True

class PartialCancelRequest(BaseModel):
    passenger_ids: List[str] = Field(..., min_length=1, description="IDs of passengers to cancel from booking")
    reason: str = Field(..., min_length=3)

class RebookRequest(BaseModel):
    new_flight_id: str
    reason: Optional[str] = "Customer requested schedule change or airline disruption rebooking"
