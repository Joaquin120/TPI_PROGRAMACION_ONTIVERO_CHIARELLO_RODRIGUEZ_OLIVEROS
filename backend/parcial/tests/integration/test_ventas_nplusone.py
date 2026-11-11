"""Integration test proving that GET /ventas/{id} executes a fixed number of SQL queries (anti N+1)."""

from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from parcial.app.core.security import ACCESS_TOKEN_COOKIE, crear_token_acceso
from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.libros.models import Autor, Editorial, Genero, Libro
from parcial.app.modules.usuarios.models import AsignacionRol, Usuario
from parcial.app.modules.ventas.models import DetalleVenta, Venta


@pytest.fixture
async def setup_ventas_variable_renglones(db_session: AsyncSession) -> dict[str, int]:
    """Creates a vendor, customer, books, and two sales (one with 1 line, one with 5 lines)."""
    # Vendor & Customer
    vendedor = Usuario(
        nombre="Vendedor N1",
        email="vendedor_n1@test.com",
        password_hash="h",
        activo=True,
        debe_cambiar_password=False,
    )
    db_session.add(vendedor)
    await db_session.flush()

    db_session.add(AsignacionRol(usuario_id=vendedor.id, rol="VENDEDOR", revocada_en=None))

    cliente = Cliente(nombre="Cliente N1", email="cliente_n1@test.com")
    autor = Autor(nombre="Autor N1")
    editorial = Editorial(nombre="Editorial N1")
    genero = Genero(nombre="Genero N1")
    db_session.add_all([cliente, autor, editorial, genero])
    await db_session.flush()

    # Create 5 distinct books
    libros: list[Libro] = []
    for i in range(1, 6):
        libro = Libro(
            titulo=f"Libro {i}",
            isbn=f"978-000-00-000{i}-0",
            precio=Decimal("1000.00"),
            stock=10,
            autor_id=autor.id,
            editorial_id=editorial.id,
            genero_id=genero.id,
        )
        libros.append(libro)
        db_session.add(libro)
    await db_session.flush()

    # Sale 1: only 1 line item
    venta1 = Venta(cliente_id=cliente.id, usuario_id=vendedor.id, total=Decimal("1000.00"))
    db_session.add(venta1)
    await db_session.flush()
    db_session.add(
        DetalleVenta(
            venta_id=venta1.id,
            libro_id=libros[0].id,
            cantidad=1,
            precio_unitario=Decimal("1000.00"),
        )
    )

    # Sale 2: 5 line items
    venta2 = Venta(cliente_id=cliente.id, usuario_id=vendedor.id, total=Decimal("5000.00"))
    db_session.add(venta2)
    await db_session.flush()
    for libro in libros:
        db_session.add(
            DetalleVenta(
                venta_id=venta2.id,
                libro_id=libro.id,
                cantidad=1,
                precio_unitario=Decimal("1000.00"),
            )
        )

    await db_session.commit()

    return {
        "vendedor_id": vendedor.id,
        "vendedor_email": vendedor.email,
        "venta_1_id": venta1.id,
        "venta_5_id": venta2.id,
    }


@pytest.mark.asyncio
async def test_detalle_venta_sin_n_plus_one(
    app_client: AsyncClient,
    setup_ventas_variable_renglones: dict[str, int],
    db_engine: AsyncEngine,
) -> None:
    """Proves query count is strictly invariant to the number of line items."""
    s = setup_ventas_variable_renglones
    token = crear_token_acceso(usuario_id=s["vendedor_id"], email=s["vendedor_email"], roles=["VENDEDOR"])
    app_client.cookies.set(ACCESS_TOKEN_COOKIE, token)

    query_counter = 0

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_counter
        # Count only SELECT queries
        raw = statement.strip().upper()
        if raw.startswith("SELECT"):
            query_counter += 1

    # Listen on sync engine
    event.listen(db_engine.sync_engine, "before_cursor_execute", before_cursor_execute)

    try:
        # Request sale with 1 item
        query_counter = 0
        resp1 = await app_client.get(f"/ventas/{s['venta_1_id']}")
        assert resp1.status_code == 200
        queries_venta_1 = query_counter

        # Request sale with 5 items
        query_counter = 0
        resp2 = await app_client.get(f"/ventas/{s['venta_5_id']}")
        assert resp2.status_code == 200
        queries_venta_5 = query_counter

        # The number of SELECT queries MUST be constant (O(1)) and NOT scale with item count
        assert queries_venta_1 == queries_venta_5, (
            f"Queries count differs: 1 item took {queries_venta_1} queries, "
            f"5 items took {queries_venta_5} queries (N+1 query problem detected!)"
        )
    finally:
        event.remove(db_engine.sync_engine, "before_cursor_execute", before_cursor_execute)
