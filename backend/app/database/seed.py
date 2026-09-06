import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select
from app.database.session import AsyncSessionLocal, engine
from app.database.base import Base
from app.models.user import User, Role
from app.models.flight import Flight
from app.models.seat import Seat, SeatMap
from app.models.fare import Fare, FareRule
from app.models.policy import PolicyDocument
from app.auth.jwt import get_password_hash
from app.utils.enums import UserRole, FlightStatus, SeatClass, SeatStatus, FareType, OverbookingPolicy

async def seed_database():
    print("[SEED] Starting Neon PostgreSQL Database Initialization...")
    
    # 1. Create all 25 tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[SEED] Database tables created / verified.")

    async with AsyncSessionLocal() as db:
        # 2. Seed Roles
        roles_map = {}
        for role_enum in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_AGENT, UserRole.CUSTOMER]:
            res = await db.execute(select(Role).where(Role.name == role_enum))
            role = res.scalar_one_or_none()
            if not role:
                role = Role(name=role_enum, description=f"{role_enum.value} system role")
                db.add(role)
                await db.flush()
            roles_map[role_enum] = role
        print("[SEED] Roles seeded: SUPER_ADMIN, OPERATIONS_AGENT, CUSTOMER.")

        # 3. Seed Users
        # 1 Single Admin
        admin_res = await db.execute(select(User).where(User.email == "admin@flightsystem.com"))
        if not admin_res.scalar_one_or_none():
            admin_user = User(
                email="admin@flightsystem.com",
                hashed_password=get_password_hash("Admin@123456"),
                first_name="System",
                last_name="Admin",
                phone="+1-800-555-0100",
                role_id=roles_map[UserRole.SUPER_ADMIN].id,
                loyalty_tier="PLATINUM",
                is_active=True
            )
            db.add(admin_user)

        # Demo Customer
        cust_res = await db.execute(select(User).where(User.email == "customer@flightsystem.com"))
        if not cust_res.scalar_one_or_none():
            cust_user = User(
                email="customer@flightsystem.com",
                hashed_password=get_password_hash("Customer@123456"),
                first_name="Ali",
                last_name="Khan",
                phone="+92-300-1234567",
                role_id=roles_map[UserRole.CUSTOMER].id,
                loyalty_tier="SILVER",
                is_active=True
            )
            db.add(cust_user)
        print("[SEED] Users seeded: admin@flightsystem.com, customer@flightsystem.com.")

        # 4. Seed Fare Rules
        fare_rules = {}
        basic_res = await db.execute(select(FareRule).where(FareRule.fare_type == FareType.BASIC_ECONOMY))
        basic_rule = basic_res.scalar_one_or_none()
        if not basic_rule:
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
            db.add(basic_rule)
            await db.flush()
        fare_rules[FareType.BASIC_ECONOMY] = basic_rule

        flex_res = await db.execute(select(FareRule).where(FareRule.fare_type == FareType.FLEXIBLE))
        flex_rule = flex_res.scalar_one_or_none()
        if not flex_rule:
            flex_rule = FareRule(
                fare_type=FareType.FLEXIBLE,
                is_refundable=True,
                is_changeable=True,
                cancellation_fee_percent=10,
                change_fee_amount=Decimal("0.00"),
                seat_selection_allowed=True,
                baggage_allowance_kg=35,
                description="Refundable with 10% fee. Free seat selection and date changes."
            )
            db.add(flex_rule)
            await db.flush()
        fare_rules[FareType.FLEXIBLE] = flex_rule

        # 5. Seed Sample Flights (UK -> Dubai, LHE -> DXB, DXB -> LHR)
        now = datetime.now(timezone.utc)
        sample_flights = [
            {
                "flight_number": "BA-105",
                "origin": "LHR",
                "origin_name": "London Heathrow Airport",
                "destination": "DXB",
                "destination_name": "Dubai International Airport",
                "departure_time": now + timedelta(days=2, hours=5),
                "arrival_time": now + timedelta(days=2, hours=12),
                "capacity": 100,
                "first": 20,
                "biz": 30,
                "eco": 50,
                "p_eco": Decimal("450.00"),
                "p_biz": Decimal("1200.00"),
                "p_first": Decimal("2400.00")
            },
            {
                "flight_number": "PK-301",
                "origin": "LHE",
                "origin_name": "Lahore Allama Iqbal Intl",
                "destination": "DXB",
                "destination_name": "Dubai International Airport",
                "departure_time": now + timedelta(days=1, hours=3),
                "arrival_time": now + timedelta(days=1, hours=6, minutes=30),
                "capacity": 100,
                "first": 20,
                "biz": 30,
                "eco": 50,
                "p_eco": Decimal("280.00"),
                "p_biz": Decimal("750.00"),
                "p_first": Decimal("1500.00")
            },
            {
                "flight_number": "EK-202",
                "origin": "DXB",
                "origin_name": "Dubai International Airport",
                "destination": "JFK",
                "destination_name": "New York JFK Airport",
                "departure_time": now + timedelta(days=3, hours=8),
                "arrival_time": now + timedelta(days=3, hours=22),
                "capacity": 100,
                "first": 20,
                "biz": 30,
                "eco": 50,
                "p_eco": Decimal("650.00"),
                "p_biz": Decimal("1800.00"),
                "p_first": Decimal("3500.00")
            }
        ]

        for sf in sample_flights:
            f_res = await db.execute(select(Flight).where(Flight.flight_number == sf["flight_number"]))
            flight = f_res.scalar_one_or_none()
            if not flight:
                flight = Flight(
                    flight_number=sf["flight_number"],
                    origin=sf["origin"],
                    origin_name=sf["origin_name"],
                    destination=sf["destination"],
                    destination_name=sf["destination_name"],
                    departure_time=sf["departure_time"],
                    arrival_time=sf["arrival_time"],
                    aircraft_capacity=sf["capacity"],
                    first_class_seats=sf["first"],
                    business_class_seats=sf["biz"],
                    economy_seats=sf["eco"],
                    base_price_economy=sf["p_eco"],
                    base_price_business=sf["p_biz"],
                    base_price_first=sf["p_first"],
                    currency="USD",
                    status=FlightStatus.SCHEDULED,
                    overbooking_policy=OverbookingPolicy.HARD_NEVER_OVERSELL
                )
                db.add(flight)
                await db.flush()

                # Generate Seat Layout (100 seats)
                seats = []
                row = 1
                # First Class (20 seats: 5 rows x 4 cols A,B,C,D)
                for _ in range(5):
                    for col in ["A", "B", "C", "D"]:
                        seats.append(Seat(
                            flight_id=flight.id,
                            seat_number=f"{row}{col}",
                            row=row,
                            column=col,
                            seat_class=SeatClass.FIRST,
                            status=SeatStatus.AVAILABLE,
                            extra_legroom=True
                        ))
                    row += 1
                # Business Class (30 seats: 5 rows x 6 cols A,B,C,D,E,F)
                for _ in range(5):
                    for col in ["A", "B", "C", "D", "E", "F"]:
                        seats.append(Seat(
                            flight_id=flight.id,
                            seat_number=f"{row}{col}",
                            row=row,
                            column=col,
                            seat_class=SeatClass.BUSINESS,
                            status=SeatStatus.AVAILABLE,
                            extra_legroom=True
                        ))
                    row += 1
                # Economy Class (50 seats)
                eco_count = 0
                while eco_count < 50:
                    for col in ["A", "B", "C", "D", "E", "F"]:
                        if eco_count >= 50:
                            break
                        seats.append(Seat(
                            flight_id=flight.id,
                            seat_number=f"{row}{col}",
                            row=row,
                            column=col,
                            seat_class=SeatClass.ECONOMY,
                            status=SeatStatus.AVAILABLE,
                            extra_legroom=(row == 11),
                            is_exit_row=(row == 11)
                        ))
                        eco_count += 1
                    row += 1

                db.add_all(seats)
                db.add(SeatMap(flight_id=flight.id, total_rows=row, layout_config="3-3"))

                # Add Fares
                db.add(Fare(
                    flight_id=flight.id,
                    seat_class=SeatClass.ECONOMY,
                    fare_type=FareType.BASIC_ECONOMY,
                    fare_rule_id=fare_rules[FareType.BASIC_ECONOMY].id,
                    price=sf["p_eco"],
                    currency="USD"
                ))
                db.add(Fare(
                    flight_id=flight.id,
                    seat_class=SeatClass.ECONOMY,
                    fare_type=FareType.FLEXIBLE,
                    fare_rule_id=fare_rules[FareType.FLEXIBLE].id,
                    price=sf["p_eco"] * Decimal("1.25"),
                    currency="USD"
                ))
                db.add(Fare(
                    flight_id=flight.id,
                    seat_class=SeatClass.BUSINESS,
                    fare_type=FareType.FLEXIBLE,
                    fare_rule_id=fare_rules[FareType.FLEXIBLE].id,
                    price=sf["p_biz"],
                    currency="USD"
                ))
                db.add(Fare(
                    flight_id=flight.id,
                    seat_class=SeatClass.FIRST,
                    fare_type=FareType.FLEXIBLE,
                    fare_rule_id=fare_rules[FareType.FLEXIBLE].id,
                    price=sf["p_first"],
                    currency="USD"
                ))

        await db.commit()
        print("[SEED] Sample Flights & Seat Maps seeded successfully!")

    await engine.dispose()
    print("[SEED] Neon Database is 100% ready and populated!")

if __name__ == "__main__":
    asyncio.run(seed_database())
