from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.modules import models  # noqa: F401
from parcial.app.modules.ventas.models import Venta
from parcial.app.modules.ventas.repository import VentaRepository


@pytest.mark.asyncio
async def test_venta_repository_add_calls_flush() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = VentaRepository(session)
    venta = Venta(cliente_id=1, usuario_id=2, total=Decimal("1000.00"))

    added = await repo.add(venta)
    assert added is venta
    session.add.assert_called_once_with(venta)
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_venta_repository_obtener_por_id_con_detalles() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = VentaRepository(session)

    mock_result = MagicMock()
    mock_venta = Venta(id=10, cliente_id=1, usuario_id=2, total=Decimal("2000.00"))
    mock_result.scalar_one_or_none.return_value = mock_venta
    session.execute.return_value = mock_result

    res = await repo.obtener_por_id_con_detalles(10)
    assert res == mock_venta
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_venta_repository_listar_paginado() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = VentaRepository(session)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Venta(id=1, cliente_id=1, usuario_id=2, total=Decimal("500.00")),
        Venta(id=2, cliente_id=2, usuario_id=2, total=Decimal("1500.00")),
    ]
    session.execute.return_value = mock_result

    res = await repo.listar_paginado(skip=0, limit=20)
    assert len(res) == 2
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_venta_repository_contar_total() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = VentaRepository(session)

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 15
    session.execute.return_value = mock_result

    assert await repo.contar_total() == 15
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_venta_repository_listar_por_cliente_paginado() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = VentaRepository(session)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Venta(id=1, cliente_id=5, usuario_id=2, total=Decimal("500.00"))
    ]
    session.execute.return_value = mock_result

    res = await repo.listar_por_cliente_paginado(cliente_id=5, skip=0, limit=10)
    assert len(res) == 1
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_venta_repository_contar_por_cliente() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = VentaRepository(session)

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 3
    session.execute.return_value = mock_result

    assert await repo.contar_por_cliente(5) == 3
    session.execute.assert_awaited_once()
