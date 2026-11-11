from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from parcial.app.core.config import get_settings


def create_engine(
    database_url: str | None = None,
    echo: bool | None = None,
    pool_size: int | None = None,
    max_overflow: int | None = None,
) -> AsyncEngine:
    """Creates an AsyncEngine with the specified or settings configuration."""
    settings = get_settings()
    return create_async_engine(
        database_url or settings.DATABASE_URL,
        echo=echo if echo is not None else settings.DB_ECHO,
        pool_size=pool_size if pool_size is not None else settings.DB_POOL_SIZE,
        max_overflow=max_overflow if max_overflow is not None else settings.DB_MAX_OVERFLOW,
    )


def create_session_factory(bind_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Creates an async_sessionmaker for the specified AsyncEngine."""
    return async_sessionmaker(
        bind=bind_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


# Engine and session factory singletons
engine: AsyncEngine = create_engine()
async_session_factory: async_sessionmaker[AsyncSession] = create_session_factory(engine)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator yielding an isolated AsyncSession and closing it on exit."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Dependency exposing the configured session factory.

    Used by flows that must commit outside the request transaction (for
    example, persisting a failed login attempt), and overridable in tests.
    """
    return async_session_factory
