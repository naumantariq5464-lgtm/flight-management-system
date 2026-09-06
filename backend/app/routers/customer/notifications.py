from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List
from decimal import Decimal
from app.database.session import get_db
from app.schemas.notification import NotificationOut, PriceAlertCreate, PriceAlertOut
from app.models.notification import Notification, PriceAlert
from app.models.user import User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["Customer Notifications"])

@router.get("", response_model=List[NotificationOut])
async def list_my_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Notification).where(
        Notification.recipient_email == current_user.email
    ).order_by(desc(Notification.created_at)).limit(50)
    
    res = await db.execute(stmt)
    return [NotificationOut.model_validate(n) for n in res.scalars().all()]

@router.post("/price-alerts", response_model=PriceAlertOut, status_code=status.HTTP_201_CREATED)
async def create_price_alert(
    data: PriceAlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    alert = PriceAlert(
        user_id=current_user.id,
        email=current_user.email,
        origin=data.origin.upper(),
        destination=data.destination.upper(),
        target_price=data.target_price,
        initial_price=data.target_price * Decimal("1.2"),
        current_price=data.target_price * Decimal("1.2"),
        is_active=True
    )
    db.add(alert)
    await db.flush()
    return PriceAlertOut.model_validate(alert)
