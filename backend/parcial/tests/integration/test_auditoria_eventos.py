from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.modules.usuarios.models import EventoSeguridad
from parcial.tests.integration.helpers import (
    PASSWORD,
    PASSWORD_TEMPORAL,
    crear_admin,
    login,
    obtener_id,
    registrar,
)


def _futuro(dias: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()


async def test_alta_personal_registra_evento_seguridad(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)

    res = await app_client.post(
        "/usuarios",
        json={
            "email": "personal@example.com",
            "nombre": "Personal Test",
            "password": PASSWORD_TEMPORAL,
            "rol": "VENDEDOR",
        },
    )
    assert res.status_code == 201

    async with db_sessionmaker() as session:
        eventos = (
            await session.execute(
                select(EventoSeguridad).where(EventoSeguridad.accion == "USUARIO_CREADO")
            )
        ).scalars().all()

    assert len(eventos) == 1
    assert eventos[0].actor == "admin@example.com"
    assert eventos[0].accion == "USUARIO_CREADO"
    assert eventos[0].cuando is not None


async def test_asignacion_rol_registra_evento_seguridad(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)
    await registrar(app_client, "empleado@example.com")
    empleado_id = await obtener_id(db_sessionmaker, "empleado@example.com")

    res = await app_client.post(
        f"/usuarios/{empleado_id}/roles",
        json={"rol": "VENDEDOR", "vence_en": _futuro()},
    )
    assert res.status_code == 201

    async with db_sessionmaker() as session:
        eventos = (
            await session.execute(
                select(EventoSeguridad).where(EventoSeguridad.accion == "ROL_ASIGNADO")
            )
        ).scalars().all()

    assert len(eventos) == 1
    assert eventos[0].actor == "admin@example.com"
    assert eventos[0].accion == "ROL_ASIGNADO"


async def test_revocacion_rol_registra_evento_seguridad(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)
    await registrar(app_client, "empleado_revocar@example.com")
    empleado_id = await obtener_id(db_sessionmaker, "empleado_revocar@example.com")

    await app_client.post(
        f"/usuarios/{empleado_id}/roles",
        json={"rol": "VENDEDOR", "vence_en": _futuro()},
    )

    res = await app_client.delete(f"/usuarios/{empleado_id}/roles/VENDEDOR")
    assert res.status_code == 204

    async with db_sessionmaker() as session:
        eventos = (
            await session.execute(
                select(EventoSeguridad).where(EventoSeguridad.accion == "ROL_REVOCADO")
            )
        ).scalars().all()

    assert len(eventos) == 1
    assert eventos[0].actor == "admin@example.com"
    assert eventos[0].accion == "ROL_REVOCADO"


async def test_cambio_password_registra_evento_seguridad(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    email = "usuario_cambio@example.com"
    await registrar(app_client, email)
    await login(app_client, email)

    res = await app_client.post(
        "/auth/cambiar-password",
        json={
            "password_actual": PASSWORD,
            "password_nueva": "nuevo-secreto-seguro-123",
        },
    )
    assert res.status_code == 200

    async with db_sessionmaker() as session:
        eventos = (
            await session.execute(
                select(EventoSeguridad).where(EventoSeguridad.accion == "PASSWORD_CAMBIADO")
            )
        ).scalars().all()

    assert len(eventos) == 1
    assert eventos[0].actor == email
    assert eventos[0].accion == "PASSWORD_CAMBIADO"
