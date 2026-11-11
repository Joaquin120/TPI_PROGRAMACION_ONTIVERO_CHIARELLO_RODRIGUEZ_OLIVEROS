from datetime import datetime, timezone
from collections.abc import AsyncGenerator

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.core.database import get_session
from parcial.app.core.dependencies import get_usuario_actual, requiere_rol
from parcial.app.modules.usuarios.models import AsignacionRol, Usuario

PASSWORD = "secreto-seguro"
EMAIL = "ana@example.com"


@pytest.fixture
async def rol_client(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    """Isolated app exposing routes protected by ``requiere_rol``."""
    app = FastAPI()

    async def _get_session() -> AsyncGenerator[AsyncSession, None]:
        async with db_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session

    @app.get("/solo-admin")
    async def solo_admin(
        usuario: Usuario = Depends(requiere_rol("ADMIN")),
    ) -> dict[str, str]:
        return {"email": usuario.email}

    @app.get("/autenticado")
    async def autenticado(
        usuario: Usuario = Depends(get_usuario_actual),
    ) -> dict[str, str]:
        return {"email": usuario.email}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _crear_usuario_con_roles(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    roles: tuple[str, ...],
) -> None:
    registro = await app_client.post(
        "/auth/registro",
        json={"email": EMAIL, "nombre": "Ana", "password": PASSWORD},
    )
    assert registro.status_code == 201

    async with db_sessionmaker() as session:
        usuario = (
            await session.execute(
                select(Usuario).where(Usuario.email == EMAIL)
            )
        ).scalar_one()
        session.add_all(
            AsignacionRol(usuario_id=usuario.id, rol=rol) for rol in roles
        )
        await session.commit()

    login = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert login.status_code == 200


def _copiar_cookie(origen: AsyncClient, destino: AsyncClient) -> None:
    token = origen.cookies.get("access_token")
    assert token is not None
    destino.cookies.set("access_token", token)


async def test_requiere_rol_sin_sesion_responde_401(rol_client: AsyncClient) -> None:
    respuesta = await rol_client.get("/solo-admin")

    assert respuesta.status_code == 401


async def test_requiere_rol_sin_el_rol_exigido_responde_403(
    app_client: AsyncClient,
    rol_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _crear_usuario_con_roles(app_client, db_sessionmaker, ())
    _copiar_cookie(app_client, rol_client)

    respuesta = await rol_client.get("/solo-admin")

    assert respuesta.status_code == 403


async def test_requiere_rol_con_rol_distinto_responde_403(
    app_client: AsyncClient,
    rol_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _crear_usuario_con_roles(app_client, db_sessionmaker, ("VENDEDOR",))
    _copiar_cookie(app_client, rol_client)

    respuesta = await rol_client.get("/solo-admin")

    assert respuesta.status_code == 403


async def test_requiere_rol_con_el_rol_exigido_permite_el_paso(
    app_client: AsyncClient,
    rol_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _crear_usuario_con_roles(app_client, db_sessionmaker, ("ADMIN",))
    _copiar_cookie(app_client, rol_client)

    respuesta = await rol_client.get("/solo-admin")

    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == EMAIL


async def test_revocacion_del_rol_impacta_en_la_peticion_siguiente(
    app_client: AsyncClient,
    rol_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _crear_usuario_con_roles(app_client, db_sessionmaker, ("ADMIN",))
    _copiar_cookie(app_client, rol_client)

    antes = await rol_client.get("/solo-admin")
    assert antes.status_code == 200

    async with db_sessionmaker() as session:
        await session.execute(
            update(AsignacionRol)
            .where(AsignacionRol.rol == "ADMIN")
            .values(revocada_en=datetime.now(timezone.utc))
        )
        await session.commit()

    despues = await rol_client.get("/solo-admin")

    assert despues.status_code == 403
