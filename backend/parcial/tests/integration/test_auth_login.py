from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.main import app
from parcial.app.modules.usuarios.models import IntentoAcceso
from parcial.app.modules.usuarios.repository import IntentoAccesoRepository

PASSWORD = "secreto-seguro"
EMAIL = "ana@example.com"


async def _registrar(client: AsyncClient, email: str = EMAIL) -> None:
    response = await client.post(
        "/auth/registro",
        json={"email": email, "nombre": "Ana", "password": PASSWORD},
    )
    assert response.status_code == 201


async def _ultima_ip(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> str:
    async with sessionmaker() as session:
        return await session.scalar(
            select(IntentoAcceso.ip).order_by(IntentoAcceso.id.desc()).limit(1)
        )


async def test_login_exitoso_devuelve_200_sin_password_hash(
    app_client: AsyncClient,
) -> None:
    await _registrar(app_client)

    respuesta = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["email"] == EMAIL
    assert "password_hash" not in cuerpo


async def test_login_invalido_y_email_inexistente_comparten_401_generico(
    app_client: AsyncClient,
) -> None:
    await _registrar(app_client)

    password_incorrecta = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": "otra-clave"},
    )
    email_inexistente = await app_client.post(
        "/auth/login",
        json={"email": "nadie@example.com", "password": PASSWORD},
    )

    assert password_incorrecta.status_code == 401
    assert email_inexistente.status_code == 401
    assert password_incorrecta.json()["detail"] == email_inexistente.json()["detail"]


async def test_email_inexistente_verifica_contra_el_hash_ficticio(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hashes_usados: list[bytes] = []

    def espia_checkpw(password: bytes, password_hash: bytes) -> bool:
        hashes_usados.append(password_hash)
        return False

    monkeypatch.setattr(bcrypt, "checkpw", espia_checkpw)

    respuesta = await app_client.post(
        "/auth/login",
        json={"email": "nadie@example.com", "password": PASSWORD},
    )

    assert respuesta.status_code == 401
    assert hashes_usados == [app.state.fictitious_password_hash.encode("utf-8")]


async def test_cinco_fallos_bloquean_con_429_sin_ejecutar_bcrypt(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _registrar(app_client)
    primer_fallo = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": "mala-clave"},
    )
    assert primer_fallo.status_code == 401
    ip = await _ultima_ip(db_sessionmaker)

    async with db_sessionmaker() as session:
        session.add_all(
            [
                IntentoAcceso(email=EMAIL, ip=ip, exito=False)
                for _ in range(4)
            ]
        )
        await session.commit()

    llamadas_bcrypt: list[int] = []

    def espia_checkpw(password: bytes, password_hash: bytes) -> bool:
        llamadas_bcrypt.append(1)
        return True

    monkeypatch.setattr(bcrypt, "checkpw", espia_checkpw)

    respuesta = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )

    assert respuesta.status_code == 429
    assert respuesta.headers["retry-after"] == "60"
    assert llamadas_bcrypt == []

    async with db_sessionmaker() as session:
        total = await session.scalar(
            select(func.count()).select_from(IntentoAcceso)
        )
    assert total == 6


async def test_menos_de_cinco_fallos_continua_con_la_verificacion(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _registrar(app_client)
    fallo = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": "mala-clave"},
    )
    assert fallo.status_code == 401
    ip = await _ultima_ip(db_sessionmaker)

    async with db_sessionmaker() as session:
        session.add_all(
            [IntentoAcceso(email=EMAIL, ip=ip, exito=False) for _ in range(3)]
        )
        await session.commit()

    respuesta = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )

    assert respuesta.status_code == 200


async def test_contar_fallos_recientes_filtra_ventana_y_exitosos(
    db_session: AsyncSession,
) -> None:
    ahora = datetime.now(timezone.utc)
    db_session.add_all(
        [
            IntentoAcceso(
                cuando=ahora - timedelta(seconds=10),
                email=EMAIL,
                ip="127.0.0.1",
                exito=False,
            ),
            IntentoAcceso(
                cuando=ahora - timedelta(seconds=61),
                email=EMAIL,
                ip="127.0.0.1",
                exito=False,
            ),
            IntentoAcceso(
                cuando=ahora - timedelta(seconds=5),
                email=EMAIL,
                ip="127.0.0.1",
                exito=True,
            ),
        ]
    )
    await db_session.commit()
    repo = IntentoAccesoRepository(db_session)

    fallos = await repo.contar_fallos_recientes(EMAIL, "127.0.0.1", 60)

    assert fallos == 1
