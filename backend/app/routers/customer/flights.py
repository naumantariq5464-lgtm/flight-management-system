from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, date
from app.database.session import get_db
from app.schemas.flight import FlightOut
from app.schemas.seat import SeatOut
from app.schemas.fare import FareOut, FareRuleOut
from app.models.fare import Fare, FareRule
from app.services.flight_service import FlightService
from app.services.seat_service import SeatService
from app.repositories.flight_repo import FlightRepository
from app.utils.enums import SeatClass
from app.utils.exceptions import NotFoundException

router = APIRouter(prefix="/flights", tags=["Customer Flights"])

@router.get("/search", response_model=List[FlightOut])
async def search_flights(
    origin: Optional[str] = Query(None, description="3-letter IATA or city code e.g. LHE"),
    destination: Optional[str] = Query(None, description="3-letter IATA or city code e.g. DXB"),
    departure_date: Optional[str] = Query(None, description="YYYY-MM-DD e.g. 2026-10-15"),
    passengers: int = Query(1, ge=1, le=9),
    seat_class: Optional[SeatClass] = None,
    db: AsyncSession = Depends(get_db)
):
    repo = FlightRepository(db)
    parsed_date = date.fromisoformat(departure_date) if departure_date else None
    
    if origin or destination or parsed_date:
        flights = await repo.list_all(
            status=None,
            origin=origin.upper() if origin else None,
            destination=destination.upper() if destination else None
        )
        if parsed_date:
            flights = [f for f in flights if f.departure_time.date() == parsed_date]
    else:
        flights = await repo.list_all()
    
    results = []
    for f in flights:
        counts = await repo.get_available_seat_counts(f.id)
        f_out = FlightOut.model_validate(f)
        f_out.available_first_seats = counts.get(SeatClass.FIRST, 0)
        f_out.available_business_seats = counts.get(SeatClass.BUSINESS, 0)
        f_out.available_economy_seats = counts.get(SeatClass.ECONOMY, 0)
        
        # Check passenger threshold for requested class
        if seat_class:
            if counts.get(seat_class, 0) >= passengers:
                results.append(f_out)
        else:
            total_avail = sum(counts.values())
            if total_avail >= passengers:
                results.append(f_out)
                
    return results

@router.get("/connecting-search", response_model=List[dict])
async def search_connecting_flights(
    origin: str = Query(..., description="Starting origin airport e.g. LHE"),
    destination: str = Query(..., description="Final destination airport e.g. LHR"),
    departure_date: str = Query(..., description="YYYY-MM-DD"),
    passengers: int = Query(1, ge=1, le=9),
    db: AsyncSession = Depends(get_db)
):
    """Multi-Leg Connecting Search: Returns 2-leg itineraries with seat validation on both legs."""
    repo = FlightRepository(db)
    parsed_date = date.fromisoformat(departure_date)
    
    # 1. Find all Leg 1 flights from origin
    leg1_flights = await repo.search_flights(origin=origin.upper(), destination="%", departure_date=parsed_date, min_available_seats=passengers)
    
    valid_itineraries = []
    for f1 in leg1_flights:
        # 2. Find matching Leg 2 flights connecting to final destination
        f2_stmt = select(Flight).where(
            and_(
                Flight.origin == f1.destination,
                Flight.destination == destination.upper(),
                Flight.departure_time >= f1.arrival_time + timedelta(hours=1),
                Flight.departure_time <= f1.arrival_time + timedelta(hours=12),
                Flight.status == FlightStatus.SCHEDULED
            )
        )
        f2_res = await db.execute(f2_stmt)
        leg2_flights = list(f2_res.scalars().all())

        for f2 in leg2_flights:
            counts1 = await repo.get_available_seat_counts(f1.id)
            counts2 = await repo.get_available_seat_counts(f2.id)
            
            if sum(counts1.values()) >= passengers and sum(counts2.values()) >= passengers:
                valid_itineraries.append({
                    "itinerary_type": "CONNECTING",
                    "layover_airport": f1.destination,
                    "total_duration_hours": round((f2.arrival_time - f1.departure_time).total_seconds() / 3600.0, 1),
                    "leg_1": FlightOut.model_validate(f1),
                    "leg_2": FlightOut.model_validate(f2),
                    "combined_base_price": f1.base_price_economy + f2.base_price_economy,
                    "currency": f1.currency
                })

    return valid_itineraries

@router.get("/{flight_id}", response_model=FlightOut)
async def get_flight_details(
    flight_id: str,
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

@router.get("/{flight_id}/seatmap", response_model=List[SeatOut])
@router.get("/{flight_id}/seats", response_model=List[SeatOut])
async def get_interactive_seatmap(
    flight_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = SeatService(db)
    seats = await service.get_flight_seats(flight_id)
    return [SeatOut.model_validate(s) for s in seats]

@router.get("/{flight_id}/fares", response_model=List[FareOut])
async def get_flight_fares(
    flight_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Fare).where(Fare.flight_id == flight_id)
    res = await db.execute(stmt)
    fares = list(res.scalars().all())
    
    out = []
    for f in fares:
        rule_res = await db.execute(select(FareRule).where(FareRule.id == f.fare_rule_id))
        rule = rule_res.scalar_one_or_none()
        f_out = FareOut.model_validate(f)
        if rule:
            f_out.fare_rule = FareRuleOut.model_validate(rule)
        out.append(f_out)
    return out
