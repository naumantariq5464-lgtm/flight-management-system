from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone
from app.models.refund import Refund, TravelCredit
from app.utils.enums import RefundStatus, CreditStatus

class RefundRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, refund_id: str, for_update: bool = False) -> Optional[Refund]:
        stmt = select(Refund).options(
            selectinload(Refund.booking),
            selectinload(Refund.passenger)
        ).where(Refund.id == refund_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_refunds(
        self,
        status: Optional[RefundStatus] = None,
        requires_approval_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Refund]:
        stmt = select(Refund).options(
            selectinload(Refund.booking),
            selectinload(Refund.passenger)
        )
        conditions = []
        if status:
            conditions.append(Refund.status == status)
        if requires_approval_only:
            conditions.append(Refund.requires_human_approval == True)
        if conditions:
            stmt = stmt.where(and_(*conditions))
            
        stmt = stmt.order_by(desc(Refund.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_refund(self, refund: Refund) -> Refund:
        self.db.add(refund)
        await self.db.flush()
        return refund

    async def update_refund(self, refund: Refund) -> Refund:
        await self.db.flush()
        return refund

    async def get_credit_by_code(self, code: str) -> Optional[TravelCredit]:
        stmt = select(TravelCredit).where(
            and_(
                TravelCredit.credit_code == code.upper(),
                TravelCredit.status == CreditStatus.ACTIVE,
                TravelCredit.expires_at > datetime.now(timezone.utc)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_travel_credit(self, credit: TravelCredit) -> TravelCredit:
        self.db.add(credit)
        await self.db.flush()
        return credit

    async def update_travel_credit(self, credit: TravelCredit) -> TravelCredit:
        await self.db.flush()
        return credit
