import asyncio
from decimal import Decimal
from app.database.session import AsyncSessionLocal, engine
from app.database.base import Base
from app.models.user import User, Role
from app.models.fare import FareRule
from app.auth.jwt import get_password_hash
from app.utils.enums import UserRole, FareType

async def reset_clean_db():
    print("[DB RESET] Dropping and recreating all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("[DB RESET] All tables freshly created.")

    async with AsyncSessionLocal() as db:
        # 1. Seed Roles
        roles_map = {}
        for role_enum in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_AGENT, UserRole.CUSTOMER]:
            role = Role(name=role_enum, description=f"{role_enum.value} system role")
            db.add(role)
            await db.flush()
            roles_map[role_enum] = role
        print("[DB RESET] Roles created: SUPER_ADMIN, OPERATIONS_AGENT, CUSTOMER.")

        # 2. Seed ONLY 1 SINGLE ADMIN
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
        print("[DB RESET] 1 Single Admin created: admin@flightsystem.com / Admin@123456")

        # 3. Seed Fare Rules (needed so newly created flights can generate tickets)
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

        await db.commit()
        print("[DB RESET] Database reset complete! Clean state ready for real-time testing.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_clean_db())
