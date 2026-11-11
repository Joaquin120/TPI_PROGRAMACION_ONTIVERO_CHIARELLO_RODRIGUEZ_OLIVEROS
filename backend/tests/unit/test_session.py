from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db


@pytest.mark.asyncio
async def test_get_db_yields_session_and_closes() -> None:
    """Verifies get_db yields an AsyncSession and ensures session is closed."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.close = AsyncMock()

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None

    mock_session_factory = MagicMock(return_value=mock_cm)

    with patch("src.db.session.async_session_factory", mock_session_factory):
        generator = get_db()
        session = await anext(generator)
        assert session == mock_session

        with pytest.raises(StopAsyncIteration):
            await anext(generator)

        mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_db_closes_session_on_exception() -> None:
    """Verifies get_db closes session even when an exception is raised in caller."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.close = AsyncMock()

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None

    mock_session_factory = MagicMock(return_value=mock_cm)

    with patch("src.db.session.async_session_factory", mock_session_factory):
        generator = get_db()
        session = await anext(generator)
        assert session == mock_session

        with pytest.raises(RuntimeError, match="Simulated consumer error"):
            await generator.athrow(RuntimeError("Simulated consumer error"))

        mock_session.close.assert_awaited_once()
