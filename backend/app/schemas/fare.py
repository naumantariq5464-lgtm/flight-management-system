from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from app.utils.enums import FareType, SeatClass

class FareRuleOut(BaseModel):
    id: str
    fare_type: FareType
    is_refundable: bool
    is_changeable: bool
    cancellation_fee_percent: int
    change_fee_amount: Decimal
    seat_selection_allowed: bool
    baggage_allowance_kg: int
    description: Optional[str] = None

    class Config:
        from_attributes = True

class FareOut(BaseModel):
    id: str
    flight_id: str
    seat_class: SeatClass
    fare_type: FareType
    price: Decimal
    currency: str
    fare_rule: Optional[FareRuleOut] = None

    class Config:
        from_attributes = True
