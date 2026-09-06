from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from typing import List, Optional
from datetime import datetime, timezone
from app.models.seat import Seat, SeatHold
from app.utils.enums import SeatStatus, SeatClass

class SeatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, seat_id: str, for_update: bool = False) -> Optional[Seat]:
        stmt = select(Seat).where(Seat.id == seat_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_seats_by_ids_for_update(self, seat_ids: List[str]) -> List[Seat]:
        """Row-level locking: SELECT ... FOR UPDATE to protect against simultaneous race conditions."""
        stmt = select(Seat).where(Seat.id.in_(seat_ids)).with_for_update()
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_flight(self, flight_id: str) -> List[Seat]:
        stmt = select(Seat).where(Seat.flight_id == flight_id).order_by(Seat.row.asc(), Seat.column.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_available_seats_for_class_for_update(
        self, 
        flight_id: str, 
        seat_class: SeatClass, 
        count: int
    ) -> List[Seat]:
        """Lock and return the next N available seats in a class."""
        stmt = select(Seat).where(
            and_(
                Seat.flight_id == flight_id,
                Seat.seat_class == seat_class,
                Seat.status == SeatStatus.AVAILABLE
            )
        ).order_by(Seat.row.asc(), Seat.column.asc()).limit(count).with_for_update()
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_bulk_seats(self, seats: List[Seat]) -> None:
        self.db.add_all(seats)
        await self.db.flush()

    async def create_hold(self, hold: SeatHold) -> SeatHold:
        self.db.add(hold)
        await self.db.flush()
        return hold

    async def get_active_hold_by_token(self, hold_token: str) -> Optional[SeatHold]:
        stmt = select(SeatHold).where(
            and_(
                SeatHold.hold_token == hold_token,
                SeatHold.is_released == False,
                SeatHold.expires_at > datetime.now(timezone.utc)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def release_expired_holds(self) -> int:
        """Find all expired holds and atomically revert their seats back to AVAILABLE."""
        now = datetime.now(timezone.utc)
        stmt = select(SeatHold).where(
            and_(
                SeatHold.expires_at <= now,
                SeatHold.is_released == False
            )
        ).with_for_update()
        
        result = await self.db.execute(stmt)
        expired_holds = list(result.scalars().all())
        
        released_count = 0
        for hold in expired_holds:
            hold.is_released = True
            # Update seat status back to AVAILABLE if it is still HELD
            seat_stmt = select(Seat).where(Seat.id == hold.seat_id).with_for_update()
            seat_res = await self.db.execute(seat_stmt)
            seat = seat_res.scalar_one_or_none()
            if seat and seat.status == SeatStatus.HELD:
                seat.status = SeatStatus.AVAILABLE
                released_count += 1
                
        await self.db.flush()
        return released_count
