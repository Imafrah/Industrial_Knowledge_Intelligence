"""
Database configuration — async SQLAlchemy engine + session factory.
On startup: creates all tables and enables the pgvector extension.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://indstry:indstry_pass@localhost:5432/indstry"
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def init_db():
    """Create the pgvector extension and all tables."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Import models so they register with Base.metadata
        from app import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency that yields a DB session and cleans up after."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
