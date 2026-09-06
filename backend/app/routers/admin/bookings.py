from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database.session import get_db
from app.schemas.booking import BookingOut, BookingPassengerOut
from app.schemas.flight import FlightOut
from app.models.user import User
from app.repositories.booking_repo import BookingRepository
from app.services.cancellation_service import CancellationService
from app.auth.dependencies import get_admin_user, get_super_admin_user
from app.utils.enums import BookingStatus
from app.utils.exceptions import NotFoundException

router = APIRouter(prefix="/admin/bookings", tags=["Admin Bookings"])

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

@router.get("", response_model=List[BookingOut])
async def list_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    flight_id: Optional[str] = None,
    status: Optional[BookingStatus] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    repo = BookingRepository(db)
    bookings = await repo.list_bookings(flight_id=flight_id, status=status, skip=skip, limit=limit)
    return [_format_booking_out(b) for b in bookings]

@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking_details(
    booking_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    repo = BookingRepository(db)
    booking = await repo.get_by_id(booking_id)
    if not booking:
        booking = await repo.get_by_pnr(booking_id)
    if not booking:
        raise NotFoundException(f"Booking {booking_id} not found")
    return _format_booking_out(booking)

@router.post("/{booking_id}/cancel")
async def admin_cancel_booking(
    booking_id: str,
    reason: str = "Administrative cancellation",
    current_user: User = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = CancellationService(db)
    return await service.cancel_booking(booking_id, reason, actor_email=current_user.email)
