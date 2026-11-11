import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.base import Base, POSTGRES_NAMING_CONVENTION
from parcial.app.core.database import (
    create_engine,
    create_session_factory,
    get_session,
)


class DummyModel(Base):
    __tablename__ = "dummy"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)


def test_base_metadata_naming_conventions() -> None:
    """Verifies that Base uses explicit PostgreSQL naming convention."""
    assert Base.metadata.naming_convention == POSTGRES_NAMING_CONVENTION
    table = DummyModel.__table__
    assert table.primary_key.name == "pk_dummy"


def test_engine_and_factory_creation() -> None:
    """Verifies engine and factory creation with custom configuration."""
    eng = create_engine(
        database_url="postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
        echo=False,
        pool_size=10,
        max_overflow=5,
    )
    factory = create_session_factory(eng)
    assert eng.url.render_as_string(hide_password=False) == "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
    assert factory.kw["expire_on_commit"] is False
    assert factory.class_ is AsyncSession


@pytest.mark.asyncio
async def test_get_session_yields_session_and_closes() -> None:
    """Verifies get_session yields an AsyncSession and ensures session is closed."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.close = AsyncMock()

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None

    mock_session_factory = MagicMock(return_value=mock_cm)

    with patch("parcial.app.core.database.async_session_factory", mock_session_factory):
        generator = get_session()
        session = await anext(generator)
        assert session == mock_session

        with pytest.raises(StopAsyncIteration):
            await anext(generator)

        mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_closes_on_exception() -> None:
    """Verifies get_session closes session even when an exception is raised in caller."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.close = AsyncMock()

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None

    mock_session_factory = MagicMock(return_value=mock_cm)

    with patch("parcial.app.core.database.async_session_factory", mock_session_factory):
        generator = get_session()
        session = await anext(generator)
        assert session == mock_session

        with pytest.raises(RuntimeError, match="Caller error"):
            await generator.athrow(RuntimeError("Caller error"))

        mock_session.close.assert_awaited_once()
