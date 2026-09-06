from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database.session import get_db
from app.schemas.booking import (
    BookingCreateRequest, 
    BookingOut, 
    BookingPassengerOut, 
    PartialCancelRequest
)
from app.schemas.seat import SeatHoldRequest, SeatHoldResponse
from app.schemas.flight import FlightOut
from app.models.user import User
from app.services.booking_service import BookingService
from app.services.seat_service import SeatService
from app.services.cancellation_service import CancellationService
from app.repositories.booking_repo import BookingRepository
from app.repositories.idempotency_repo import IdempotencyRepository
from app.auth.dependencies import get_current_user, get_optional_current_user
from app.utils.exceptions import NotFoundException
import json

router = APIRouter(prefix="/bookings", tags=["Customer Bookings"])

def _format_booking_out(b) -> BookingOut:
    b_out = BookingOut(
        id=b.id,
        pnr=b.pnr,
        user_id=b.user_id,
        flight_id=b.flight_id,
        fare_type=b.fare_type,
        seat_class=b.seat_class,
        status=b.status,
        total_amount=b.total_amount,
        currency=b.currency,
        contact_email=b.contact_email,
        contact_phone=b.contact_phone,
        confirmed_at=b.confirmed_at,
        cancelled_at=b.cancelled_at,
        created_at=b.created_at,
        flight=FlightOut.model_validate(b.flight) if b.flight else None,
        passengers=[]
    )
    for p in b.passengers:
        seat_num = None
        for bs in b.seats:
            if bs.passenger_id == p.id and bs.seat:
                seat_num = bs.seat.seat_number
        p_out = BookingPassengerOut(
            id=p.id,
            first_name=p.first_name,
            last_name=p.last_name,
            date_of_birth=p.date_of_birth,
            passport_number=p.passport_number,
            nationality=p.nationality,
            e_ticket_number=p.e_ticket_number,
            is_cancelled=p.is_cancelled,
            cancelled_at=p.cancelled_at,
            seat_number=seat_num
        )
        b_out.passengers.append(p_out)
    return b_out

@router.post("/hold", response_model=SeatHoldResponse, status_code=status.HTTP_201_CREATED)
async def hold_seats(
    request: SeatHoldRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = SeatService(db)
    return await service.hold_seats(
        request=request, 
        user_id=current_user.id if current_user else None,
        actor_email=current_user.email if current_user else None
    )

@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: BookingCreateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    idempotency_repo = IdempotencyRepository(db)
    booking_service = BookingService(db)

    # 1. Check Idempotency Key
    if idempotency_key:
        cached = await idempotency_repo.get_by_key(idempotency_key)
        if cached and cached.response_body:
            cached_data = json.loads(cached.response_body)
            return BookingOut(**cached_data)

    # 2. Execute Booking
    booking = await booking_service.create_booking(
        request=request,
        user_id=current_user.id if current_user else None,
        actor_email=current_user.email if current_user else request.contact_email
    )

    formatted = _format_booking_out(booking)

    # 3. Store Idempotency Result
    if idempotency_key:
        await idempotency_repo.lock_key(key=idempotency_key, request_path="/bookings")
        key_record = await idempotency_repo.get_by_key(idempotency_key)
        if key_record:
            await idempotency_repo.complete_key(
                record=key_record,
                status_code=201,
                response_body=formatted.model_dump_json()
            )

    return formatted

@router.get("/my-bookings", response_model=List[BookingOut])
async def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = BookingRepository(db)
    bookings = await repo.list_bookings(user_id=current_user.id)
    return [_format_booking_out(b) for b in bookings]

@router.get("/{pnr_or_id}", response_model=BookingOut)
async def get_booking_by_pnr(
    pnr_or_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = BookingRepository(db)
    booking = await repo.get_by_pnr(pnr_or_id)
    if not booking:
        booking = await repo.get_by_id(pnr_or_id)
    if not booking:
        raise NotFoundException(f"Booking {pnr_or_id} not found")
    return _format_booking_out(booking)

@router.post("/{booking_id}/cancel")
async def cancel_customer_booking(
    booking_id: str,
    reason: str = "Customer self-service cancellation",
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CancellationService(db)
    return await service.cancel_booking(
        booking_id=booking_id,
        reason=reason,
        actor_email=current_user.email if current_user else "customer"
    )

@router.post("/{booking_id}/partial-cancel")
async def partial_cancel_customer_booking(
    booking_id: str,
    request: PartialCancelRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CancellationService(db)
    return await service.partial_cancel(
        booking_id=booking_id,
        passenger_ids=request.passenger_ids,
        reason=request.reason,
        actor_email=current_user.email if current_user else "customer"
    )
