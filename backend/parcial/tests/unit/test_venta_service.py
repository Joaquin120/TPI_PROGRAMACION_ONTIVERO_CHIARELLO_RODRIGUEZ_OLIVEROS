from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
import pytest

from parcial.app.core.paginacion import PaginationParams
from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules import models  # noqa: F401
from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.libros.models import Libro
from parcial.app.modules.usuarios.models import AsignacionRol, Usuario
from parcial.app.modules.ventas.models import DetalleVenta, Venta
from parcial.app.modules.ventas.schemas import VentaCreateRequest, VentaItemRequest
from parcial.app.modules.ventas.service import VentaService


@pytest.mark.asyncio
async def test_crear_venta_exitosa_y_descuento_stock() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    uow = UnitOfWork(session)
    service = VentaService()

    mock_cliente_repo = AsyncMock()
    mock_cliente_repo.get_by_id.return_value = Cliente(id=1, nombre="Lucía", email="lucia@example.com")

    libro = Libro(id=10, titulo="Ficciones", precio=Decimal("15000.00"), stock=5, borrado_en=None)
    mock_libro_repo = AsyncMock()
    mock_libro_repo.get_by_id.return_value = libro

    mock_venta_repo = AsyncMock()

    ahora = datetime.now(timezone.utc)

    async def fake_add(v: Venta) -> Venta:
        v.id = 100
        return v

    mock_venta_repo.add.side_effect = fake_add

    # Simular retorno con detalles y fecha válida
    def make_venta_cargada() -> Venta:
        v = Venta(
            id=100,
            cliente_id=1,
            usuario_id=2,
            total=Decimal("30000.00"),
            fecha=ahora,
        )
        v.detalles = [
            DetalleVenta(
                id=1,
                venta_id=100,
                libro_id=10,
                cantidad=2,
                precio_unitario=Decimal("15000.00"),
                libro=libro,
            )
        ]
        v.cliente = Cliente(id=1, nombre="Lucía", email="lucia@example.com")
        return v

    mock_venta_repo.obtener_por_id_con_detalles.return_value = make_venta_cargada()

    req = VentaCreateRequest(cliente_id=1, items=[VentaItemRequest(libro_id=10, cantidad=2)])
    res = await service.crear_venta(
        req,
        usuario_id=2,
        uow=uow,
        venta_repo=mock_venta_repo,
        cliente_repo=mock_cliente_repo,
        libro_repo=mock_libro_repo,
    )

    assert res.id == 100
    assert res.total == Decimal("30000.00")
    assert res.fecha == ahora
    assert libro.stock == 3  # 5 - 2 = 3
    mock_libro_repo.update.assert_awaited_once_with(libro)


@pytest.mark.asyncio
async def test_crear_venta_rechaza_por_stock_insuficiente() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    uow = UnitOfWork(session)
    service = VentaService()

    mock_cliente_repo = AsyncMock()
    mock_cliente_repo.get_by_id.return_value = Cliente(id=1, nombre="Lucía", email="lucia@example.com")

    libro = Libro(id=10, titulo="Ficciones", precio=Decimal("15000.00"), stock=1, borrado_en=None)
    mock_libro_repo = AsyncMock()
    mock_libro_repo.get_by_id.return_value = libro

    req = VentaCreateRequest(cliente_id=1, items=[VentaItemRequest(libro_id=10, cantidad=2)])
    with pytest.raises(HTTPException) as exc_info:
        await service.crear_venta(
            req,
            usuario_id=2,
            uow=uow,
            cliente_repo=mock_cliente_repo,
            libro_repo=mock_libro_repo,
        )

    assert exc_info.value.status_code == 409
    assert libro.stock == 1  # No se alteró


@pytest.mark.asyncio
async def test_crear_venta_rechaza_libro_dado_de_baja() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    uow = UnitOfWork(session)
    service = VentaService()

    mock_cliente_repo = AsyncMock()
    mock_cliente_repo.get_by_id.return_value = Cliente(id=1, nombre="Lucía", email="l@a.com")

    libro = Libro(
        id=10,
        titulo="Borrado",
        precio=Decimal("1000.00"),
        stock=10,
        borrado_en=datetime.now(timezone.utc),
    )
    mock_libro_repo = AsyncMock()
    mock_libro_repo.get_by_id.return_value = libro

    req = VentaCreateRequest(cliente_id=1, items=[VentaItemRequest(libro_id=10, cantidad=1)])
    with pytest.raises(HTTPException) as exc_info:
        await service.crear_venta(
            req,
            usuario_id=2,
            uow=uow,
            cliente_repo=mock_cliente_repo,
            libro_repo=mock_libro_repo,
        )

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_obtener_venta_permisos_personal_y_titular() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    uow = UnitOfWork(session)
    service = VentaService()

    ahora = datetime.now(timezone.utc)
    mock_venta = Venta(
        id=10,
        cliente_id=1,
        usuario_id=2,
        total=Decimal("5000.00"),
        fecha=ahora,
    )
    mock_venta.cliente = Cliente(id=1, nombre="Ana", email="ana@example.com", usuario_id=42)
    mock_venta.detalles = []

    mock_venta_repo = AsyncMock()
    mock_venta_repo.obtener_por_id_con_detalles.return_value = mock_venta

    # 1. Personal (ADMIN) accede exitosamente
    admin = Usuario(id=1, email="admin@test.com", nombre="Admin")
    admin.roles = [AsignacionRol(usuario_id=1, rol="ADMIN", revocada_en=None, vence_en=None)]
    res = await service.obtener_venta_por_id(10, admin, uow, venta_repo=mock_venta_repo)
    assert res.id == 10
    assert res.fecha == ahora

    # 2. Cliente dueño (usuario_id == 42) accede exitosamente
    titular = Usuario(id=42, email="ana@example.com", nombre="Ana")
    titular.roles = [AsignacionRol(usuario_id=42, rol="CLIENTE", revocada_en=None, vence_en=None)]
    res = await service.obtener_venta_por_id(10, titular, uow, venta_repo=mock_venta_repo)
    assert res.id == 10

    # 3. Cliente ajeno (usuario_id == 99) recibe HTTP 403 Forbidden
    ajeno = Usuario(id=99, email="ajeno@example.com", nombre="Ajeno")
    ajeno.roles = [AsignacionRol(usuario_id=99, rol="CLIENTE", revocada_en=None, vence_en=None)]
    with pytest.raises(HTTPException) as exc_info:
        await service.obtener_venta_por_id(10, ajeno, uow, venta_repo=mock_venta_repo)
    assert exc_info.value.status_code == 403
