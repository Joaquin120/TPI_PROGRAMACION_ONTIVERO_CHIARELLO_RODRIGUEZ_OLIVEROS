import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest


@pytest.mark.asyncio
async def test_liveness_probes_healthy(client: httpx.AsyncClient) -> None:
    """Verifies GET /health and /health/live immediately return 200 OK with status healthy."""
    endpoints = ["/health", "/health/live", "/api/v1/health", "/api/v1/health/live"]
    for path in endpoints:
        response = await client.get(path)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "environment" in data


@pytest.mark.asyncio
async def test_readiness_probe_success(client: httpx.AsyncClient) -> None:
    """Verifies GET /health/ready returns 200 OK when database ping succeeds."""
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = MagicMock()

    mock_connect_cm = AsyncMock()
    mock_connect_cm.__aenter__.return_value = mock_conn
    mock_connect_cm.__aexit__.return_value = None

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_connect_cm

    with patch("src.api.v1.endpoints.health.engine", mock_engine):
        for path in ["/health/ready", "/api/v1/health/ready"]:
            response = await client.get(path)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_readiness_probe_database_error(client: httpx.AsyncClient) -> None:
    """Verifies GET /health/ready returns 503 Service Unavailable when database ping fails."""
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = ConnectionRefusedError("Connection refused")

    mock_connect_cm = AsyncMock()
    mock_connect_cm.__aenter__.return_value = mock_conn
    mock_connect_cm.__aexit__.return_value = None

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_connect_cm

    with patch("src.api.v1.endpoints.health.engine", mock_engine):
        for path in ["/health/ready", "/api/v1/health/ready"]:
            response = await client.get(path)
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"


@pytest.mark.asyncio
async def test_readiness_probe_timeout(client: httpx.AsyncClient) -> None:
    """Verifies GET /health/ready returns 503 Service Unavailable on timeout."""
    async def slow_execute(*args: object, **kwargs: object) -> None:
        await asyncio.sleep(10)

    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = slow_execute

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
        assert data["database"] == "disconnected"
