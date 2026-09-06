import asyncio
import asyncpg
import ssl
import os
import bcrypt
from dotenv import load_dotenv

load_dotenv()

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

async def reset_db():
    print("[RESET] Connecting directly to Neon PostgreSQL...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    raw_url = os.getenv("DATABASE_URL")
    url = raw_url.replace("postgresql+asyncpg://", "postgresql://").split("?")[0]
    
    conn = await asyncpg.connect(url, ssl=ctx)
    
    # 1. Fetch all user tables in public schema
    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
    table_names = [t["table_name"] for t in tables]
    print(f"[RESET] Existing tables ({len(table_names)}): {table_names}")

    # 2. Truncate all tables with CASCADE
    if table_names:
        truncate_sql = f"TRUNCATE TABLE {', '.join(table_names)} CASCADE;"
        await conn.execute(truncate_sql)
        print("[RESET] All tables truncated successfully.")

    # 3. Seed Roles with gen_random_uuid()
    admin_role_id = await conn.fetchval("""
        INSERT INTO roles (id, name, description, created_at, updated_at)
        VALUES (gen_random_uuid(), 'SUPER_ADMIN', 'Super Admin with full access', NOW(), NOW())
        RETURNING id
    """)
    await conn.execute("""
        INSERT INTO roles (id, name, description, created_at, updated_at)
        VALUES 
        (gen_random_uuid(), 'OPERATIONS_AGENT', 'Airport operations agent', NOW(), NOW()),
        (gen_random_uuid(), 'CUSTOMER', 'Standard passenger', NOW(), NOW())
    """)
    print("[RESET] Roles seeded: SUPER_ADMIN, OPERATIONS_AGENT, CUSTOMER.")

    # 4. Seed ONLY 1 SINGLE ADMIN
    admin_hash = get_password_hash("Admin@123456")
    admin_id = await conn.fetchval("""
        INSERT INTO users (
            id, email, hashed_password, first_name, last_name, phone, role_id, loyalty_tier, is_active, created_at, updated_at
        ) VALUES (
            gen_random_uuid(), 'admin@flightsystem.com', $1, 'System', 'Admin', '+1-800-555-0100', $2, 'PLATINUM', TRUE, NOW(), NOW()
        ) RETURNING id
    """, admin_hash, admin_role_id)
    print(f"[RESET] Single Admin seeded: admin@flightsystem.com (ID: {admin_id})")

    # 5. Seed Fare Rules
    await conn.execute("""
        INSERT INTO fare_rules (
            id, fare_type, is_refundable, is_changeable, cancellation_fee_percent, change_fee_amount, seat_selection_allowed, baggage_allowance_kg, description, created_at, updated_at
        ) VALUES 
        (gen_random_uuid(), 'BASIC_ECONOMY', FALSE, FALSE, 100, 150.00, FALSE, 20, 'Non-refundable. Seat assigned automatically at check-in.', NOW(), NOW()),
        (gen_random_uuid(), 'FLEXIBLE', TRUE, TRUE, 10, 0.00, TRUE, 35, 'Refundable with 10% fee. Free seat selection and date changes.', NOW(), NOW())
    """)
    print("[RESET] Standard Fare Rules seeded.")

    # Verify counts
    users_count = await conn.fetchval("SELECT count(*) FROM users")
    flights_count = await conn.fetchval("SELECT count(*) FROM flights")
    bookings_count = await conn.fetchval("SELECT count(*) FROM bookings")
    print(f"[RESET] Verification: Users: {users_count}, Flights: {flights_count}, Bookings: {bookings_count}")
    
    await conn.close()
    print("[RESET] Database is 100% clean and ready!")

if __name__ == "__main__":
    asyncio.run(reset_db())
