from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timezone
from app.models.refund import Refund
from app.models.user import User
from app.repositories.refund_repo import RefundRepository
from app.repositories.audit_repo import AuditRepository
from app.utils.enums import RefundStatus, AuditSource
from app.utils.exceptions import NotFoundException, BadRequestException

class RefundService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.refund_repo = RefundRepository(db)
        self.audit_repo = AuditRepository(db)

    async def list_refunds(
        self,
        status: Optional[RefundStatus] = None,
        requires_approval_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Refund]:
        return await self.refund_repo.list_refunds(status, requires_approval_only, skip, limit)

    async def approve_refund(self, refund_id: str, admin_user: User, notes: Optional[str] = None) -> Refund:
        refund = await self.refund_repo.get_by_id(refund_id, for_update=True)
        if not refund:
            raise NotFoundException(f"Refund {refund_id} not found")
        if refund.status != RefundStatus.PENDING:
            raise BadRequestException(f"Refund is already {refund.status.value}")

        refund.status = RefundStatus.COMPLETED
        refund.approved_by_user_id = admin_user.id
        refund.processed_at = datetime.now(timezone.utc)
        await self.refund_repo.update_refund(refund)

        await self.audit_repo.create_log(
            action="REFUND_APPROVED",
            entity_type="Refund",
            entity_id=refund.id,
            actor_email=admin_user.email,
            actor_role=admin_user.role.name.value,
            new_values={"status": RefundStatus.COMPLETED.value, "notes": notes},
            source=AuditSource.ADMIN
        )

        return refund

    async def reject_refund(self, refund_id: str, admin_user: User, reason: str) -> Refund:
        refund = await self.refund_repo.get_by_id(refund_id, for_update=True)
        if not refund:
            raise NotFoundException(f"Refund {refund_id} not found")
        if refund.status != RefundStatus.PENDING:
            raise BadRequestException(f"Refund is already {refund.status.value}")

        refund.status = RefundStatus.FAILED
        refund.escalation_reason = f"Rejected by admin: {reason}"
        refund.processed_at = datetime.now(timezone.utc)
        await self.refund_repo.update_refund(refund)

        await self.audit_repo.create_log(
            action="REFUND_REJECTED",
            entity_type="Refund",
            entity_id=refund.id,
            actor_email=admin_user.email,
            actor_role=admin_user.role.name.value,
            new_values={"status": RefundStatus.FAILED.value, "rejection_reason": reason},
            source=AuditSource.ADMIN
        )

        return refund
