from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import uuid
from app.models.waitlist import Waitlist
from app.models.flight import Flight
from app.models.user import User
from app.schemas.waitlist import WaitlistJoinRequest
from app.repositories.waitlist_repo import WaitlistRepository
from app.repositories.flight_repo import FlightRepository
from app.repositories.seat_repo import SeatRepository
from app.repositories.audit_repo import AuditRepository
from app.utils.enums import WaitlistStatus, SeatStatus, FlightStatus, FareType, AuditSource
from app.utils.exceptions import NotFoundException, FlightCancelledException, BadRequestException

class WaitlistService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.waitlist_repo = WaitlistRepository(db)
        self.flight_repo = FlightRepository(db)
        self.seat_repo = SeatRepository(db)
        self.audit_repo = AuditRepository(db)

    def _compute_priority_score(self, loyalty_tier: str, fare_type: FareType) -> int:
        score = 0
        tier_upper = (loyalty_tier or "STANDARD").upper()
        if tier_upper == "PLATINUM":
            score += 3000
        elif tier_upper == "GOLD":
            score += 2000
        elif tier_upper == "SILVER":
            score += 1000
            
        if fare_type == FareType.FLEXIBLE:
            score += 500
            
        return score

    async def join_waitlist(
        self, 
        request: WaitlistJoinRequest, 
        user: Optional[User] = None
    ) -> Waitlist:
        flight = await self.flight_repo.get_by_id(request.flight_id)
        if not flight:
            raise NotFoundException(f"Flight {request.flight_id} not found")
        if flight.status == FlightStatus.CANCELLED:
            raise FlightCancelledException("Cannot join waitlist for a cancelled flight")

        loyalty_tier = user.loyalty_tier if user else "STANDARD"
        priority_score = self._compute_priority_score(loyalty_tier, request.fare_type)

        waitlist = Waitlist(
            flight_id=flight.id,
            user_id=user.id if user else None,
            passenger_first_name=request.passenger_first_name,
            passenger_last_name=request.passenger_last_name,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            seat_class=request.seat_class,
            fare_type=request.fare_type,
            loyalty_tier=loyalty_tier,
            priority_score=priority_score,
            status=WaitlistStatus.WAITING
        )
        await self.waitlist_repo.create(waitlist)

        # Audit Log
        await self.audit_repo.create_log(
            action="WAITLIST_JOINED",
            entity_type="Waitlist",
            entity_id=waitlist.id,
            actor_email=request.contact_email,
            new_values={
                "flight_id": flight.id,
                "seat_class": request.seat_class.value,
                "priority_score": priority_score
            },
            source=AuditSource.FASTAPI
        )

        return waitlist

    async def promote_next_candidate(
        self, 
        flight_id: str, 
        seat_class: str,
        source: AuditSource = AuditSource.N8N
    ) -> Optional[Waitlist]:
        """Atomic candidate promotion with FOR UPDATE SKIP LOCKED and Cancelled-flight conflict safety."""
        # 1. Check flight is not cancelled
        flight = await self.flight_repo.get_by_id(flight_id, for_update=True)
        if not flight or flight.status == FlightStatus.CANCELLED:
            # Conflict resolution: If flight is cancelled, skip promotion
            return None

        # 2. Lock next available seat
        available_seats = await self.seat_repo.get_available_seats_for_class_for_update(flight_id, seat_class, 1)
        if not available_seats:
            return None
        promoted_seat = available_seats[0]

        # 3. Lock candidate row
        candidate = await self.waitlist_repo.get_top_candidate_for_promotion(flight_id, seat_class)
        if not candidate:
            return None

        # 4. Hold seat for candidate and set claim window (24 hours)
        now = datetime.now(timezone.utc)
        claim_token = f"CLAIM-{uuid.uuid4().hex[:12].upper()}"
        
        promoted_seat.status = SeatStatus.HELD
        candidate.status = WaitlistStatus.PROMOTED
        candidate.promoted_at = now
        candidate.claim_expires_at = now + timedelta(hours=24)
        candidate.promoted_seat_id = promoted_seat.id
        candidate.claim_token = claim_token

        await self.waitlist_repo.update(candidate)

        # 5. Audit Log
        await self.audit_repo.create_log(
            action="WAITLIST_PROMOTED",
            entity_type="Waitlist",
            entity_id=candidate.id,
            actor_email=candidate.contact_email,
            new_values={
                "flight_id": flight.id,
                "seat_number": promoted_seat.seat_number,
                "claim_token": claim_token,
                "claim_expires_at": str(candidate.claim_expires_at)
            },
            source=source
        )

        return candidate

    async def claim_promotion(self, claim_token: str) -> dict:
        waitlist = await self.waitlist_repo.get_by_claim_token(claim_token)
        if not waitlist:
            raise BadRequestException("Invalid or expired waitlist claim token")

        # Confirm seat is held for this passenger
        if waitlist.promoted_seat_id:
            seat = await self.seat_repo.get_by_id(waitlist.promoted_seat_id, for_update=True)
            if seat:
                seat.status = SeatStatus.BOOKED

        waitlist.status = WaitlistStatus.CLAIMED
        waitlist.claimed_at = datetime.now(timezone.utc)
        await self.waitlist_repo.update(waitlist)

        await self.audit_repo.create_log(
            action="WAITLIST_CLAIMED",
            entity_type="Waitlist",
            entity_id=waitlist.id,
            actor_email=waitlist.contact_email,
            source=AuditSource.FASTAPI
        )

        return {
            "message": "Waitlist seat successfully claimed and confirmed.",
            "flight_id": waitlist.flight_id,
            "passenger": f"{waitlist.passenger_first_name} {waitlist.passenger_last_name}"
        }
