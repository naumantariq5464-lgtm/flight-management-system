import sys
import os

# Ensure root directory is on Python path for rag module imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config.settings import settings
from app.database.base import Base
from app.database.session import engine, AsyncSessionLocal
from app.models.user import User, Role
from app.models import *  # Ensure all models are registered
from app.auth.jwt import get_password_hash
from app.utils.enums import UserRole
from app.utils.exceptions import AppBaseException

# Import Routers
from app.routers.auth import router as auth_router
from app.routers.admin.flights import router as admin_flights_router
from app.routers.admin.bookings import router as admin_bookings_router
from app.routers.admin.refunds import router as admin_refunds_router
from app.routers.admin.waitlist import router as admin_waitlist_router
from app.routers.admin.reports import router as admin_reports_router
from app.routers.admin.fraud import router as admin_fraud_router
from app.routers.admin.rag import router as admin_rag_router
from app.routers.admin.audit import router as admin_audit_router
from app.routers.admin.users import router as admin_users_router

from app.routers.customer.flights import router as customer_flights_router
from app.routers.customer.bookings import router as customer_bookings_router
from app.routers.customer.waitlist import router as customer_waitlist_router
from app.routers.customer.notifications import router as customer_notifications_router
from app.routers.customer.rag import router as customer_rag_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FlightSystem")

async def init_db_and_seed():
    """Create tables if not existing and seed default admin user."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Seed default roles
        from sqlalchemy import select
        for role_enum in [UserRole.SUPER_ADMIN, UserRole.OPERATIONS_AGENT, UserRole.CUSTOMER]:
            res = await db.execute(select(Role).where(Role.name == role_enum))
            if not res.scalar_one_or_none():
                db.add(Role(name=role_enum, description=f"{role_enum.value} system role"))
        await db.commit()

        # Seed super admin user if not exists
        admin_res = await db.execute(select(User).where(User.email == "admin@flightsystem.com"))
        if not admin_res.scalar_one_or_none():
            role_res = await db.execute(select(Role).where(Role.name == UserRole.SUPER_ADMIN))
            super_role = role_res.scalar_one()
            admin_user = User(
                email="admin@flightsystem.com",
                hashed_password=get_password_hash("Admin@123456"),
                first_name="Super",
                last_name="Admin",
                phone="+1-800-555-0199",
                role_id=super_role.id,
                loyalty_tier="PLATINUM",
                is_active=True
            )
            db.add(admin_user)
            await db.commit()
            logger.info("Default super-admin seeded: admin@flightsystem.com / Admin@123456")

def init_rag_chroma_vectors():
    """Auto-embed and persist policy documents into ChromaDB upon server start."""
    try:
        from rag.ingestion import run_ingestion
        res = run_ingestion()
        logger.info(f"[RAG ChromaDB] Auto-ingestion completed: {res.get('total_vectors', 0)} chunks vectorized.")
    except Exception as e:
        logger.warning(f"[RAG ChromaDB] Ingestion skipped or encountered notice: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Flight Management System Backend...")
    try:
        await init_db_and_seed()
    except Exception as e:
        logger.warning(f"DB auto-initialization skipped or failed (if using Neon migrations): {e}")

    # Auto-initialize ChromaDB vector store
    init_rag_chroma_vectors()

    yield
    logger.info("Shutting down Flight Management System Backend...")
    await engine.dispose()

app = FastAPI(
    title="Flight Management System API",
    description="Production-grade Flight Management System backend with Neon DB, Concurrency Row-Locking, and n8n Coordination",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handler
@app.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Flight Management System API",
        "environment": settings.ENVIRONMENT
    }

# Mount Auth
app.include_router(auth_router)

# Mount Admin Routers
app.include_router(admin_flights_router)
app.include_router(admin_bookings_router)
app.include_router(admin_refunds_router)
app.include_router(admin_waitlist_router)
app.include_router(admin_reports_router)
app.include_router(admin_fraud_router)
app.include_router(admin_rag_router)
app.include_router(admin_audit_router)
app.include_router(admin_users_router)

# Mount Customer Routers
app.include_router(customer_flights_router)
app.include_router(customer_bookings_router)
app.include_router(customer_waitlist_router)
app.include_router(customer_notifications_router)
app.include_router(customer_rag_router)
