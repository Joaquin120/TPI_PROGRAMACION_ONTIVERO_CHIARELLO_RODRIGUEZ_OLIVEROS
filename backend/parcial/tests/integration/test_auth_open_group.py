from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.main import open_router, protected_router
from parcial.app.modules.usuarios.models import Usuario

PASSWORD = "secreto-seguro"
NUEVA_PASSWORD = "nueva-clave-segura"
EMAIL = "ana@example.com"

AUTH_PATHS = {
    "/auth/registro",
    "/auth/login",
    "/auth/logout",
    "/auth/yo",
    "/auth/cambiar-password",
}


def _paths(router: object) -> set[str]:
    """Collects paths recursively; newer FastAPI wraps included routers."""
    paths: set[str] = set()
    for route in getattr(router, "routes", []):
        path = getattr(route, "path", None)
        if path is not None:
            paths.add(path)
        original = getattr(route, "original_router", None)
        if original is not None:
            paths |= _paths(original)
    return paths


def test_router_de_auth_esta_montado_en_el_grupo_abierto_y_no_en_el_protegido() -> None:
    rutas_abiertas = _paths(open_router)
    rutas_protegidas = _paths(protected_router)

    assert AUTH_PATHS <= rutas_abiertas
    assert not AUTH_PATHS & rutas_protegidas


async def test_endpoints_de_auth_son_alcanzables_sin_el_gate_de_cambio_de_password(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    registro = await app_client.post(
        "/auth/registro",
        json={"email": EMAIL, "nombre": "Ana", "password": PASSWORD},
    )
    assert registro.status_code == 201

    async with db_sessionmaker() as session:
        await session.execute(
            update(Usuario)
            .where(Usuario.email == EMAIL)
            .values(debe_cambiar_password=True)
        )
        await session.commit()

    login = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert login.status_code == 200

    # The pending flag blocks the protected group, never the open auth group.
    yo = await app_client.get("/auth/yo")
    assert yo.status_code == 200
    assert yo.json()["usuario"]["debe_cambiar_password"] is True

    cambio = await app_client.post(
        "/auth/cambiar-password",
        json={"password_actual": PASSWORD, "password_nueva": NUEVA_PASSWORD},
    )
    assert cambio.status_code == 200

    logout = await app_client.post("/auth/logout")
    assert logout.status_code == 204
