from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from app.models.booking import Booking, BookingPassenger, BookingSeat
from app.models.flight import Flight
from app.models.seat import Seat
from app.models.fare import FareRule
from app.models.refund import Refund, TravelCredit
from app.repositories.booking_repo import BookingRepository
from app.repositories.seat_repo import SeatRepository
from app.repositories.refund_repo import RefundRepository
from app.repositories.audit_repo import AuditRepository
from app.utils.enums import BookingStatus, SeatStatus, RefundStatus, RefundType, CreditStatus, FareType, AuditSource
from app.utils.exceptions import NotFoundException, BadRequestException
from app.utils.helpers import generate_credit_code, utc_now

class CancellationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.seat_repo = SeatRepository(db)
        self.refund_repo = RefundRepository(db)
        self.audit_repo = AuditRepository(db)

    async def cancel_booking(
        self, 
        booking_id: str, 
        reason: str, 
        actor_email: str = "customer"
    ) -> dict:
        """Full booking cancellation with dynamic fare policy computation."""
        booking = await self.booking_repo.get_by_id(booking_id, for_update=True)
        if not booking:
            booking = await self.booking_repo.get_by_pnr(booking_id, for_update=True)
        if not booking:
            raise NotFoundException(f"Booking {booking_id} not found")
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.REFUNDED]:
            raise BadRequestException("Booking is already cancelled or refunded")

        # 1. Fetch FareRule for this booking's fare_type
        rule_stmt = select(FareRule).where(FareRule.fare_type == booking.fare_type)
        rule_res = await self.db.execute(rule_stmt)
        fare_rule = rule_res.scalar_one_or_none()

        # 2. Calculate eligible refund / credit amount
        cancellation_fee_percent = Decimal(str(fare_rule.cancellation_fee_percent if fare_rule else 100))
        is_refundable = fare_rule.is_refundable if fare_rule else False
        
        refundable_fraction = (Decimal("100") - cancellation_fee_percent) / Decimal("100")
        eligible_amount = booking.total_amount * max(Decimal("0.00"), refundable_fraction)

        # 3. Release all active assigned seats back to AVAILABLE
        seat_ids_to_release = [bs.seat_id for bs in booking.seats]
        if seat_ids_to_release:
            seats = await self.seat_repo.get_seats_by_ids_for_update(seat_ids_to_release)
            for s in seats:
                s.status = SeatStatus.AVAILABLE

        # 4. Mark all passengers as cancelled
        now = utc_now()
        for p in booking.passengers:
            p.is_cancelled = True
            p.cancelled_at = now

        # 5. Create Refund or TravelCredit record if eligible
        refund_record = None
        travel_credit_record = None

        if is_refundable and eligible_amount > Decimal("0.00"):
            refund_record = Refund(
                booking_id=booking.id,
                user_id=booking.user_id,
                amount=eligible_amount,
                currency=booking.currency,
                reason=reason,
                refund_type=RefundType.FULL,
                status=RefundStatus.COMPLETED if cancellation_fee_percent == 0 else RefundStatus.PENDING,
                requires_human_approval=(cancellation_fee_percent > 0)
            )
            await self.refund_repo.create_refund(refund_record)
        elif not is_refundable and booking.fare_type == FareType.FLEXIBLE:
            # If flexible but credit-only, issue travel credit
            travel_credit_record = TravelCredit(
                credit_code=generate_credit_code(),
                user_id=booking.user_id,
                passenger_name=f"{booking.passengers[0].first_name} {booking.passengers[0].last_name}" if booking.passengers else "Valued Passenger",
                original_amount=booking.total_amount,
                balance_amount=booking.total_amount,
                currency=booking.currency,
                expires_at=datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1),
                status=CreditStatus.ACTIVE,
                source_booking_id=booking.id
            )
            await self.refund_repo.create_travel_credit(travel_credit_record)

        # 6. Mark booking as CANCELLED
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = now
        await self.booking_repo.update(booking)

        # 7. Audit Log
        await self.audit_repo.create_log(
            action="BOOKING_CANCELLED",
            entity_type="Booking",
            entity_id=booking.id,
            actor_email=actor_email,
            new_values={
                "pnr": booking.pnr,
                "reason": reason,
                "is_refundable": is_refundable,
                "eligible_refund_amount": str(eligible_amount),
                "has_travel_credit": bool(travel_credit_record)
            },
            source=AuditSource.FASTAPI
        )

        # 8. Transactional Cancellation Receipt Notification
        from app.models.notification import Notification
        from app.utils.enums import NotificationType, NotificationStatus
        notif = Notification(
            recipient_email=booking.contact_email,
            user_id=booking.user_id,
            flight_id=booking.flight_id,
            booking_id=booking.id,
            title=f"Booking Cancellation Receipt - PNR: {booking.pnr}",
            message=f"Your booking (PNR: {booking.pnr}) has been cancelled. Refund/Credit details: ${eligible_amount}.",
            notification_type=NotificationType.EMAIL,
            status=NotificationStatus.SENT,
            source=AuditSource.FASTAPI,
            sent_at=now
        )
        self.db.add(notif)

        # Trigger n8n Automation Webhook (Freed Seat + Waitlist Promotion Trigger)
        try:
            from app.utils.n8n_client import trigger_n8n_webhook
            import asyncio
            asyncio.create_task(trigger_n8n_webhook(
                event_type="WAITLIST_PROMOTION",
                data={
                    "flight_id": booking.flight_id,
                    "pnr": booking.pnr,
                    "customer_email": booking.contact_email,
                    "released_seat_ids": seat_ids_to_release,
                    "message": f"Seat released from cancelled booking {booking.pnr}. Auto-promoting waitlist."
                }
            ))
        except Exception:
            pass

        return {
            "pnr": booking.pnr,
            "status": booking.status.value,
            "is_refundable": is_refundable,
            "refund_amount": eligible_amount,
            "travel_credit_code": travel_credit_record.credit_code if travel_credit_record else None,
            "message": "Booking successfully cancelled and seat inventory released."
        }

    async def partial_cancel(
        self, 
        booking_id: str, 
        passenger_ids: List[str], 
        reason: str,
        actor_email: str = "customer"
    ) -> dict:
        """Partial Cancellation: Cancel only selected passengers in a group booking."""
        booking = await self.booking_repo.get_by_id(booking_id, for_update=True)
        if not booking:
            booking = await self.booking_repo.get_by_pnr(booking_id, for_update=True)
        if not booking:
            raise NotFoundException(f"Booking {booking_id} not found")
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.REFUNDED]:
            raise BadRequestException("Cannot partially cancel an inactive booking")

        active_passengers = [p for p in booking.passengers if not p.is_cancelled]
        if len(passenger_ids) >= len(active_passengers):
            # If cancelling all remaining passengers, delegate to full cancellation
            return await self.cancel_booking(booking_id, reason, actor_email)

        # Fetch FareRule
        rule_stmt = select(FareRule).where(FareRule.fare_type == booking.fare_type)
        rule_res = await self.db.execute(rule_stmt)
        fare_rule = rule_res.scalar_one_or_none()

        now = utc_now()
        cancelled_passenger_count = 0
        seats_to_release = []

        # Find passengers and associated seats
        for p in booking.passengers:
            if p.id in passenger_ids and not p.is_cancelled:
                p.is_cancelled = True
                p.cancelled_at = now
                cancelled_passenger_count += 1
                
                # Find passenger seat
                for bs in booking.seats:
                    if bs.passenger_id == p.id:
                        seats_to_release.append(bs.seat_id)

        if cancelled_passenger_count == 0:
            raise BadRequestException("No active matching passengers found to cancel")

        # Release the specific cancelled seats
        if seats_to_release:
            seats = await self.seat_repo.get_seats_by_ids_for_update(seats_to_release)
            for s in seats:
                s.status = SeatStatus.AVAILABLE

        # Proportional refund computation
        unit_price = booking.total_amount / Decimal(str(len(booking.passengers)))
        cancellation_fee_percent = Decimal(str(fare_rule.cancellation_fee_percent if fare_rule else 100))
        is_refundable = fare_rule.is_refundable if fare_rule else False
        refundable_fraction = (Decimal("100") - cancellation_fee_percent) / Decimal("100")
        
        refund_amount = (unit_price * Decimal(str(cancelled_passenger_count))) * max(Decimal("0.00"), refundable_fraction)

        if is_refundable and refund_amount > Decimal("0.00"):
            refund = Refund(
                booking_id=booking.id,
                user_id=booking.user_id,
                amount=refund_amount,
                currency=booking.currency,
                reason=f"Partial cancellation: {reason}",
                refund_type=RefundType.PARTIAL,
                status=RefundStatus.PENDING,
                requires_human_approval=True
            )
            await self.refund_repo.create_refund(refund)

        # Audit Log
        await self.audit_repo.create_log(
            action="BOOKING_PARTIAL_CANCELLED",
            entity_type="Booking",
            entity_id=booking.id,
            actor_email=actor_email,
            new_values={
                "pnr": booking.pnr,
                "cancelled_passenger_ids": passenger_ids,
                "refund_amount": str(refund_amount),
                "released_seats_count": len(seats_to_release)
            },
            source=AuditSource.FASTAPI
        )

        return {
            "pnr": booking.pnr,
            "cancelled_passengers_count": cancelled_passenger_count,
            "refund_amount": refund_amount,
            "message": "Selected passengers cancelled and their seats returned to available inventory."
        }
