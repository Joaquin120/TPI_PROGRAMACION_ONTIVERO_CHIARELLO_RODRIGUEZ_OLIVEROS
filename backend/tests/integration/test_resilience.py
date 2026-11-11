import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
from sqlalchemy.exc import OperationalError, SQLAlchemyError


@pytest.mark.asyncio
async def test_readiness_operational_failure(client: httpx.AsyncClient) -> None:
    """Verifies GET /health/ready returns 503 Service Unavailable when DB throws operational errors."""
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = OperationalError("connection failure", None, Exception("Connection closed"))

    mock_connect_cm = AsyncMock()
    mock_connect_cm.__aenter__.return_value = mock_conn
    mock_connect_cm.__aexit__.return_value = None

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_connect_cm

    with patch("src.api.v1.endpoints.health.engine", mock_engine):
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] in ("disconnected", "timeout")


@pytest.mark.asyncio
async def test_readiness_sqlalchemy_error(client: httpx.AsyncClient) -> None:
    """Verifies GET /health/ready returns 503 on generic SQLAlchemyError."""
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError("Database driver fatal error")

    mock_connect_cm = AsyncMock()
    mock_connect_cm.__aenter__.return_value = mock_conn
    mock_connect_cm.__aexit__.return_value = None

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_connect_cm

    with patch("src.api.v1.endpoints.health.engine", mock_engine):
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] in ("disconnected", "timeout")


@pytest.mark.asyncio
async def test_readiness_query_timeout(client: httpx.AsyncClient) -> None:
    """Verifies GET /health/ready returns 503 when DB ping exceeds DB_TIMEOUT threshold."""
    async def hang_query(*args: object, **kwargs: object) -> None:
        await asyncio.sleep(5.0)

    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = hang_query

    mock_connect_cm = AsyncMock()
    mock_connect_cm.__aenter__.return_value = mock_conn
    mock_connect_cm.__aexit__.return_value = None

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_connect_cm

    with patch("src.api.v1.endpoints.health.engine", mock_engine), \
         patch("src.api.v1.endpoints.health.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.DB_TIMEOUT = 0.05
        mock_get_settings.return_value = mock_settings

        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] in ("disconnected", "timeout")


@pytest.mark.asyncio
async def test_readiness_recovery_after_fault(client: httpx.AsyncClient) -> None:
    """Verifies system recovers and returns 200 OK once the database connection is restored."""
    mock_conn = AsyncMock()
    # First call fails, second call succeeds
    mock_conn.execute.side_effect = [
        OperationalError("temporary network partition", None, Exception()),
        MagicMock(),
    ]

    mock_connect_cm = AsyncMock()
    mock_connect_cm.__aenter__.return_value = mock_conn
    mock_connect_cm.__aexit__.return_value = None

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_connect_cm

    with patch("src.api.v1.endpoints.health.engine", mock_engine):
        # 1. Fault state
        res_fail = await client.get("/health/ready")
        assert res_fail.status_code == 503
        assert res_fail.json()["status"] == "unhealthy"

        # 2. Restored state
        res_ok = await client.get("/health/ready")
        assert res_ok.status_code == 200
        assert res_ok.json()["status"] == "ready"
        assert res_ok.json()["database"] == "connected"
