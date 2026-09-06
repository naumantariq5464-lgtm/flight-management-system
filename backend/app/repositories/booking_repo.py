from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.booking import Booking, BookingPassenger, BookingSeat
from app.models.flight import Flight
from app.utils.enums import BookingStatus

class BookingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, booking_id: str, for_update: bool = False) -> Optional[Booking]:
        stmt = select(Booking).options(
            selectinload(Booking.passengers),
            selectinload(Booking.seats).selectinload(BookingSeat.seat),
            selectinload(Booking.flight)
        ).where(Booking.id == booking_id)
        
        if for_update:
            stmt = stmt.with_for_update()
            
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_pnr(self, pnr: str) -> Optional[Booking]:
        stmt = select(Booking).options(
            selectinload(Booking.passengers),
            selectinload(Booking.seats).selectinload(BookingSeat.seat),
            selectinload(Booking.flight)
        ).where(Booking.pnr == pnr.upper())
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_bookings(
        self,
        user_id: Optional[str] = None,
        flight_id: Optional[str] = None,
        status: Optional[BookingStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Booking]:
        stmt = select(Booking).options(
            selectinload(Booking.passengers),
            selectinload(Booking.seats).selectinload(BookingSeat.seat),
            selectinload(Booking.flight)
        )
        conditions = []
        if user_id:
            conditions.append(Booking.user_id == user_id)
        if flight_id:
            conditions.append(Booking.flight_id == flight_id)
        if status:
            conditions.append(Booking.status == status)
        if conditions:
            stmt = stmt.where(and_(*conditions))
            
        stmt = stmt.order_by(desc(Booking.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        await self.db.flush()
        return booking

    async def update(self, booking: Booking) -> Booking:
        await self.db.flush()
        return booking

    async def get_passenger_by_id(self, passenger_id: str) -> Optional[BookingPassenger]:
        stmt = select(BookingPassenger).where(BookingPassenger.id == passenger_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
