from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database.session import get_db
from app.schemas.waitlist import WaitlistJoinRequest, WaitlistOut, WaitlistClaimRequest
from app.models.user import User
from app.services.waitlist_service import WaitlistService
from app.auth.dependencies import get_optional_current_user

router = APIRouter(prefix="/waitlist", tags=["Customer Waitlist"])

@router.post("", response_model=WaitlistOut, status_code=status.HTTP_201_CREATED)
@router.post("/join", response_model=WaitlistOut, status_code=status.HTTP_201_CREATED)
async def join_waitlist(
    request: WaitlistJoinRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = WaitlistService(db)
    record = await service.join_waitlist(request, user=current_user)
    return WaitlistOut.model_validate(record)

@router.post("/claim")
@router.post("/claim/{claim_token}")
async def claim_promoted_seat(
    claim_token: Optional[str] = None,
    request: Optional[WaitlistClaimRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    token = claim_token or (request.claim_token if request else None)
    if not token:
        from app.utils.exceptions import BadRequestException
        raise BadRequestException("claim_token is required")
    service = WaitlistService(db)
    return await service.claim_promotion(token)
