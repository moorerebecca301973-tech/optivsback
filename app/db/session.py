# app/db/session.py
# This file handles the async database session creation.
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Create an async engine for Supabase PostgreSQL
# 'asyncpg' is the recommended driver for async operations with PostgreSQL
engine = create_async_engine(
    str(settings.DATABASE_URL),  # Convert PostgresDsn to string
    echo=False,  # Set to True for SQL query logging (useful for development)
    future=True,  # Use SQLAlchemy 2.0 style APIs
)

# Create a configured "Session" class
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Important for async
    autoflush=False
)

# Dependency to get a database session
async def get_db() -> AsyncSession:
    """
    Async dependency that yields a database session.
    This will be used in our API route dependencies.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()