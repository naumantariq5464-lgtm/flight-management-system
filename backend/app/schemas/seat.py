from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.utils.enums import SeatClass, SeatStatus

class SeatOut(BaseModel):
    id: str
    flight_id: str
    seat_number: str
    row: int
    column: str
    seat_class: SeatClass
    status: SeatStatus
    extra_legroom: bool
    is_exit_row: bool

    class Config:
        from_attributes = True

class SeatHoldRequest(BaseModel):
    flight_id: str
    seat_ids: List[str] = Field(..., min_length=1, max_length=9, description="List of seat IDs to hold")

class SeatHoldResponse(BaseModel):
    hold_token: str
    flight_id: str
    held_seats: List[SeatOut]
    expires_at: datetime
    message: str = "Seats held temporarily. Complete checkout before expiry."

class SeatMapConfig(BaseModel):
    flight_id: str
    layout_config: str = "3-3"
    extra_legroom_rows: List[int] = []
    exit_rows: List[int] = []
