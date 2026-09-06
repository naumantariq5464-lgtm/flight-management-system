from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timezone
from app.models.notification import Notification, PriceAlert
from app.models.flight import Flight
from app.repositories.flight_repo import FlightRepository
from app.repositories.audit_repo import AuditRepository
from app.utils.enums import NotificationType, NotificationStatus, FlightStatus, AuditSource
from app.config.settings import settings

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.flight_repo = FlightRepository(db)
        self.audit_repo = AuditRepository(db)

    async def create_notification(
        self,
        recipient_email: str,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.EMAIL,
        source: AuditSource = AuditSource.FASTAPI,
        flight_id: Optional[str] = None,
        booking_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Notification:
        # CANCELLED FLIGHT SUPPRESSION: Check if flight is cancelled
        status = NotificationStatus.PENDING
        if flight_id:
            flight = await self.flight_repo.get_by_id(flight_id)
            if flight and flight.status == FlightStatus.CANCELLED and "cancellation" not in title.lower():
                # Suppress reminders and standard alerts for cancelled flights!
                status = NotificationStatus.SUPPRESSED

        notif = Notification(
            recipient_email=recipient_email,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            status=status,
            source=source,
            flight_id=flight_id,
            booking_id=booking_id,
            sent_at=datetime.now(timezone.utc) if status != NotificationStatus.SUPPRESSED else None
        )
        self.db.add(notif)
        await self.db.flush()
        return notif
