from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from app.models.fraud import FraudScore
from app.models.booking import Booking
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.schemas.fraud import FraudReviewRequest
from app.utils.enums import RiskLevel, FraudStatus, BookingStatus, AuditSource
from app.utils.exceptions import NotFoundException

class FraudService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_repo = AuditRepository(db)

    async def scan_booking_for_fraud(self, booking_id: str) -> FraudScore:
        """Evaluate heuristic fraud signals for a booking."""
        stmt = select(Booking).where(Booking.id == booking_id)
        res = await self.db.execute(stmt)
        booking = res.scalar_one_or_none()
        if not booking:
            raise NotFoundException(f"Booking {booking_id} not found")

        score = 0
        reasons = []

        # 1. Velocity check: check how many bookings this email made in last 24h
        since_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        vel_stmt = select(func.count(Booking.id)).where(
            and_(Booking.contact_email == booking.contact_email, Booking.created_at >= since_24h)
        )
        vel_res = await self.db.execute(vel_stmt)
        recent_count = vel_res.scalar() or 0
        if recent_count > 3:
            score += 35
            reasons.append(f"High booking velocity ({recent_count} bookings in 24 hours)")

        # 2. Large party size check
        if len(booking.passengers) >= 5:
            score += 20
            reasons.append("Large group booking (5+ passengers)")

        # 3. High total transaction amount check
        if booking.total_amount > 3000:
            score += 25
            reasons.append(f"High transaction value (${booking.total_amount})")

        # Determine Risk Level
        if score >= 75:
            risk_level = RiskLevel.CRITICAL
        elif score >= 50:
            risk_level = RiskLevel.HIGH
        elif score >= 25:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        fraud_record = FraudScore(
            booking_id=booking.id,
            user_id=booking.user_id,
            score=score,
            risk_level=risk_level,
            reasons="; ".join(reasons) if reasons else "Normal transaction behavior",
            status=FraudStatus.FLAGGED if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else FraudStatus.APPROVED
        )
        self.db.add(fraud_record)
        await self.db.flush()

        return fraud_record

    async def list_fraud_alerts(self, skip: int = 0, limit: int = 100) -> List[FraudScore]:
        stmt = select(FraudScore).order_by(desc(FraudScore.score)).offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def review_fraud_score(self, fraud_id: str, request: FraudReviewRequest, admin_user: User) -> FraudScore:
        stmt = select(FraudScore).where(FraudScore.id == fraud_id).with_for_update()
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise NotFoundException(f"Fraud alert {fraud_id} not found")

        record.status = request.status
        record.reviewed_by_user_id = admin_user.id
        record.reviewed_at = datetime.now(timezone.utc)
        record.review_notes = request.review_notes

        await self.audit_repo.create_log(
            action="FRAUD_REVIEW_DECISION",
            entity_type="FraudScore",
            entity_id=record.id,
            actor_email=admin_user.email,
            actor_role=admin_user.role.name.value,
            new_values={"status": request.status.value, "notes": request.review_notes},
            source=AuditSource.ADMIN
        )

        return record
