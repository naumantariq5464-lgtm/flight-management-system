from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, or_
from typing import List, Optional
from datetime import datetime, date
from app.models.flight import Flight
from app.models.seat import Seat
from app.utils.enums import FlightStatus, SeatStatus, SeatClass

class FlightRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, flight_id: str, for_update: bool = False) -> Optional[Flight]:
        stmt = select(Flight).where(Flight.id == flight_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_flight_number_and_departure(self, flight_number: str, departure_time: datetime) -> Optional[Flight]:
        stmt = select(Flight).where(
            and_(Flight.flight_number == flight_number, Flight.departure_time == departure_time)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[FlightStatus] = None,
        origin: Optional[str] = None,
        destination: Optional[str] = None
    ) -> List[Flight]:
        stmt = select(Flight)
        conditions = []
        if status:
            conditions.append(Flight.status == status)
        if origin:
            conditions.append(Flight.origin.ilike(f"%{origin}%"))
        if destination:
            conditions.append(Flight.destination.ilike(f"%{destination}%"))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(Flight.departure_time.asc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        min_available_seats: int = 1,
        seat_class: Optional[SeatClass] = None
    ) -> List[Flight]:
        start_of_day = datetime.combine(departure_date, datetime.min.time())
        end_of_day = datetime.combine(departure_date, datetime.max.time())
        
        stmt = select(Flight).where(
            and_(
                Flight.origin.ilike(origin),
                Flight.destination.ilike(destination),
                Flight.departure_time >= start_of_day,
                Flight.departure_time <= end_of_day,
                Flight.status == FlightStatus.SCHEDULED
            )
        ).order_by(Flight.departure_time.asc())
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, flight: Flight) -> Flight:
        self.db.add(flight)
        await self.db.flush()
        return flight

    async def update(self, flight: Flight) -> Flight:
        await self.db.flush()
        return flight

    async def get_available_seat_counts(self, flight_id: str) -> dict:
        """Calculate live available seat count per class for a flight."""
        stmt = select(
            Seat.seat_class,
            func.count(Seat.id)
        ).where(
            and_(
                Seat.flight_id == flight_id,
                Seat.status == SeatStatus.AVAILABLE
            )
        ).group_by(Seat.seat_class)
        
        result = await self.db.execute(stmt)
        counts = {SeatClass.FIRST: 0, SeatClass.BUSINESS: 0, SeatClass.ECONOMY: 0}
        for seat_class, count in result.all():
            counts[seat_class] = count
        return counts
