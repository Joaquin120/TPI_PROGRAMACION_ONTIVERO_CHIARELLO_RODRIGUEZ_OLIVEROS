from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.usuarios.models import AsignacionRol, EventoSeguridad
from parcial.app.modules.usuarios.service import revocar_rol
from parcial.tests.integration.helpers import crear_admin, obtener_id, registrar

OBJETIVO = "objetivo@example.com"


def _futuro(dias: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()


async def _asignar_vendedor(app_client: AsyncClient, objetivo_id: int) -> None:
    respuesta = await app_client.post(
        f"/usuarios/{objetivo_id}/roles",
        json={"rol": "VENDEDOR", "vence_en": _futuro()},
    )
    assert respuesta.status_code == 201


async def test_revocacion_exitosa_marca_revocada_en_y_audita(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)
    await registrar(app_client, OBJETIVO)
    objetivo_id = await obtener_id(db_sessionmaker, OBJETIVO)
    await _asignar_vendedor(app_client, objetivo_id)

    respuesta = await app_client.delete(f"/usuarios/{objetivo_id}/roles/VENDEDOR")

    assert respuesta.status_code == 204

    async with db_sessionmaker() as session:
        asignacion = (
            await session.execute(
                select(AsignacionRol).where(
                    AsignacionRol.usuario_id == objetivo_id,
                    AsignacionRol.rol == "VENDEDOR",
                )
            )
        ).scalar_one()
        eventos = (
            await session.execute(
                select(EventoSeguridad).where(EventoSeguridad.accion == "ROL_REVOCADO")
            )
        ).scalars().all()

    assert asignacion.revocada_en is not None
    assert len(eventos) == 1
    assert eventos[0].actor == "admin@example.com"


async def test_revocacion_sin_asignacion_activa_responde_404(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)
    await registrar(app_client, OBJETIVO)
    objetivo_id = await obtener_id(db_sessionmaker, OBJETIVO)

    respuesta = await app_client.delete(f"/usuarios/{objetivo_id}/roles/VENDEDOR")

    assert respuesta.status_code == 404


async def test_revocar_dos_veces_la_misma_asignacion_responde_404(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)
    await registrar(app_client, OBJETIVO)
    objetivo_id = await obtener_id(db_sessionmaker, OBJETIVO)
    await _asignar_vendedor(app_client, objetivo_id)

    primera = await app_client.delete(f"/usuarios/{objetivo_id}/roles/VENDEDOR")
    segunda = await app_client.delete(f"/usuarios/{objetivo_id}/roles/VENDEDOR")

    assert primera.status_code == 204
    assert segunda.status_code == 404


async def test_auto_revocacion_de_admin_responde_409(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)
    admin_id = await obtener_id(db_sessionmaker, "admin@example.com")

    respuesta = await app_client.delete(f"/usuarios/{admin_id}/roles/ADMIN")

    assert respuesta.status_code == 409

    async with db_sessionmaker() as session:
        asignacion = (
            await session.execute(
                select(AsignacionRol).where(
                    AsignacionRol.usuario_id == admin_id,
                    AsignacionRol.rol == "ADMIN",
                )
            )
        ).scalar_one()

    assert asignacion.revocada_en is None


async def test_servicio_rechaza_dejar_el_sistema_sin_administradores(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """Defensive invariant: the guard is a service-level last line of defense.

    Through the HTTP route this branch is unreachable while the actor holds a
    live ADMIN role (which ``solo_admin`` already requires), because a second
    administrator always remains. It is exercised directly here so the
    ``SELECT ... FOR UPDATE`` protection cannot silently regress.
    """
    async with db_sessionmaker() as session:
        from parcial.app.core.security import hash_password
        from parcial.app.modules.usuarios.models import Usuario

        admin = Usuario(
            email="unico-admin@example.com",
            nombre="Único Admin",
            password_hash=await hash_password("secreto-seguro"),
        )
        session.add(admin)
        await session.flush()
        session.add(AsignacionRol(usuario_id=admin.id, rol="ADMIN"))
        await session.commit()
        admin_id = admin.id

    async with db_sessionmaker() as session:
        with pytest.raises(HTTPException) as exc:
            async with UnitOfWork(session) as uow:
                await revocar_rol(
                    uow,
                    usuario_id=admin_id,
                    rol="ADMIN",
                    actor_id=9999,
                    actor_email="otro@example.com",
                )

    assert exc.value.status_code == 409

    async with db_sessionmaker() as session:
        asignacion = (
            await session.execute(
                select(AsignacionRol).where(
                    AsignacionRol.usuario_id == admin_id,
                    AsignacionRol.rol == "ADMIN",
                )
            )
        ).scalar_one()

    assert asignacion.revocada_en is None
