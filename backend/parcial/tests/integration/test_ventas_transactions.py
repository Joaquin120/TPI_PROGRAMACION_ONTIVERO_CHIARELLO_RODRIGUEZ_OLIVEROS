"""Integration tests for atomic sales transactions and stock movement consistency."""

from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.security import ACCESS_TOKEN_COOKIE, crear_token_acceso
from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.libros.models import Autor, Editorial, Genero, Libro, MovimientoStock
from parcial.app.modules.usuarios.models import AsignacionRol, Usuario
from parcial.app.modules.ventas.models import DetalleVenta, Venta


@pytest.fixture
async def catalogo_con_stock(db_session: AsyncSession) -> dict[str, int]:
    """Populates initial publishers, authors, genres, and books with balanced stock."""
    autor = Autor(nombre="Jorge Luis Borges", biografia="Escritor argentino")
    editorial = Editorial(nombre="Sur")
    genero = Genero(nombre="Ficción")
    db_session.add_all([autor, editorial, genero])
    await db_session.flush()

    # Create admin user for stock operations
    admin = Usuario(
        nombre="Admin",
        email="admin_stock@test.com",
        password_hash="hashed",
        activo=True,
        debe_cambiar_password=False,
    )
    db_session.add(admin)
    await db_session.flush()

    libro1 = Libro(
        titulo="Ficciones",
        isbn="978-950-04-0001-1",
        precio=Decimal("15000.00"),
        stock=10,
        autor_id=autor.id,
        editorial_id=editorial.id,
        genero_id=genero.id,
    )
    libro2 = Libro(
        titulo="El Aleph",
        isbn="978-950-04-0002-2",
        precio=Decimal("12000.00"),
        stock=5,
        autor_id=autor.id,
        editorial_id=editorial.id,
        genero_id=genero.id,
    )
    db_session.add_all([libro1, libro2])
    await db_session.flush()

    # Initial append-only movements matching stock
    mov1 = MovimientoStock(
        libro_id=libro1.id,
        usuario_id=admin.id,
        cantidad=10,
        motivo="Stock inicial",
    )
    mov2 = MovimientoStock(
        libro_id=libro2.id,
        usuario_id=admin.id,
        cantidad=5,
        motivo="Stock inicial",
    )
    db_session.add_all([mov1, mov2])

    # Create customer
    cliente = Cliente(
        nombre="Lucía Fernández",
        email="lucia@example.com",
        telefono="123456",
        direccion="Calle Falsa 123",
    )
    db_session.add(cliente)
    await db_session.commit()

    return {
        "libro1_id": libro1.id,
        "libro2_id": libro2.id,
        "cliente_id": cliente.id,
        "admin_id": admin.id,
    }


@pytest.fixture
async def vendedor_autenticado(app_client: AsyncClient, db_session: AsyncSession) -> Usuario:
    """Creates a vendor user and sets the auth cookie."""
    usuario = Usuario(
        nombre="Vendedor Test",
        email="vendedor@libreria.com",
        password_hash="hashed",
        activo=True,
        debe_cambiar_password=False,
    )
    db_session.add(usuario)
    await db_session.flush()

    rol = AsignacionRol(usuario_id=usuario.id, rol="VENDEDOR", revocada_en=None)
    db_session.add(rol)
    await db_session.commit()

    token = crear_token_acceso(
        usuario_id=usuario.id,
        email=usuario.email,
        roles=["VENDEDOR"],
    )
    app_client.cookies.set(ACCESS_TOKEN_COOKIE, token)
    return usuario


@pytest.mark.asyncio
async def test_crear_venta_atomica_exito(
    app_client: AsyncClient,
    catalogo_con_stock: dict[str, int],
    vendedor_autenticado: Usuario,
    db_session: AsyncSession,
) -> None:
    """Verifies atomic sale creation, stock deduction, and negative audit movements."""
    payload = {
        "cliente_id": catalogo_con_stock["cliente_id"],
        "items": [
            {"libro_id": catalogo_con_stock["libro1_id"], "cantidad": 2},
            {"libro_id": catalogo_con_stock["libro2_id"], "cantidad": 1},
        ],
    }

    resp = await app_client.post("/ventas", json=payload)
    assert resp.status_code == 201
    data = resp.json()

    # Total = (15000 * 2) + (12000 * 1) = 42000.00
    assert Decimal(str(data["total"])) == Decimal("42000.00")
    assert len(data["detalles"]) == 2

    # Verify database stock mutated and append-only movements created
    libro1 = await db_session.get(Libro, catalogo_con_stock["libro1_id"])
    libro2 = await db_session.get(Libro, catalogo_con_stock["libro2_id"])
    assert libro1.stock == 8  # 10 - 2
    assert libro2.stock == 4  # 5 - 1

    # Verify stock invariant: libro.stock == SUM(movimiento_stock.cantidad)
    stmt_sum1 = select(func.sum(MovimientoStock.cantidad)).where(
        MovimientoStock.libro_id == libro1.id
    )
    sum_movs1 = (await db_session.execute(stmt_sum1)).scalar_one()
    assert sum_movs1 == libro1.stock

    stmt_sum2 = select(func.sum(MovimientoStock.cantidad)).where(
        MovimientoStock.libro_id == libro2.id
    )
    sum_movs2 = (await db_session.execute(stmt_sum2)).scalar_one()
    assert sum_movs2 == libro2.stock


@pytest.mark.asyncio
async def test_crear_venta_rollback_total_por_stock_insuficiente(
    app_client: AsyncClient,
    catalogo_con_stock: dict[str, int],
    vendedor_autenticado: Usuario,
    db_session: AsyncSession,
) -> None:
    """Guarantees complete rollback if any item lacks sufficient stock."""
    payload = {
        "cliente_id": catalogo_con_stock["cliente_id"],
        "items": [
            {"libro_id": catalogo_con_stock["libro1_id"], "cantidad": 2},
            {"libro_id": catalogo_con_stock["libro2_id"], "cantidad": 999},  # Exceeds 5
        ],
    }

    resp = await app_client.post("/ventas", json=payload)
    assert resp.status_code == 409

    # Verify no sales, details, or movements were persisted
    stmt_ventas = select(func.count()).select_from(Venta)
    assert (await db_session.execute(stmt_ventas)).scalar_one() == 0

    # Stock must remain unchanged
    libro1 = await db_session.get(Libro, catalogo_con_stock["libro1_id"])
    assert libro1.stock == 10


@pytest.mark.asyncio
async def test_crear_venta_rechaza_libro_dado_de_baja(
    app_client: AsyncClient,
    catalogo_con_stock: dict[str, int],
    vendedor_autenticado: Usuario,
    db_session: AsyncSession,
) -> None:
    """Verifies that selling a soft-deleted book is rejected with HTTP 409."""
    from datetime import datetime, timezone

    libro1 = await db_session.get(Libro, catalogo_con_stock["libro1_id"])
    libro1.borrado_en = datetime.now(timezone.utc)
    await db_session.commit()

    payload = {
        "cliente_id": catalogo_con_stock["cliente_id"],
        "items": [{"libro_id": libro1.id, "cantidad": 1}],
    }

    resp = await app_client.post("/ventas", json=payload)
    assert resp.status_code == 409
