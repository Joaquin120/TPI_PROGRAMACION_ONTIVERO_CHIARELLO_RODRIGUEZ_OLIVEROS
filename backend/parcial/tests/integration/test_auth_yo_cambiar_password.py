from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.core.security import verify_password
from parcial.app.modules.usuarios.models import (
    AsignacionRol,
    EventoSeguridad,
    Usuario,
)

PASSWORD = "secreto-seguro"
NUEVA_PASSWORD = "nueva-clave-segura"
EMAIL = "ana@example.com"


async def _registrar(client: AsyncClient) -> None:
    respuesta = await client.post(
        "/auth/registro",
        json={"email": EMAIL, "nombre": "Ana", "password": PASSWORD},
    )
    assert respuesta.status_code == 201


async def _login(client: AsyncClient, password: str = PASSWORD) -> None:
    respuesta = await client.post(
        "/auth/login",
        json={"email": EMAIL, "password": password},
    )
    assert respuesta.status_code == 200


async def _marcar_cambio_pendiente(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async with sessionmaker() as session:
        await session.execute(
            update(Usuario)
            .where(Usuario.email == EMAIL)
            .values(debe_cambiar_password=True)
        )
        await session.commit()


async def test_yo_devuelve_identidad_roles_y_nunca_password_hash(
    app_client: AsyncClient,
) -> None:
    await _registrar(app_client)
    await _login(app_client)

    respuesta = await app_client.get("/auth/yo")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["usuario"]["email"] == EMAIL
    assert cuerpo["usuario"]["nombre"] == "Ana"
    assert cuerpo["roles_vigentes"] == ["CLIENTE"]
    assert cuerpo["roles_token"] == ["CLIENTE"]
    assert "password_hash" not in respuesta.text


async def test_yo_consulta_roles_vigentes_en_bd_y_toma_los_del_token_como_informativos(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _registrar(app_client)
    await _login(app_client)

    async with db_sessionmaker() as session:
        usuario = (
            await session.execute(
                select(Usuario).where(Usuario.email == EMAIL)
            )
        ).scalar_one()
        session.add(AsignacionRol(usuario_id=usuario.id, rol="VENDEDOR"))
        await session.commit()

    respuesta = await app_client.get("/auth/yo")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["roles_vigentes"] == ["CLIENTE", "VENDEDOR"]
    assert cuerpo["roles_token"] == ["CLIENTE"]


async def test_cambiar_password_con_marca_pendiente_limpia_la_marca_y_audita(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _registrar(app_client)
    await _marcar_cambio_pendiente(db_sessionmaker)
    await _login(app_client)

    respuesta = await app_client.post(
        "/auth/cambiar-password",
        json={"password_actual": PASSWORD, "password_nueva": NUEVA_PASSWORD},
    )

    assert respuesta.status_code == 200

    async with db_sessionmaker() as session:
        usuario = (
            await session.execute(
                select(Usuario).where(Usuario.email == EMAIL)
            )
        ).scalar_one()
        eventos = (
            await session.execute(select(EventoSeguridad))
        ).scalars().all()

    assert usuario.debe_cambiar_password is False
    assert await verify_password(NUEVA_PASSWORD, usuario.password_hash)
    assert len(eventos) == 1
    assert eventos[0].actor == EMAIL
    assert eventos[0].accion == "PASSWORD_CAMBIADO"


async def test_cambiar_password_invalida_la_credencial_anterior(
    app_client: AsyncClient,
) -> None:
    await _registrar(app_client)
    await _login(app_client)

    cambio = await app_client.post(
        "/auth/cambiar-password",
        json={"password_actual": PASSWORD, "password_nueva": NUEVA_PASSWORD},
    )
    assert cambio.status_code == 200

    app_client.cookies.clear()
    anterior = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    nueva = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": NUEVA_PASSWORD},
    )

    assert anterior.status_code == 401
    assert nueva.status_code == 200


async def test_cambiar_password_rechaza_actual_incorrecta_sin_mutar(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _registrar(app_client)
    await _login(app_client)

    respuesta = await app_client.post(
        "/auth/cambiar-password",
        json={"password_actual": "clave-equivocada", "password_nueva": NUEVA_PASSWORD},
    )

    assert respuesta.status_code == 401

    async with db_sessionmaker() as session:
        usuario = (
            await session.execute(
                select(Usuario).where(Usuario.email == EMAIL)
            )
        ).scalar_one()

    assert await verify_password(PASSWORD, usuario.password_hash)


async def test_cambiar_password_rechaza_mas_de_72_bytes_con_422(
    app_client: AsyncClient,
) -> None:
    await _registrar(app_client)
    await _login(app_client)

    nueva_larga = await app_client.post(
        "/auth/cambiar-password",
        json={"password_actual": PASSWORD, "password_nueva": "a" * 73},
    )
    actual_larga = await app_client.post(
        "/auth/cambiar-password",
        json={"password_actual": "a" * 73, "password_nueva": NUEVA_PASSWORD},
    )

    assert nueva_larga.status_code == 422
    assert actual_larga.status_code == 422


async def test_cambiar_password_sin_sesion_responde_401(
    app_client: AsyncClient,
) -> None:
    respuesta = await app_client.post(
        "/auth/cambiar-password",
        json={"password_actual": PASSWORD, "password_nueva": NUEVA_PASSWORD},
    )

    assert respuesta.status_code == 401
