from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from app.models.flight import Flight
from app.models.seat import Seat, SeatMap
from app.models.fare import Fare, FareRule
from app.models.schedule import ScheduleChange
from app.models.booking import Booking
from app.schemas.flight import FlightCreate, FlightUpdate
from app.repositories.flight_repo import FlightRepository
from app.repositories.seat_repo import SeatRepository
from app.repositories.audit_repo import AuditRepository
from app.utils.enums import FlightStatus, SeatStatus, SeatClass, FareType, BookingStatus, AuditSource
from app.utils.exceptions import BadRequestException, NotFoundException, FlightCancelledException

class FlightService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.flight_repo = FlightRepository(db)
        self.seat_repo = SeatRepository(db)
        self.audit_repo = AuditRepository(db)

    async def create_flight(self, data: FlightCreate, actor_email: str = "admin@flightsystem.com") -> Flight:
        # 1. Duplicate flight-number check for same day/route
        existing = await self.flight_repo.get_by_flight_number_and_departure(
            data.flight_number, data.departure_time
        )
        if existing:
            raise BadRequestException(f"Flight {data.flight_number} already exists for departure time {data.departure_time}")

        # 2. Instantiate Flight
        flight = Flight(
            flight_number=data.flight_number.upper(),
            origin=data.origin.upper(),
            origin_name=data.origin_name,
            destination=data.destination.upper(),
            destination_name=data.destination_name,
            departure_time=data.departure_time,
            arrival_time=data.arrival_time,
            aircraft_capacity=data.aircraft_capacity,
            first_class_seats=data.first_class_seats,
            business_class_seats=data.business_class_seats,
            economy_seats=data.economy_seats,
            base_price_economy=data.base_price_economy,
            base_price_business=data.base_price_business,
            base_price_first=data.base_price_first,
            currency=data.currency,
            overbooking_policy=data.overbooking_policy,
            overbooking_buffer_percentage=data.overbooking_buffer_percentage,
            aircraft_id=data.aircraft_id,
            status=FlightStatus.SCHEDULED
        )
        await self.flight_repo.create(flight)

        # 3. Generate Visual Seat Layout and Individual Seat Inventory Rows
        await self._generate_seats_for_flight(flight)

        # 4. Generate Default Fares for First, Business, Economy
        await self._generate_fares_for_flight(flight)

        # 5. Audit Log
        await self.audit_repo.create_log(
            action="FLIGHT_CREATED",
            entity_type="Flight",
            entity_id=flight.id,
            actor_email=actor_email,
            new_values=data.model_dump(mode="json"),
            source=AuditSource.ADMIN
        )

        return flight

    async def _generate_seats_for_flight(self, flight: Flight) -> None:
        """Systematically generate exact rows and seat maps matching class breakdowns."""
        seats = []
        current_row = 1
        
        # 1. First Class Seats
        if flight.first_class_seats > 0:
            first_cols = ["A", "B", "C", "D"]
            seats_created = 0
            while seats_created < flight.first_class_seats:
                for col in first_cols:
                    if seats_created >= flight.first_class_seats:
                        break
                    seats.append(Seat(
                        flight_id=flight.id,
                        seat_number=f"{current_row}{col}",
                        row=current_row,
                        column=col,
                        seat_class=SeatClass.FIRST,
                        status=SeatStatus.AVAILABLE,
                        extra_legroom=True
                    ))
                    seats_created += 1
                current_row += 1

        # 2. Business Class Seats
        if flight.business_class_seats > 0:
            biz_cols = ["A", "C", "D", "F"]
            seats_created = 0
            while seats_created < flight.business_class_seats:
                for col in biz_cols:
                    if seats_created >= flight.business_class_seats:
                        break
                    seats.append(Seat(
                        flight_id=flight.id,
                        seat_number=f"{current_row}{col}",
                        row=current_row,
                        column=col,
                        seat_class=SeatClass.BUSINESS,
                        status=SeatStatus.AVAILABLE,
                        extra_legroom=True
                    ))
                    seats_created += 1
                current_row += 1

        # 3. Economy Class Seats
        if flight.economy_seats > 0:
            eco_cols = ["A", "B", "C", "D", "E", "F"]
            seats_created = 0
            while seats_created < flight.economy_seats:
                for col in eco_cols:
                    if seats_created >= flight.economy_seats:
                        break
                    seats.append(Seat(
                        flight_id=flight.id,
                        seat_number=f"{current_row}{col}",
                        row=current_row,
                        column=col,
                        seat_class=SeatClass.ECONOMY,
                        status=SeatStatus.AVAILABLE,
                        extra_legroom=(current_row in [current_row + 1, current_row + 2]),
                        is_exit_row=(current_row in [current_row + 1])
                    ))
                    seats_created += 1
                current_row += 1

        seat_map = SeatMap(
            flight_id=flight.id,
            total_rows=current_row,
            layout_config="3-3"
        )
        self.db.add(seat_map)
        await self.seat_repo.create_bulk_seats(seats)

    async def _generate_fares_for_flight(self, flight: Flight) -> None:
        """Create fare records associated with fare rules."""
        rules_res = await self.db.execute(select(FareRule))
        rules = {r.fare_type: r for r in rules_res.scalars().all()}
        
        if FareType.BASIC_ECONOMY not in rules:
            basic_rule = FareRule(
                fare_type=FareType.BASIC_ECONOMY,
                is_refundable=False,
                is_changeable=False,
                cancellation_fee_percent=100,
                change_fee_amount=Decimal("150.00"),
                seat_selection_allowed=False,
                baggage_allowance_kg=20,
                description="Non-refundable. Seat assigned automatically at check-in."
            )
            self.db.add(basic_rule)
            await self.db.flush()
            rules[FareType.BASIC_ECONOMY] = basic_rule

        if FareType.FLEXIBLE not in rules:
            flex_rule = FareRule(
                fare_type=FareType.FLEXIBLE,
                is_refundable=True,
                is_changeable=True,
                cancellation_fee_percent=10,
                change_fee_amount=Decimal("0.00"),
                seat_selection_allowed=True,
                baggage_allowance_kg=35,
                description="Fully refundable within policy window. Free seat selection."
            )
            self.db.add(flex_rule)
            await self.db.flush()
            rules[FareType.FLEXIBLE] = flex_rule

        if flight.economy_seats > 0:
            self.db.add(Fare(
                flight_id=flight.id,
                seat_class=SeatClass.ECONOMY,
                fare_type=FareType.BASIC_ECONOMY,
                fare_rule_id=rules[FareType.BASIC_ECONOMY].id,
                price=flight.base_price_economy,
                currency=flight.currency
            ))
            self.db.add(Fare(
                flight_id=flight.id,
                seat_class=SeatClass.ECONOMY,
                fare_type=FareType.FLEXIBLE,
                fare_rule_id=rules[FareType.FLEXIBLE].id,
                price=flight.base_price_economy * Decimal("1.25"),
                currency=flight.currency
            ))

        if flight.business_class_seats > 0:
            self.db.add(Fare(
                flight_id=flight.id,
                seat_class=SeatClass.BUSINESS,
                fare_type=FareType.FLEXIBLE,
                fare_rule_id=rules[FareType.FLEXIBLE].id,
                price=flight.base_price_business,
                currency=flight.currency
            ))

        if flight.first_class_seats > 0:
            self.db.add(Fare(
                flight_id=flight.id,
                seat_class=SeatClass.FIRST,
                fare_type=FareType.FLEXIBLE,
                fare_rule_id=rules[FareType.FLEXIBLE].id,
                price=flight.base_price_first,
                currency=flight.currency
            ))
        await self.db.flush()

    async def update_flight(self, flight_id: str, data: FlightUpdate, actor_email: str) -> Flight:
        flight = await self.flight_repo.get_by_id(flight_id, for_update=True)
        if not flight:
            raise NotFoundException(f"Flight {flight_id} not found")
        if flight.status == FlightStatus.CANCELLED:
            raise FlightCancelledException("Cannot modify a cancelled flight")

        old_values = {
            "departure_time": str(flight.departure_time),
            "arrival_time": str(flight.arrival_time),
            "origin": flight.origin,
            "destination": flight.destination,
            "status": flight.status.value
        }

        schedule_changed = False
        if data.departure_time and data.departure_time != flight.departure_time:
            schedule_changed = True
            flight.departure_time = data.departure_time
        if data.arrival_time and data.arrival_time != flight.arrival_time:
            schedule_changed = True
            flight.arrival_time = data.arrival_time
        if data.origin:
            flight.origin = data.origin.upper()
        if data.destination:
            flight.destination = data.destination.upper()
        if data.status:
            flight.status = data.status

        # Invariant: Cannot shrink class capacity below already-booked count
        booked_counts_res = await self.db.execute(
            select(Seat.seat_class, func.count(Seat.id))
            .where(and_(Seat.flight_id == flight_id, Seat.status == SeatStatus.BOOKED))
            .group_by(Seat.seat_class)
        )
        booked_map = {row[0]: row[1] for row in booked_counts_res.all()}
        if flight.economy_seats < booked_map.get(SeatClass.ECONOMY, 0):
            raise BadRequestException(f"Cannot reduce Economy capacity below booked count ({booked_map.get(SeatClass.ECONOMY, 0)})")
        if flight.business_class_seats < booked_map.get(SeatClass.BUSINESS, 0):
            raise BadRequestException(f"Cannot reduce Business capacity below booked count ({booked_map.get(SeatClass.BUSINESS, 0)})")
        if flight.first_class_seats < booked_map.get(SeatClass.FIRST, 0):
            raise BadRequestException(f"Cannot reduce First capacity below booked count ({booked_map.get(SeatClass.FIRST, 0)})")

        if schedule_changed:
            bookings_res = await self.db.execute(
                select(Booking).where(
                    and_(Booking.flight_id == flight_id, Booking.status == BookingStatus.CONFIRMED)
                )
            )
            affected_bookings = list(bookings_res.scalars().all())
            
            sched_change = ScheduleChange(
                flight_id=flight.id,
                old_departure_time=datetime.fromisoformat(old_values["departure_time"]),
                new_departure_time=flight.departure_time,
                old_arrival_time=datetime.fromisoformat(old_values["arrival_time"]),
                new_arrival_time=flight.arrival_time,
                old_origin=old_values["origin"],
                new_origin=flight.origin,
                old_destination=old_values["destination"],
                new_destination=flight.destination,
                reason=data.reason or "Operational schedule adjustment",
                affected_bookings_count=len(affected_bookings)
            )
            self.db.add(sched_change)

        await self.flight_repo.update(flight)

        await self.audit_repo.create_log(
            action="FLIGHT_UPDATED",
            entity_type="Flight",
            entity_id=flight.id,
            actor_email=actor_email,
            old_values=old_values,
            new_values=data.model_dump(mode="json", exclude_none=True),
            source=AuditSource.ADMIN
        )

        return flight

    async def cancel_flight(self, flight_id: str, reason: str, actor_email: str) -> Flight:
        flight = await self.flight_repo.get_by_id(flight_id, for_update=True)
        if not flight:
            raise NotFoundException(f"Flight {flight_id} not found")
        if flight.status == FlightStatus.CANCELLED:
            raise BadRequestException("Flight is already cancelled")

        old_status = flight.status.value
        flight.status = FlightStatus.CANCELLED
        await self.flight_repo.update(flight)

        await self.audit_repo.create_log(
            action="FLIGHT_CANCELLED",
            entity_type="Flight",
            entity_id=flight.id,
            actor_email=actor_email,
            old_values={"status": old_status},
            new_values={"status": FlightStatus.CANCELLED.value, "cancellation_reason": reason},
            source=AuditSource.ADMIN
        )

        # Trigger n8n Automation Webhook
        try:
            from app.utils.n8n_client import trigger_n8n_webhook
            import asyncio
            asyncio.create_task(trigger_n8n_webhook(
                event_type="FLIGHT_CANCELLED",
                data={
                    "flight_id": flight.id,
                    "flight_number": flight.flight_number,
                    "origin": flight.origin,
                    "destination": flight.destination,
                    "reason": reason,
                    "customer_email": "customer@flightsystem.com",
                    "message": f"Flight {flight.flight_number} ({flight.origin} -> {flight.destination}) has been CANCELLED: {reason}"
                }
            ))
        except Exception:
            pass

        return flight
