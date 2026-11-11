"""Integration tests for dynamic sales authorization and customer profile linking."""

from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.security import ACCESS_TOKEN_COOKIE, crear_token_acceso
from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.libros.models import Autor, Editorial, Genero, Libro, MovimientoStock
from parcial.app.modules.usuarios.models import AsignacionRol, Usuario
from parcial.app.modules.ventas.models import DetalleVenta, Venta


@pytest.fixture
async def setup_ventas_permisos(db_session: AsyncSession) -> dict[str, int]:
    """Sets up users with different roles, customer profiles, and a sample sale."""
    # 1. Staff users
    admin = Usuario(
        nombre="Admin User",
        email="admin_perm@test.com",
        password_hash="h",
        activo=True,
        debe_cambiar_password=False,
    )
    vendedor = Usuario(
        nombre="Vendedor User",
        email="vendedor_perm@test.com",
        password_hash="h",
        activo=True,
        debe_cambiar_password=False,
    )
    # 2. Customer user (owner)
    cliente_user = Usuario(
        nombre="Ana Paz",
        email="ana_perm@test.com",
        password_hash="h",
        activo=True,
        debe_cambiar_password=False,
    )
    # 3. Foreign customer user
    ajeno_user = Usuario(
        nombre="Juan Ajeno",
        email="ajeno_perm@test.com",
        password_hash="h",
        activo=True,
        debe_cambiar_password=False,
    )
    db_session.add_all([admin, vendedor, cliente_user, ajeno_user])
    await db_session.flush()

    # Assign roles
    db_session.add_all([
        AsignacionRol(usuario_id=admin.id, rol="ADMIN", revocada_en=None),
        AsignacionRol(usuario_id=vendedor.id, rol="VENDEDOR", revocada_en=None),
        AsignacionRol(usuario_id=cliente_user.id, rol="CLIENTE", revocada_en=None),
        AsignacionRol(usuario_id=ajeno_user.id, rol="CLIENTE", revocada_en=None),
    ])

    # Customer profile linked to cliente_user
    cliente = Cliente(
        nombre="Ana Paz",
        email="ana_perm@test.com",
        usuario_id=cliente_user.id,
    )
    db_session.add(cliente)
    await db_session.flush()

    # Catalog & sale
    autor = Autor(nombre="Borges")
    editorial = Editorial(nombre="Sur")
    genero = Genero(nombre="Ficción")
    db_session.add_all([autor, editorial, genero])
    await db_session.flush()

    libro = Libro(
        titulo="Ficciones",
        isbn="978-000-00-1111-1",
        precio=Decimal("10000.00"),
        stock=10,
        autor_id=autor.id,
        editorial_id=editorial.id,
        genero_id=genero.id,
    )
    db_session.add(libro)
    await db_session.flush()

    venta = Venta(
        cliente_id=cliente.id,
        usuario_id=vendedor.id,
        total=Decimal("10000.00"),
    )
    db_session.add(venta)
    await db_session.flush()

    detalle = DetalleVenta(
        venta_id=venta.id,
        libro_id=libro.id,
        cantidad=1,
        precio_unitario=Decimal("10000.00"),
    )
    db_session.add(detalle)
    await db_session.commit()

    return {
        "admin_id": admin.id,
        "admin_email": admin.email,
        "vendedor_id": vendedor.id,
        "vendedor_email": vendedor.email,
        "cliente_user_id": cliente_user.id,
        "cliente_email": cliente_user.email,
        "ajeno_user_id": ajeno_user.id,
        "ajeno_email": ajeno_user.email,
        "venta_id": venta.id,
        "cliente_id": cliente.id,
    }


def _autenticar(client: AsyncClient, user_id: int, email: str, rol: str) -> None:
    token = crear_token_acceso(usuario_id=user_id, email=email, roles=[rol])
    client.cookies.set(ACCESS_TOKEN_COOKIE, token)


@pytest.mark.asyncio
async def test_get_venta_permisos_matrix(
    app_client: AsyncClient,
    setup_ventas_permisos: dict[str, int],
) -> None:
    """Verifies that GET /ventas/{id} permits staff and owner, but denies foreign customers."""
    s = setup_ventas_permisos
    venta_id = s["venta_id"]

    # 1. Unauthenticated -> 401
    resp = await app_client.get(f"/ventas/{venta_id}")
    assert resp.status_code == 401

    # 2. Staff: ADMIN -> 200
    _autenticar(app_client, s["admin_id"], s["admin_email"], "ADMIN")
    resp = await app_client.get(f"/ventas/{venta_id}")
    assert resp.status_code == 200

    # 3. Staff: VENDEDOR -> 200
    _autenticar(app_client, s["vendedor_id"], s["vendedor_email"], "VENDEDOR")
    resp = await app_client.get(f"/ventas/{venta_id}")
    assert resp.status_code == 200

    # 4. Owner: CLIENTE dueño -> 200
    _autenticar(app_client, s["cliente_user_id"], s["cliente_email"], "CLIENTE")
    resp = await app_client.get(f"/ventas/{venta_id}")
    assert resp.status_code == 200

    # 5. Foreign: CLIENTE ajeno -> 403 Forbidden
    _autenticar(app_client, s["ajeno_user_id"], s["ajeno_email"], "CLIENTE")
    resp = await app_client.get(f"/ventas/{venta_id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_mis_ventas_endpoint(
    app_client: AsyncClient,
    setup_ventas_permisos: dict[str, int],
) -> None:
    """Verifies that GET /mis-ventas returns purchase history for the logged-in customer."""
    s = setup_ventas_permisos

    # Owner gets their sales
    _autenticar(app_client, s["cliente_user_id"], s["cliente_email"], "CLIENTE")
    resp = await app_client.get("/mis-ventas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == s["venta_id"]

    # Foreign customer with no linked profile gets 404
    _autenticar(app_client, s["ajeno_user_id"], s["ajeno_email"], "CLIENTE")
    resp = await app_client.get("/mis-ventas")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_vincular_perfil_cliente(
    app_client: AsyncClient,
    setup_ventas_permisos: dict[str, int],
    db_session: AsyncSession,
) -> None:
    """Tests binding a user account to an unassigned customer profile."""
    s = setup_ventas_permisos

    # Create an unassigned customer profile
    cliente_libre = Cliente(
        nombre="Tomás Sin Usuario",
        email="tomas@test.com",
    )
    db_session.add(cliente_libre)
    await db_session.commit()

    # Authenticate as ajeno_user (who has no customer profile yet)
    _autenticar(app_client, s["ajeno_user_id"], s["ajeno_email"], "CLIENTE")
    resp = await app_client.post(f"/clientes/{cliente_libre.id}/perfil")
    assert resp.status_code == 200
    assert resp.json()["usuario_id"] == s["ajeno_user_id"]

    # Binding again -> 409 Conflict
    resp_again = await app_client.post(f"/clientes/{cliente_libre.id}/perfil")
    assert resp_again.status_code == 409
