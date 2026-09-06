from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from app.models.booking import Booking, BookingPassenger, BookingSeat
from app.models.flight import Flight
from app.models.seat import Seat, SeatHold
from app.models.fare import Fare
from app.models.refund import TravelCredit
from app.schemas.booking import BookingCreateRequest, BookingOut, BookingPassengerOut
from app.repositories.booking_repo import BookingRepository
from app.repositories.flight_repo import FlightRepository
from app.repositories.seat_repo import SeatRepository
from app.repositories.refund_repo import RefundRepository
from app.repositories.audit_repo import AuditRepository
from app.utils.enums import (
    BookingStatus, 
    SeatStatus, 
    FlightStatus, 
    CreditStatus, 
    AuditSource, 
    SeatClass, 
    FareType,
    NotificationType,
    NotificationStatus
)
from app.utils.exceptions import (
    NotFoundException, 
    SeatUnavailableException, 
    FlightCancelledException, 
    BadRequestException, 
    HoldExpiredException
)
from app.utils.helpers import generate_pnr, generate_ticket_number, utc_now

class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.flight_repo = FlightRepository(db)
        self.seat_repo = SeatRepository(db)
        self.refund_repo = RefundRepository(db)
        self.audit_repo = AuditRepository(db)

    async def create_booking(
        self, 
        request: BookingCreateRequest, 
        user_id: Optional[str] = None,
        actor_email: Optional[str] = None
    ) -> Booking:
        """Atomic Booking Creation with Row Locking: Prevents overselling and race conditions."""
        # 1. First cleanup any expired holds
        await self.seat_repo.release_expired_holds()

        # 2. Lock and fetch Flight
        flight = await self.flight_repo.get_by_id(request.flight_id, for_update=True)
        if not flight:
            raise NotFoundException(f"Flight {request.flight_id} not found")
        if flight.status == FlightStatus.CANCELLED:
            raise FlightCancelledException("Cannot book a flight that is cancelled")

        # 2b. Class-Specific Booking Cutoff Validation (Economy: 60m, First/Biz: 30m before departure)
        time_until_dep = (flight.departure_time - datetime.now(timezone.utc)).total_seconds() / 60.0
        min_cutoff = 30.0 if request.seat_class in [SeatClass.FIRST, SeatClass.BUSINESS] else 60.0
        if time_until_dep < min_cutoff:
            raise BadRequestException(
                f"Booking closed for {request.seat_class.value} class. Must book at least {int(min_cutoff)} minutes before departure."
            )

        # 3. Retrieve Fare Price for Flight + Class + FareType
        fare_stmt = select(Fare).where(
            and_(
                Fare.flight_id == flight.id,
                Fare.seat_class == request.seat_class,
                Fare.fare_type == request.fare_type
            )
        )
        fare_res = await self.db.execute(fare_stmt)
        fare = fare_res.scalar_one_or_none()
        
        base_unit_price = fare.price if fare else flight.base_price_economy
        passenger_count = len(request.passengers)
        total_amount = base_unit_price * Decimal(str(passenger_count))

        # 4. Handle Travel Credit deduction if provided
        credit_deducted = Decimal("0.00")
        if request.credit_code:
            credit = await self.refund_repo.get_credit_by_code(request.credit_code)
            if not credit:
                raise BadRequestException("Invalid or expired travel credit code")
            if credit.balance_amount >= total_amount:
                credit_deducted = total_amount
                credit.balance_amount -= total_amount
                if credit.balance_amount == Decimal("0.00"):
                    credit.status = CreditStatus.USED
            else:
                credit_deducted = credit.balance_amount
                credit.balance_amount = Decimal("0.00")
                credit.status = CreditStatus.USED
            await self.refund_repo.update_travel_credit(credit)

        # 5. Acquire Seats with Row-Level Locking (SELECT FOR UPDATE)
        assigned_seats: List[Seat] = []
        
        if request.hold_token:
            # If user has a hold token, retrieve held seats
            hold_stmt = select(SeatHold).where(
                and_(
                    SeatHold.hold_token == request.hold_token,
                    SeatHold.is_released == False,
                    SeatHold.expires_at > datetime.now(timezone.utc)
                )
            ).with_for_update()
            hold_res = await self.db.execute(hold_stmt)
            holds = list(hold_res.scalars().all())
            
            if len(holds) < passenger_count:
                raise HoldExpiredException("Seat hold has expired or does not cover all passengers")
            
            held_seat_ids = [h.seat_id for h in holds]
            seats = await self.seat_repo.get_seats_by_ids_for_update(held_seat_ids)
            for s in seats:
                if s.status != SeatStatus.HELD:
                    raise SeatUnavailableException(f"Seat {s.seat_number} is no longer held (status: {s.status.value})")
                assigned_seats.append(s)
                
            # Release the hold records as they are being converted to confirmed booking
            for h in holds:
                h.is_released = True
        else:
            # Check if specific seat IDs were passed in passengers
            explicit_seat_ids = [p.seat_id for p in request.passengers if p.seat_id]
            if explicit_seat_ids:
                seats = await self.seat_repo.get_seats_by_ids_for_update(explicit_seat_ids)
                if len(seats) == passenger_count:
                    for s in seats:
                        if s.flight_id == flight.id and s.status == SeatStatus.AVAILABLE:
                            assigned_seats.append(s)
                            # Align seat class dynamically with the actual selected seat
                            request.seat_class = s.seat_class

            # Fallback to auto-assign if explicit seats were stale or not fully resolved
            if len(assigned_seats) < passenger_count:
                available_seats = await self.seat_repo.get_available_seats_for_class_for_update(
                    flight_id=flight.id,
                    seat_class=request.seat_class,
                    count=passenger_count
                )
                if len(available_seats) < passenger_count:
                    # Try economy if requested class is full
                    available_seats = await self.seat_repo.get_available_seats_for_class_for_update(
                        flight_id=flight.id,
                        seat_class=SeatClass.ECONOMY,
                        count=passenger_count
                    )
                if len(available_seats) < passenger_count:
                    raise SeatUnavailableException(
                        f"Not enough available seats on Flight {flight.flight_number}. Available: {len(available_seats)}"
                    )
                assigned_seats = available_seats[:passenger_count]

        # 6. Mark all assigned seats as BOOKED atomically
        for s in assigned_seats:
            s.status = SeatStatus.BOOKED

        # 7. Generate PNR
        pnr = generate_pnr()
        while await self.booking_repo.get_by_pnr(pnr):
            pnr = generate_pnr()

        # 8. Create Booking Entity
        booking = Booking(
            pnr=pnr,
            user_id=user_id,
            flight_id=flight.id,
            fare_type=request.fare_type,
            seat_class=request.seat_class,
            status=BookingStatus.CONFIRMED,
            total_amount=total_amount - credit_deducted,
            currency=flight.currency,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            payment_reference=f"PAY-{pnr}-{int(datetime.now(timezone.utc).timestamp())}",
            confirmed_at=utc_now()
        )
        await self.booking_repo.create(booking)

        # 9. Create BookingPassenger and BookingSeat records
        for idx, p_input in enumerate(request.passengers):
            assigned_seat = assigned_seats[idx]
            passenger = BookingPassenger(
                booking_id=booking.id,
                first_name=p_input.first_name,
                last_name=p_input.last_name,
                date_of_birth=p_input.date_of_birth,
                passport_number=p_input.passport_number,
                nationality=p_input.nationality,
                e_ticket_number=generate_ticket_number(),
                is_cancelled=False
            )
            self.db.add(passenger)
            await self.db.flush()

            booking_seat = BookingSeat(
                booking_id=booking.id,
                passenger_id=passenger.id,
                seat_id=assigned_seat.id,
                seat_price=base_unit_price
            )
            self.db.add(booking_seat)

        # 10. Write Audit Log
        await self.audit_repo.create_log(
            action="BOOKING_CONFIRMED",
            entity_type="Booking",
            entity_id=booking.id,
            actor_email=actor_email or request.contact_email,
            new_values={
                "pnr": booking.pnr,
                "flight_number": flight.flight_number,
                "passenger_count": passenger_count,
                "total_amount": str(booking.total_amount),
                "seat_numbers": [s.seat_number for s in assigned_seats]
            },
            source=AuditSource.FASTAPI
        )

        # 11. Transactional Notification Record (Confirmation Receipt)
        from app.models.notification import Notification
        from app.utils.enums import NotificationType, NotificationStatus
        notif = Notification(
            recipient_email=booking.contact_email,
            user_id=user_id,
            flight_id=flight.id,
            booking_id=booking.id,
            title=f"Booking Confirmation - PNR: {booking.pnr}",
            message=f"Your booking on Flight {flight.flight_number} ({flight.origin}->{flight.destination}) is confirmed.",
            notification_type=NotificationType.EMAIL,
            status=NotificationStatus.SENT,
            source=AuditSource.FASTAPI,
            sent_at=utc_now()
        )
        self.db.add(notif)

        return await self.booking_repo.get_by_id(booking.id)
