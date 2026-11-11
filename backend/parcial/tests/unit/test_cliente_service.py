from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
import pytest

from parcial.app.core.paginacion import PaginationParams
from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules import models  # noqa: F401
from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.clientes.schemas import ClienteCreateRequest, ClienteUpdateRequest
from parcial.app.modules.clientes.service import ClienteService


@pytest.mark.asyncio
async def test_crear_cliente_exitoso() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    uow = UnitOfWork(session)
    service = ClienteService()

    datos = ClienteCreateRequest(nombre="Lucía", email="lucia@example.com")
    mock_repo = AsyncMock()
    mock_repo.obtener_por_email.return_value = None

    async def fake_add(c: Cliente) -> Cliente:
        c.id = 1
        return c

    mock_repo.add.side_effect = fake_add

    res = await service.crear_cliente(datos, uow, repo=mock_repo)
    assert res.id == 1
    assert res.nombre == "Lucía"
    assert res.email == "lucia@example.com"


@pytest.mark.asyncio
async def test_crear_cliente_conflicto_email() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    uow = UnitOfWork(session)
    service = ClienteService()

    datos = ClienteCreateRequest(nombre="Lucía", email="lucia@example.com")
    mock_repo = AsyncMock()
    mock_repo.obtener_por_email.return_value = Cliente(id=9, nombre="Otra", email="lucia@example.com")

    with pytest.raises(HTTPException) as exc_info:
        await service.crear_cliente(datos, uow, repo=mock_repo)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_obtener_cliente_no_encontrado() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    uow = UnitOfWork(session)
    service = ClienteService()

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await service.obtener_cliente_por_id(999, uow, repo=mock_repo)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_actualizar_cliente_parcial() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    uow = UnitOfWork(session)
    service = ClienteService()

    cliente = Cliente(id=1, nombre="Original", email="orig@example.com", telefono="111")
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = cliente

    datos = ClienteUpdateRequest(telefono="222")
    res = await service.actualizar_cliente(1, datos, uow, repo=mock_repo)
    assert res.telefono == "222"
    assert res.nombre == "Original"


@pytest.mark.asyncio
async def test_vincular_perfil_exitoso() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    uow = UnitOfWork(session)
    service = ClienteService()

    cliente = Cliente(id=1, nombre="Lucía", email="l@a.com", usuario_id=None)
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = cliente
    mock_repo.obtener_por_usuario_id.return_value = None

    res = await service.vincular_perfil(1, usuario_id=10, uow=uow, repo=mock_repo)
    assert res.usuario_id == 10


@pytest.mark.asyncio
async def test_vincular_perfil_conflicto_si_ya_asignado() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    uow = UnitOfWork(session)
    service = ClienteService()

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = Cliente(id=1, nombre="Lucía", email="l@a.com", usuario_id=5)

    with pytest.raises(HTTPException) as exc_info:
        await service.vincular_perfil(1, usuario_id=10, uow=uow, repo=mock_repo)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_listar_clientes_paginado() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    uow = UnitOfWork(session)
    service = ClienteService()

    mock_repo = AsyncMock()
    mock_repo.contar_total.return_value = 1
    mock_repo.listar_paginado.return_value = [
        Cliente(id=1, nombre="Lucía", email="l@a.com")
    ]

    res = await service.listar_clientes_paginado(PaginationParams(page=1, size=20), uow, repo=mock_repo)
    assert res.total == 1
    assert len(res.items) == 1
