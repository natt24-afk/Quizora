from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# 1. Create the asynchronous engine connected to MariaDB via asyncmy
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,  # Logs generated SQL queries when debugging
    pool_pre_ping=True,       # Ensures connection is still alive before using it
)

# 2. Asynchronous session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# 3. FastAPI Dependency Injection for async DB sessions
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an AsyncSession per request and ensures it is safely closed.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()