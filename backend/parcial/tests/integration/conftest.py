"""PostgreSQL-backed fixtures for integration tests.

The design requires a real PostgreSQL engine: the behaviour under test relies on
partial unique indexes, ``now()`` defaults and ``SELECT ... FOR UPDATE`` locks,
none of which a SQLite fallback can reproduce faithfully.
"""

import os
from collections.abc import AsyncGenerator

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from parcial.app.core.base import Base
from parcial.app.core.database import get_session, get_sessionmaker
from parcial.app.core.security import hash_password
from parcial.app.modules import models  # noqa: F401  (registers every mapped model)

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/parcial_test_db",
)

TRUNCATE_TABLES = (
    "movimiento_stock",
    "evento_seguridad",
    "intento_acceso",
    "asignacion_rol",
    "detalle_venta",
    "venta",
    "cliente",
    "usuario",
    "libro",
    "autor",
    "editorial",
    "genero",
)


async def _asegurar_base_de_datos() -> None:
    """Creates the test database from the maintenance database when missing."""
    url = make_url(TEST_DATABASE_URL)
    admin_dsn = (
        url.set(database="postgres")
        .render_as_string(hide_password=False)
        .replace("postgresql+asyncpg://", "postgresql://")
    )
    connection = await asyncpg.connect(admin_dsn)
    try:
        existe = await connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            url.database,
        )
        if not existe:
            await connection.execute(f'CREATE DATABASE "{url.database}"')
    finally:
        await connection.close()


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Creates the schema for each test and guarantees isolation via truncation."""
    await _asegurar_base_de_datos()
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text(f"TRUNCATE TABLE {', '.join(TRUNCATE_TABLES)} RESTART IDENTITY CASCADE")
        )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Yields a session bound to the test engine for repository-level assertions."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def db_sessionmaker(
    db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Exposes the same factory shape used by the application's isolated sessions."""
    return async_sessionmaker(db_engine, expire_on_commit=False, autoflush=False)


@pytest.fixture
async def app_client(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX client over the real ASGI app with DB dependencies overridden."""
    from parcial.app.main import app

    async def _get_session() -> AsyncGenerator[AsyncSession, None]:
        async with db_sessionmaker() as session:
            yield session

    async def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
        return db_sessionmaker

    app.dependency_overrides[get_session] = _get_session
    app.dependency_overrides[get_sessionmaker] = _get_sessionmaker
    app.state.fictitious_password_hash = await hash_password("clave-ficticia")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
