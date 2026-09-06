import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, delete
from app.database.session import AsyncSessionLocal, engine
from app.models import (
    User, Role, Flight, Aircraft, SeatMap, Seat, SeatHold,
    FareRule, Fare, Booking, BookingPassenger, BookingSeat,
    Waitlist, Refund, TravelCredit, ScheduleChange,
    Notification, PriceAlert, FraudScore, RagApproval,
    AuditLog, IdempotencyKey, AutomationJob, ReconciliationLog
)
from app.auth.jwt import get_password_hash
from app.utils.enums import UserRole, FareType
from decimal import Decimal

async def clean_dummy_data():
    print("[CLEAN] Starting fast database clean...")
    async with AsyncSessionLocal() as db:
        # 1. Clear operational tables
        for model in [
            ReconciliationLog, AutomationJob, IdempotencyKey,
            RagApproval, FraudScore, PriceAlert, Notification,
            ScheduleChange, TravelCredit, Refund, Waitlist,
            BookingSeat, BookingPassenger, Booking,
            SeatHold, Seat, SeatMap, Fare, Flight, Aircraft,
            AuditLog
        ]:
            try:
                await db.execute(delete(model))
            except Exception as e:
                print(f"Warning deleting {model.__name__}: {e}")

        # Delete non-admin users
        await db.execute(delete(User).where(User.email != "admin@flightsystem.com"))
        await db.commit()
        print("[CLEAN] Operational data and extra users deleted.")

        # 2. Ensure Roles
        roles_map = {}
        for role_enum in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_AGENT, UserRole.CUSTOMER]:
            res = await db.execute(select(Role).where(Role.name == role_enum))
            role = res.scalar_one_or_none()
            if not role:
                role = Role(name=role_enum, description=f"{role_enum.value} system role")
                db.add(role)
                await db.flush()
            roles_map[role_enum] = role

        # 3. Ensure 1 Single Admin
        res_admin = await db.execute(select(User).where(User.email == "admin@flightsystem.com"))
        admin = res_admin.scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin@flightsystem.com",
                hashed_password=get_password_hash("Admin@123456"),
                first_name="System",
                last_name="Admin",
                phone="+1-800-555-0100",
                role_id=roles_map[UserRole.SUPER_ADMIN].id,
                loyalty_tier="PLATINUM",
                is_active=True
            )
            db.add(admin)
        else:
            admin.role_id = roles_map[UserRole.SUPER_ADMIN].id
            admin.hashed_password = get_password_hash("Admin@123456")
            admin.is_active = True

        # 4. Ensure Standard Fare Rules
        basic_res = await db.execute(select(FareRule).where(FareRule.fare_type == FareType.BASIC_ECONOMY))
        if not basic_res.scalar_one_or_none():
            db.add(FareRule(
                fare_type=FareType.BASIC_ECONOMY,
                is_refundable=False,
                is_changeable=False,
                cancellation_fee_percent=100,
                change_fee_amount=Decimal("150.00"),
                seat_selection_allowed=False,
                baggage_allowance_kg=20,
                description="Non-refundable. Seat assigned automatically at check-in."
            ))
        
        flex_res = await db.execute(select(FareRule).where(FareRule.fare_type == FareType.FLEXIBLE))
        if not flex_res.scalar_one_or_none():
            db.add(FareRule(
                fare_type=FareType.FLEXIBLE,
                is_refundable=True,
                is_changeable=True,
                cancellation_fee_percent=10,
                change_fee_amount=Decimal("0.00"),
                seat_selection_allowed=True,
                baggage_allowance_kg=35,
                description="Refundable with 10% fee. Free seat selection and date changes."
            ))

        await db.commit()
        print("[CLEAN] SUCCESS: Database is 100% clean. Only 1 Admin exists: admin@flightsystem.com")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clean_dummy_data())
