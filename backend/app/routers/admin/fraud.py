from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.session import get_db
from app.schemas.fraud import FraudScoreOut, FraudReviewRequest
from app.models.user import User
from app.services.fraud_service import FraudService
from app.auth.dependencies import get_admin_user

router = APIRouter(prefix="/admin/fraud", tags=["Admin Fraud Detection"])

@router.get("", response_model=List[FraudScoreOut])
async def list_fraud_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = FraudService(db)
    records = await service.list_fraud_alerts(skip, limit)
    return [FraudScoreOut.model_validate(r) for r in records]

@router.post("/{fraud_id}/review", response_model=FraudScoreOut)
async def review_fraud_alert(
    fraud_id: str,
    request: FraudReviewRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = FraudService(db)
    record = await service.review_fraud_score(fraud_id, request, admin_user=current_user)
    return FraudScoreOut.model_validate(record)
