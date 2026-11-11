import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.usuarios.models import EventoSeguridad
from parcial.app.modules.usuarios.repository import EventoSeguridadRepository


class _FallaDeMutacion(Exception):
    """Stand-in for a business rule failure after the audit event is staged."""


async def test_evento_seguridad_reverts_with_the_failing_mutation(
    db_session: AsyncSession,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    repo = EventoSeguridadRepository(db_session)

    with pytest.raises(_FallaDeMutacion):
        async with UnitOfWork(db_session):
            await repo.registrar(
                actor="admin@example.com",
                accion="USUARIO_CREADO",
            )
            raise _FallaDeMutacion()

    async with db_sessionmaker() as verificacion:
        total = await verificacion.scalar(
            select(func.count()).select_from(EventoSeguridad)
        )

    assert total == 0


async def test_evento_seguridad_commits_with_the_successful_mutation(
    db_session: AsyncSession,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    repo = EventoSeguridadRepository(db_session)

    async with UnitOfWork(db_session):
        evento = await repo.registrar(
            actor="admin@example.com",
            accion="ROL_ASIGNADO",
        )
        assert evento.id is not None

    async with db_sessionmaker() as verificacion:
        persistido = (
            await verificacion.execute(select(EventoSeguridad))
        ).scalar_one()

    assert persistido.actor == "admin@example.com"
    assert persistido.accion == "ROL_ASIGNADO"
    assert persistido.cuando is not None
