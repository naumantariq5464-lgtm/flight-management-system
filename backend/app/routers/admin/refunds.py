from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database.session import get_db
from app.schemas.refund import RefundOut, RefundApprovalRequest
from app.models.user import User
from app.services.refund_service import RefundService
from app.auth.dependencies import get_admin_user, get_super_admin_user
from app.utils.enums import RefundStatus

router = APIRouter(prefix="/admin/refunds", tags=["Admin Refunds"])

@router.get("", response_model=List[RefundOut])
async def list_refunds(
    status: Optional[RefundStatus] = None,
    requires_approval_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = RefundService(db)
    refunds = await service.list_refunds(status, requires_approval_only, skip, limit)
    return [RefundOut.model_validate(r) for r in refunds]

@router.post("/{refund_id}/approve", response_model=RefundOut)
async def approve_refund(
    refund_id: str,
    action: RefundApprovalRequest,
    current_user: User = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = RefundService(db)
    if action.approved:
        refund = await service.approve_refund(refund_id, admin_user=current_user, notes=action.notes)
    else:
        refund = await service.reject_refund(refund_id, admin_user=current_user, reason=action.notes or "Rejected by supervisor")
    return RefundOut.model_validate(refund)
