from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config.settings import settings
import ssl

# Clean url for asyncpg
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Configure connect_args for asyncpg (Neon PgBouncer requires statement_cache_size=0)
connect_args = {
    "statement_cache_size": 0,
}

if "neon.tech" in db_url or "ssl=require" in db_url:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context
    db_url = db_url.split("?")[0]

# Create async engine with robust connection pooling
engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=5,
    pool_recycle=300,
    pool_pre_ping=False,
    connect_args=connect_args
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
