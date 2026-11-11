"""Shared helpers for the authentication/administration integration tests."""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.modules.usuarios.models import AsignacionRol, Usuario

PASSWORD = "secreto-seguro"
PASSWORD_TEMPORAL = "temporal-segura"


async def registrar(
    client: AsyncClient,
    email: str,
    *,
    password: str = PASSWORD,
    nombre: str = "Usuario",
) -> None:
    respuesta = await client.post(
        "/auth/registro",
        json={"email": email, "nombre": nombre, "password": password},
    )
    assert respuesta.status_code == 201


async def asignar_rol(
    sessionmaker: async_sessionmaker[AsyncSession],
    email: str,
    rol: str,
) -> None:
    async with sessionmaker() as session:
        usuario = (
            await session.execute(select(Usuario).where(Usuario.email == email))
        ).scalar_one()
        session.add(AsignacionRol(usuario_id=usuario.id, rol=rol))
        await session.commit()


async def obtener_id(
    sessionmaker: async_sessionmaker[AsyncSession],
    email: str,
) -> int:
    """Returns the primary key of the user with the given email."""
    async with sessionmaker() as session:
        usuario = (
            await session.execute(select(Usuario).where(Usuario.email == email))
        ).scalar_one()
        return usuario.id


async def login(
    client: AsyncClient,
    email: str,
    *,
    password: str = PASSWORD,
) -> None:
    respuesta = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert respuesta.status_code == 200


async def crear_admin(
    client: AsyncClient,
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    email: str = "admin@example.com",
    password: str = PASSWORD,
) -> None:
    await registrar(client, email, password=password, nombre="Admin")
    await asignar_rol(sessionmaker, email, "ADMIN")
    await login(client, email, password=password)


# Alias for compatibility with sales integration tests
login_user = login
