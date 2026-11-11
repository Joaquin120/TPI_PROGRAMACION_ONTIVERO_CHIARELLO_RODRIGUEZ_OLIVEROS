from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.modules import models  # noqa: F401
from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.clientes.repository import ClienteRepository


@pytest.mark.asyncio
async def test_cliente_repository_add_calls_flush() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = ClienteRepository(session)
    cliente = Cliente(nombre="Lucía", email="lucia@example.com")

    added = await repo.add(cliente)
    assert added is cliente
    session.add.assert_called_once_with(cliente)
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_cliente_repository_obtener_por_email() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = ClienteRepository(session)

    mock_result = MagicMock()
    mock_cliente = Cliente(id=1, nombre="Lucía", email="lucia@example.com")
    mock_result.scalar_one_or_none.return_value = mock_cliente
    session.execute.return_value = mock_result

    res = await repo.obtener_por_email("lucia@example.com")
    assert res == mock_cliente
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_cliente_repository_obtener_por_usuario_id() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = ClienteRepository(session)

    mock_result = MagicMock()
    mock_cliente = Cliente(id=1, nombre="Lucía", email="lucia@example.com", usuario_id=10)
    mock_result.scalar_one_or_none.return_value = mock_cliente
    session.execute.return_value = mock_result

    res = await repo.obtener_por_usuario_id(10)
    assert res == mock_cliente
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_cliente_repository_listar_paginado() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = ClienteRepository(session)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Cliente(id=1, nombre="A", email="a@example.com"),
        Cliente(id=2, nombre="B", email="b@example.com"),
    ]
    session.execute.return_value = mock_result

    items = await repo.listar_paginado(skip=0, limit=2)
    assert len(items) == 2
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_cliente_repository_contar_total() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = ClienteRepository(session)

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 42
    session.execute.return_value = mock_result

    total = await repo.contar_total()
    assert total == 42
    session.execute.assert_awaited_once()
