from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.usuarios.models import AsignacionRol, Usuario

PASSWORD = "secreto-seguro"


async def _contar(
    sessionmaker: async_sessionmaker[AsyncSession],
    modelo: type[object],
) -> int:
    async with sessionmaker() as session:
        return await session.scalar(select(func.count()).select_from(modelo))


async def test_registro_crea_usuario_rol_cliente_y_ficha_atomicamente(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    response = await app_client.post(
        "/auth/registro",
        json={"email": "ana@example.com", "nombre": "Ana", "password": PASSWORD},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@example.com"
    assert body["nombre"] == "Ana"
    assert body["roles"] == ["CLIENTE"]
    assert body["debe_cambiar_password"] is False
    assert "password_hash" not in body

    async with db_sessionmaker() as session:
        usuario = (
            await session.execute(
                select(Usuario).where(Usuario.email == "ana@example.com")
            )
        ).scalar_one()
        roles = (
            await session.execute(
                select(AsignacionRol.rol).where(
                    AsignacionRol.usuario_id == usuario.id
                )
            )
        ).scalars().all()
        cliente = (
            await session.execute(
                select(Cliente).where(Cliente.usuario_id == usuario.id)
            )
        ).scalar_one()

    assert roles == ["CLIENTE"]
    assert cliente.email == "ana@example.com"
    assert cliente.nombre == "Ana"
    assert usuario.password_hash.startswith("$2")
    assert usuario.password_hash != PASSWORD


async def test_registro_duplicado_responde_409_sin_registros_parciales(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    payload = {"email": "ana@example.com", "nombre": "Ana", "password": PASSWORD}
    primero = await app_client.post("/auth/registro", json=payload)
    segundo = await app_client.post("/auth/registro", json=payload)

    assert primero.status_code == 201
    assert segundo.status_code == 409
    assert await _contar(db_sessionmaker, Usuario) == 1
    assert await _contar(db_sessionmaker, AsignacionRol) == 1
    assert await _contar(db_sessionmaker, Cliente) == 1


async def test_registro_rechaza_campo_extra_con_422_sin_crear_usuario(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    response = await app_client.post(
        "/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana",
            "password": PASSWORD,
            "activo": False,
        },
    )

    assert response.status_code == 422
    assert await _contar(db_sessionmaker, Usuario) == 0


async def test_registro_rechaza_password_mayor_a_72_bytes_con_422(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    response = await app_client.post(
        "/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana",
            "password": "a" * 73,
        },
    )

    assert response.status_code == 422
    assert await _contar(db_sessionmaker, Usuario) == 0


async def test_registro_acepta_password_de_exactamente_72_bytes(
    app_client: AsyncClient,
) -> None:
    response = await app_client.post(
        "/auth/registro",
        json={
            "email": "limite@example.com",
            "nombre": "Limite",
            "password": "a" * 72,
        },
    )

    assert response.status_code == 201
