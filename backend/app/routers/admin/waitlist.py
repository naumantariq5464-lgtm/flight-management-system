from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database.session import get_db
from app.schemas.waitlist import WaitlistOut
from app.schemas.flight import FlightOut
from app.models.user import User
from app.repositories.waitlist_repo import WaitlistRepository
from app.services.waitlist_service import WaitlistService
from app.auth.dependencies import get_admin_user
from app.utils.enums import WaitlistStatus, SeatClass, AuditSource
from app.utils.exceptions import NotFoundException

router = APIRouter(prefix="/admin/waitlist", tags=["Admin Waitlist"])

@router.get("", response_model=List[WaitlistOut])
async def list_admin_waitlist(
    flight_id: Optional[str] = None,
    status: Optional[WaitlistStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    repo = WaitlistRepository(db)
    items = await repo.list_waitlist(flight_id=flight_id, status=status, skip=skip, limit=limit)
    
    out = []
    for w in items:
        w_out = WaitlistOut.model_validate(w)
        if w.flight:
            w_out.flight = FlightOut.model_validate(w.flight)
        out.append(w_out)
    return out

@router.post("/promote/{flight_id}/{seat_class}", response_model=Optional[WaitlistOut])
async def trigger_manual_promotion(
    flight_id: str,
    seat_class: SeatClass,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = WaitlistService(db)
    promoted = await service.promote_next_candidate(flight_id, seat_class, source=AuditSource.ADMIN)
    if not promoted:
        return None
    return WaitlistOut.model_validate(promoted)
