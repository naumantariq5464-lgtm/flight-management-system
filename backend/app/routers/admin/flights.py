from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database.session import get_db
from app.schemas.flight import FlightCreate, FlightUpdate, FlightCancelRequest, FlightOut
from app.schemas.seat import SeatOut
from app.models.user import User
from app.services.flight_service import FlightService
from app.services.seat_service import SeatService
from app.repositories.flight_repo import FlightRepository
from app.auth.dependencies import get_admin_user, get_super_admin_user
from app.utils.enums import FlightStatus, SeatClass
from app.utils.exceptions import NotFoundException

router = APIRouter(prefix="/admin/flights", tags=["Admin Flights"])

@router.post("", response_model=FlightOut, status_code=status.HTTP_201_CREATED)
async def create_flight(
    data: FlightCreate,
    current_user: User = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = FlightService(db)
    flight = await service.create_flight(data, actor_email=current_user.email)
    
    # Enrich with live seat counts
    counts = await service.flight_repo.get_available_seat_counts(flight.id)
    flight_out = FlightOut.model_validate(flight)
    flight_out.available_first_seats = counts.get(SeatClass.FIRST, 0)
    flight_out.available_business_seats = counts.get(SeatClass.BUSINESS, 0)
    flight_out.available_economy_seats = counts.get(SeatClass.ECONOMY, 0)
    return flight_out

@router.get("", response_model=List[FlightOut])
async def list_admin_flights(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status: Optional[FlightStatus] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    repo = FlightRepository(db)
    flights = await repo.list_all(skip=skip, limit=limit, status=status, origin=origin, destination=destination)
    
    output = []
    for f in flights:
        counts = await repo.get_available_seat_counts(f.id)
        f_out = FlightOut.model_validate(f)
        f_out.available_first_seats = counts.get(SeatClass.FIRST, 0)
        f_out.available_business_seats = counts.get(SeatClass.BUSINESS, 0)
        f_out.available_economy_seats = counts.get(SeatClass.ECONOMY, 0)
        output.append(f_out)
    return output

@router.get("/{flight_id}", response_model=FlightOut)
async def get_flight(
    flight_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    repo = FlightRepository(db)
    flight = await repo.get_by_id(flight_id)
    if not flight:
        raise NotFoundException(f"Flight {flight_id} not found")
    
    counts = await repo.get_available_seat_counts(flight.id)
    f_out = FlightOut.model_validate(flight)
    f_out.available_first_seats = counts.get(SeatClass.FIRST, 0)
    f_out.available_business_seats = counts.get(SeatClass.BUSINESS, 0)
    f_out.available_economy_seats = counts.get(SeatClass.ECONOMY, 0)
    return f_out

@router.put("/{flight_id}", response_model=FlightOut)
async def update_flight(
    flight_id: str,
    data: FlightUpdate,
    current_user: User = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = FlightService(db)
    flight = await service.update_flight(flight_id, data, actor_email=current_user.email)
    return FlightOut.model_validate(flight)

@router.post("/{flight_id}/cancel", response_model=FlightOut)
async def cancel_flight(
    flight_id: str,
    data: FlightCancelRequest,
    current_user: User = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = FlightService(db)
    flight = await service.cancel_flight(flight_id, data.reason, actor_email=current_user.email)
    return FlightOut.model_validate(flight)

@router.get("/{flight_id}/seats", response_model=List[SeatOut])
async def get_flight_seats(
    flight_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = SeatService(db)
    seats = await service.get_flight_seats(flight_id)
    return [SeatOut.model_validate(s) for s in seats]
