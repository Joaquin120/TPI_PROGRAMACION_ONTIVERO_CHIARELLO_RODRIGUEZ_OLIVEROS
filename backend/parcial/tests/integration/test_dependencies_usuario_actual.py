from datetime import datetime, timedelta, timezone

import jwt
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.core.config import get_settings
from parcial.app.modules.usuarios.models import Usuario

PASSWORD = "secreto-seguro"
EMAIL = "ana@example.com"


async def _registrar_y_loguear(client: AsyncClient) -> None:
    registro = await client.post(
        "/auth/registro",
        json={"email": EMAIL, "nombre": "Ana", "password": PASSWORD},
    )
    assert registro.status_code == 201
    login = await client.post(
        "/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert login.status_code == 200


def _token(payload: dict[str, object]) -> str:
    settings = get_settings()
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def test_cookie_valida_resuelve_el_usuario_autenticado(
    app_client: AsyncClient,
) -> None:
    await _registrar_y_loguear(app_client)

    respuesta = await app_client.get("/auth/yo")

    assert respuesta.status_code == 200
    assert respuesta.json()["usuario"]["email"] == EMAIL


async def test_token_ilegible_responde_401(app_client: AsyncClient) -> None:
    app_client.cookies.set("access_token", "esto-no-es-un-jwt")

    respuesta = await app_client.get("/auth/yo")

    assert respuesta.status_code == 401


async def test_token_expirado_responde_401(app_client: AsyncClient) -> None:
    ahora = datetime.now(timezone.utc)
    token = _token(
        {
            "sub": "1",
            "email": EMAIL,
            "roles": ["CLIENTE"],
            "iat": ahora - timedelta(hours=2),
            "exp": ahora - timedelta(hours=1),
        }
    )
    app_client.cookies.set("access_token", token)

    respuesta = await app_client.get("/auth/yo")

    assert respuesta.status_code == 401


async def test_token_de_usuario_inexistente_responde_401(
    app_client: AsyncClient,
) -> None:
    ahora = datetime.now(timezone.utc)
    token = _token(
        {
            "sub": "9999",
            "email": "fantasma@example.com",
            "roles": ["CLIENTE"],
            "iat": ahora,
            "exp": ahora + timedelta(hours=1),
        }
    )
    app_client.cookies.set("access_token", token)

    respuesta = await app_client.get("/auth/yo")

    assert respuesta.status_code == 401


async def test_usuario_desactivado_con_token_vigente_responde_401(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _registrar_y_loguear(app_client)

    async with db_sessionmaker() as session:
        await session.execute(
            update(Usuario).where(Usuario.email == EMAIL).values(activo=False)
        )
        await session.commit()

    respuesta = await app_client.get("/auth/yo")

    assert respuesta.status_code == 401
