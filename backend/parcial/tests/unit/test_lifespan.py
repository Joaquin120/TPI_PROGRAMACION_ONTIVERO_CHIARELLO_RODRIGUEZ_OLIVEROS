from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from parcial.app.core.dependencies import get_usuario_actual
from parcial.app.main import app, lifespan


def _usar_usuario(usuario: object):
    """Temporarily overrides the identity dependency for a protected-group test."""
    app.dependency_overrides[get_usuario_actual] = lambda: usuario
    return usuario


@pytest.mark.asyncio
async def test_lifespan_initializes_state_and_disposes() -> None:
    """Verifies that lifespan sets up fictitious password hash, engine, and cleans up."""
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()

    with patch("parcial.app.main.engine", mock_engine):
        async with lifespan(app):
            assert hasattr(app.state, "fictitious_password_hash")
            assert app.state.fictitious_password_hash.startswith("$2b$")
            assert hasattr(app.state, "engine")
            assert hasattr(app.state, "sessionmaker")
            mock_engine.dispose.assert_not_called()

        mock_engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_open_route_group_health_live() -> None:
    """Verifies that open route group handles /health/live with 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_protected_route_group_requires_session() -> None:
    """Verifies protected route group rejects requests without a session cookie."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/protected/ping")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_group_allows_normal_user() -> None:
    """Verifies protected route group allows access when debe_cambiar_password is False."""
    _usar_usuario(SimpleNamespace(activo=True, debe_cambiar_password=False))
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/protected/ping")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
    finally:
        app.dependency_overrides.pop(get_usuario_actual, None)


@pytest.mark.asyncio
async def test_protected_route_group_blocks_when_must_change_password() -> None:
    """Verifies protected route group returns 403 Forbidden when debe_cambiar_password is True."""
    _usar_usuario(SimpleNamespace(activo=True, debe_cambiar_password=True))
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/protected/ping")
            assert response.status_code == 403
            assert "Debe cambiar su contraseña" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_usuario_actual, None)
