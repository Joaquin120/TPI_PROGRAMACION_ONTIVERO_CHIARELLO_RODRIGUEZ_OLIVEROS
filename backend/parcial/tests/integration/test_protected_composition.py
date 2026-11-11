"""Composition tests: the centralized gate must cover the real admin routes.

This complements the per-endpoint contract tests. It asserts the *wiring*:
administration endpoints are mounted inside the protected group, so they
inherit both the identity dependency (401 without a session) and the
``debe_cambiar_password`` gate (403 when pending) on top of their own
ADMIN check.
"""

from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.main import open_router, protected_router
from parcial.app.modules.usuarios.models import Usuario
from parcial.tests.integration.helpers import PASSWORD_TEMPORAL, crear_admin

ADMIN_ENDPOINTS = {"/usuarios"}


def _paths(router: object) -> set[str]:
    """Collects paths recursively; FastAPI wraps included routers."""
    paths: set[str] = set()
    for route in getattr(router, "routes", []):
        path = getattr(route, "path", None)
        if path is not None:
            paths.add(path)
        original = getattr(route, "original_router", None)
        if original is not None:
            paths |= _paths(original)
    return paths


def _payload() -> dict[str, str]:
    return {
        "email": "nuevo@example.com",
        "nombre": "Nuevo",
        "password": PASSWORD_TEMPORAL,
        "rol": "VENDEDOR",
    }


def test_rutas_de_administracion_cuelgan_del_grupo_protegido() -> None:
    rutas_protegidas = _paths(protected_router)
    rutas_abiertas = _paths(open_router)

    assert ADMIN_ENDPOINTS <= rutas_protegidas
    assert not ADMIN_ENDPOINTS & rutas_abiertas


async def test_endpoint_admin_real_exige_sesion(app_client: AsyncClient) -> None:
    respuesta = await app_client.post("/usuarios", json=_payload())

    assert respuesta.status_code == 401


async def test_gate_central_bloquea_a_un_admin_con_cambio_pendiente(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)

    async with db_sessionmaker() as session:
        await session.execute(
            update(Usuario)
            .where(Usuario.email == "admin@example.com")
            .values(debe_cambiar_password=True)
        )
        await session.commit()

    respuesta = await app_client.post("/usuarios", json=_payload())

    # The pending flag is evaluated before the ADMIN role requirement.
    assert respuesta.status_code == 403


async def test_endpoint_admin_real_alcanzable_con_admin_sin_pendiente(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)

    respuesta = await app_client.post("/usuarios", json=_payload())

    assert respuesta.status_code == 201
    assert respuesta.json()["email"] == "nuevo@example.com"
