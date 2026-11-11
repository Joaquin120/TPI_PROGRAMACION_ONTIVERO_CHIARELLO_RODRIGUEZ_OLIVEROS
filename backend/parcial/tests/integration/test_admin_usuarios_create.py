import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.modules.usuarios.models import AsignacionRol, Usuario
from parcial.tests.integration.helpers import (
    PASSWORD,
    PASSWORD_TEMPORAL,
    crear_admin,
    login,
    registrar,
)


async def test_admin_crea_personal_con_rol_admin(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)

    respuesta = await app_client.post(
        "/usuarios",
        json={
            "email": "nuevo-admin@example.com",
            "nombre": "Nuevo Admin",
            "password": PASSWORD_TEMPORAL,
            "rol": "ADMIN",
        },
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["email"] == "nuevo-admin@example.com"
    assert cuerpo["roles"] == ["ADMIN"]
    assert cuerpo["debe_cambiar_password"] is True
    assert "password_hash" not in respuesta.text

    async with db_sessionmaker() as session:
        usuario = (
            await session.execute(
                select(Usuario).where(Usuario.email == "nuevo-admin@example.com")
            )
        ).scalar_one()
        asignaciones = (
            await session.execute(
                select(AsignacionRol.rol).where(
                    AsignacionRol.usuario_id == usuario.id
                )
            )
        ).scalars().all()

    assert asignaciones == ["ADMIN"]
    assert usuario.activo is True


async def test_admin_crea_vendedor_con_password_temporal_utilizable(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)

    creacion = await app_client.post(
        "/usuarios",
        json={
            "email": "vendedor@example.com",
            "nombre": "Vendedor",
            "password": PASSWORD_TEMPORAL,
            "rol": "VENDEDOR",
        },
    )
    assert creacion.status_code == 201

    app_client.cookies.clear()
    await login(app_client, "vendedor@example.com", password=PASSWORD_TEMPORAL)

    yo = await app_client.get("/auth/yo")
    assert yo.status_code == 200
    assert yo.json()["usuario"]["debe_cambiar_password"] is True
    assert yo.json()["roles_vigentes"] == ["VENDEDOR"]


async def test_creacion_duplicada_responde_409_sin_registros_parciales(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)
    await registrar(app_client, "existente@example.com")

    respuesta = await app_client.post(
        "/usuarios",
        json={
            "email": "existente@example.com",
            "nombre": "Duplicado",
            "password": PASSWORD_TEMPORAL,
            "rol": "VENDEDOR",
        },
    )

    assert respuesta.status_code == 409

    async with db_sessionmaker() as session:
        total = await session.scalar(select(func.count()).select_from(Usuario))
        roles = await session.scalar(
            select(func.count()).select_from(AsignacionRol)
        )

    assert total == 2  # admin + existing customer
    assert roles == 3  # admin: CLIENTE+ADMIN; customer: CLIENTE


@pytest.mark.parametrize(
    "payload",
    [
        {
            "email": "cliente@example.com",
            "nombre": "Cliente",
            "password": PASSWORD_TEMPORAL,
            "rol": "CLIENTE",
        },
        {
            "email": "larga@example.com",
            "nombre": "Larga",
            "password": "a" * 73,
            "rol": "VENDEDOR",
        },
        {
            "email": "extra@example.com",
            "nombre": "Extra",
            "password": PASSWORD_TEMPORAL,
            "rol": "VENDEDOR",
            "activo": False,
        },
    ],
)
async def test_payload_invalido_responde_422_sin_crear_usuario(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    payload: dict[str, object],
) -> None:
    await crear_admin(app_client, db_sessionmaker)

    respuesta = await app_client.post("/usuarios", json=payload)

    assert respuesta.status_code == 422

    async with db_sessionmaker() as session:
        total = await session.scalar(select(func.count()).select_from(Usuario))

    assert total == 1  # only the admin


async def test_usuario_sin_rol_admin_recibe_403(
    app_client: AsyncClient,
) -> None:
    await registrar(app_client, "cliente@example.com")
    await login(app_client, "cliente@example.com")

    respuesta = await app_client.post(
        "/usuarios",
        json={
            "email": "otro@example.com",
            "nombre": "Otro",
            "password": PASSWORD_TEMPORAL,
            "rol": "VENDEDOR",
        },
    )

    assert respuesta.status_code == 403


async def test_sin_sesion_responde_401(app_client: AsyncClient) -> None:
    respuesta = await app_client.post(
        "/usuarios",
        json={
            "email": "otro@example.com",
            "nombre": "Otro",
            "password": PASSWORD_TEMPORAL,
            "rol": "VENDEDOR",
        },
    )

    assert respuesta.status_code == 401


async def test_admin_con_debe_cambiar_password_no_puede_usar_el_grupo_protegido(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    from sqlalchemy import update

    await crear_admin(app_client, db_sessionmaker)

    async with db_sessionmaker() as session:
        await session.execute(
            update(Usuario)
            .where(Usuario.email == "admin@example.com")
            .values(debe_cambiar_password=True)
        )
        await session.commit()

    respuesta = await app_client.post(
        "/usuarios",
        json={
            "email": "bloqueado@example.com",
            "nombre": "Bloqueado",
            "password": PASSWORD_TEMPORAL,
            "rol": "VENDEDOR",
        },
    )

    assert respuesta.status_code == 403
