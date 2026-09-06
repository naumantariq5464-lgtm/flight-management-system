from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.utils.enums import FlightStatus, OverbookingPolicy, SeatClass

class FlightCreate(BaseModel):
    flight_number: str = Field(..., min_length=2, max_length=20, examples=["PK-301", "EK-202", "BA-117"])
    origin: str = Field(..., min_length=2, max_length=10, examples=["LHE", "DXB", "LHR", "JFK"])
    origin_name: Optional[str] = "Lahore Allama Iqbal Intl"
    destination: str = Field(..., min_length=2, max_length=10, examples=["DXB", "LHR", "JFK"])
    destination_name: Optional[str] = "Dubai International Airport"
    
    departure_time: datetime
    arrival_time: datetime
    
    aircraft_capacity: int = Field(..., gt=0, description="Total passenger aircraft capacity")
    first_class_seats: int = Field(0, ge=0)
    business_class_seats: int = Field(0, ge=0)
    economy_seats: int = Field(..., ge=0)
    
    base_price_economy: Decimal = Field(..., gt=Decimal("0.00"))
    base_price_business: Decimal = Field(..., ge=Decimal("0.00"))
    base_price_first: Decimal = Field(..., ge=Decimal("0.00"))
    currency: str = Field("USD", max_length=3)
    
    overbooking_policy: OverbookingPolicy = OverbookingPolicy.HARD_NEVER_OVERSELL
    overbooking_buffer_percentage: int = Field(0, ge=0, le=20)
    aircraft_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_flight_invariants(self):
        if self.arrival_time <= self.departure_time:
            raise ValueError("arrival_time must be strictly after departure_time")
        
        calculated_sum = self.first_class_seats + self.business_class_seats + self.economy_seats
        if calculated_sum != self.aircraft_capacity:
            raise ValueError(
                f"Seat breakdown sum ({calculated_sum}) must strictly equal aircraft capacity ({self.aircraft_capacity})"
            )
        
        if self.origin.upper() == self.destination.upper():
            raise ValueError("Origin and Destination cannot be the same airport")
        
        return self

class FlightUpdate(BaseModel):
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    origin: Optional[str] = None
    origin_name: Optional[str] = None
    destination: Optional[str] = None
    destination_name: Optional[str] = None
    base_price_economy: Optional[Decimal] = None
    base_price_business: Optional[Decimal] = None
    base_price_first: Optional[Decimal] = None
    overbooking_policy: Optional[OverbookingPolicy] = None
    overbooking_buffer_percentage: Optional[int] = None
    status: Optional[FlightStatus] = None
    reason: Optional[str] = Field(None, description="Reason for schedule/details modification")

class FlightCancelRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Operational or technical cancellation reason")

class FlightOut(BaseModel):
    id: str
    flight_number: str
    origin: str
    origin_name: Optional[str] = None
    destination: str
    destination_name: Optional[str] = None
    departure_time: datetime
    arrival_time: datetime
    status: FlightStatus
    
    aircraft_capacity: int
    first_class_seats: int
    business_class_seats: int
    economy_seats: int
    
    available_first_seats: Optional[int] = 0
    available_business_seats: Optional[int] = 0
    available_economy_seats: Optional[int] = 0
    
    base_price_economy: Decimal
    base_price_business: Decimal
    base_price_first: Decimal
    currency: str
    overbooking_policy: OverbookingPolicy
    created_at: datetime

    class Config:
        from_attributes = True

class FlightSearchQuery(BaseModel):
    origin: str
    destination: str
    departure_date: str  # YYYY-MM-DD
    passengers: int = Field(1, ge=1, le=10)
    seat_class: Optional[SeatClass] = None
