from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import FastAPI

from src.core.lifespan import lifespan


@pytest.mark.asyncio
async def test_lifespan_startup_and_shutdown_success() -> None:
    """Verifies lifespan executes startup ping and engine dispose on shutdown."""
    app = FastAPI()

    mock_conn = AsyncMock()
    mock_conn.execute.return_value = MagicMock()

    mock_connect_cm = AsyncMock()
    mock_connect_cm.__aenter__.return_value = mock_conn
    mock_connect_cm.__aexit__.return_value = None

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_connect_cm
    mock_engine.dispose = AsyncMock()

    with patch("src.core.lifespan.engine", mock_engine):
        async with lifespan(app):
            mock_engine.connect.assert_called_once()
            mock_conn.execute.assert_awaited_once()

        mock_engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_startup_failure_raises_exception() -> None:
    """Verifies that database connection failure during startup raises an exception."""
    app = FastAPI()

    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = ConnectionRefusedError("Database unreachable")

    mock_connect_cm = AsyncMock()
    mock_connect_cm.__aenter__.return_value = mock_conn
    mock_connect_cm.__aexit__.return_value = None

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_connect_cm
    mock_engine.dispose = AsyncMock()

    with patch("src.core.lifespan.engine", mock_engine):
        with pytest.raises(ConnectionRefusedError, match="Database unreachable"):
            async with lifespan(app):
                pass

        mock_engine.dispose.assert_not_called()
