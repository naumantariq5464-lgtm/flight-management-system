from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, asc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone
from app.models.waitlist import Waitlist
from app.utils.enums import WaitlistStatus, SeatClass

class WaitlistRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, waitlist_id: str, for_update: bool = False) -> Optional[Waitlist]:
        stmt = select(Waitlist).options(selectinload(Waitlist.flight)).where(Waitlist.id == waitlist_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_claim_token(self, claim_token: str) -> Optional[Waitlist]:
        stmt = select(Waitlist).options(selectinload(Waitlist.flight)).where(
            and_(
                Waitlist.claim_token == claim_token,
                Waitlist.status == WaitlistStatus.PROMOTED,
                Waitlist.claim_expires_at > datetime.now(timezone.utc)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_top_candidate_for_promotion(
        self, 
        flight_id: str, 
        seat_class: SeatClass
    ) -> Optional[Waitlist]:
        """Atomic candidate row lock using FOR UPDATE SKIP LOCKED for high-concurrency n8n processing."""
        stmt = select(Waitlist).where(
            and_(
                Waitlist.flight_id == flight_id,
                Waitlist.seat_class == seat_class,
                Waitlist.status == WaitlistStatus.WAITING
            )
        ).order_by(
            desc(Waitlist.priority_score),
            asc(Waitlist.created_at)
        ).limit(1).with_for_update(skip_locked=True)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_waitlist(
        self,
        flight_id: Optional[str] = None,
        status: Optional[WaitlistStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Waitlist]:
        stmt = select(Waitlist).options(selectinload(Waitlist.flight))
        conditions = []
        if flight_id:
            conditions.append(Waitlist.flight_id == flight_id)
        if status:
            conditions.append(Waitlist.status == status)
        if conditions:
            stmt = stmt.where(and_(*conditions))
            
        stmt = stmt.order_by(desc(Waitlist.priority_score), asc(Waitlist.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, waitlist: Waitlist) -> Waitlist:
        self.db.add(waitlist)
        await self.db.flush()
        return waitlist

    async def update(self, waitlist: Waitlist) -> Waitlist:
        await self.db.flush()
        return waitlist
