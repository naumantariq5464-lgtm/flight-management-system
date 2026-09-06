from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import uuid
from app.models.seat import Seat, SeatHold
from app.models.flight import Flight
from app.schemas.seat import SeatHoldRequest, SeatHoldResponse, SeatOut
from app.repositories.seat_repo import SeatRepository
from app.repositories.flight_repo import FlightRepository
from app.repositories.audit_repo import AuditRepository
from app.utils.enums import SeatStatus, FlightStatus, AuditSource
from app.utils.exceptions import NotFoundException, SeatUnavailableException, FlightCancelledException, BadRequestException
from app.config.settings import settings

class SeatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.seat_repo = SeatRepository(db)
        self.flight_repo = FlightRepository(db)
        self.audit_repo = AuditRepository(db)

    async def get_flight_seats(self, flight_id: str) -> List[Seat]:
        flight = await self.flight_repo.get_by_id(flight_id)
        if not flight:
            raise NotFoundException(f"Flight {flight_id} not found")
        
        # Clean up any expired holds before listing
        await self.seat_repo.release_expired_holds()
        
        return await self.seat_repo.list_by_flight(flight_id)

    async def hold_seats(
        self, 
        request: SeatHoldRequest, 
        user_id: Optional[str] = None,
        actor_email: Optional[str] = None
    ) -> SeatHoldResponse:
        """Atomic seat hold with row locking to protect against simultaneous race conditions."""
        flight = await self.flight_repo.get_by_id(request.flight_id)
        if not flight:
            raise NotFoundException(f"Flight {request.flight_id} not found")
        if flight.status == FlightStatus.CANCELLED:
            raise FlightCancelledException("Cannot hold seats on a cancelled flight")

        # 1. First release any globally expired holds
        await self.seat_repo.release_expired_holds()

        # 2. Acquire row-level locks on requested seats
        seats = await self.seat_repo.get_seats_by_ids_for_update(request.seat_ids)
        if len(seats) != len(request.seat_ids):
            raise BadRequestException("One or more requested seat IDs do not exist")

        # 3. Verify that all seats belong to this flight and are currently AVAILABLE
        for seat in seats:
            if seat.flight_id != request.flight_id:
                raise BadRequestException(f"Seat {seat.seat_number} does not belong to flight {request.flight_id}")
            if seat.status != SeatStatus.AVAILABLE:
                raise SeatUnavailableException(f"Seat {seat.seat_number} is no longer available (status: {seat.status.value})")

        # 4. Generate unique hold token and expiration timestamp
        hold_token = f"HOLD-{uuid.uuid4().hex[:12].upper()}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.SEAT_HOLD_DURATION_MINUTES)

        held_seats_out = []
        for seat in seats:
            seat.status = SeatStatus.HELD
            hold = SeatHold(
                seat_id=seat.id,
                flight_id=flight.id,
                user_id=user_id,
                hold_token=hold_token,
                expires_at=expires_at,
                is_released=False
            )
            await self.seat_repo.create_hold(hold)
            held_seats_out.append(SeatOut.model_validate(seat))

        # 5. Audit Log
        await self.audit_repo.create_log(
            action="SEATS_HELD",
            entity_type="SeatHold",
            entity_id=hold_token,
            actor_email=actor_email or "guest_customer",
            new_values={
                "flight_id": flight.id,
                "seat_numbers": [s.seat_number for s in seats],
                "expires_at": str(expires_at)
            },
            source=AuditSource.FASTAPI
        )

        return SeatHoldResponse(
            hold_token=hold_token,
            flight_id=flight.id,
            held_seats=held_seats_out,
            expires_at=expires_at
        )

    async def release_expired_holds(self) -> int:
        return await self.seat_repo.release_expired_holds()
