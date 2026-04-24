# core/database.py
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from core.config import settings

logger = logging.getLogger(__name__)

if not settings.async_database_url:
    raise ValueError(
        "NEON_DATABASE_URL is missing. Check the Windows WSLENV bridge.")

# Create the async engine
engine = create_async_engine(
    settings.async_database_url,
    echo=False,           # Set to True if you need to debug SQL queries
    future=True,
    pool_size=10,         # Enterprise-grade connection pooling
    max_overflow=20
)


async def init_db():
    """Initialize the database schema in Neon Postgres."""
    try:
        async with engine.begin() as conn:
            # Note: For production, we'll use Alembic.
            # For this epic, we'll sync models directly.
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("✅ Database schema synchronized with Neon Postgres.")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def get_session() -> AsyncSession:
    """Dependency for injecting DB sessions into FastAPI routes."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
