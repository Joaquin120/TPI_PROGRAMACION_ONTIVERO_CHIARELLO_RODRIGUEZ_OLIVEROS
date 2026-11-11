import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.core.database import async_session_factory, get_sessionmaker
from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.usuarios.models import IntentoAcceso
from parcial.app.modules.usuarios.repository import registrar_intento_acceso_aislado


class _FalloDeLogin(Exception):
    """Stand-in for the credential error that aborts the login transaction."""


async def test_intento_acceso_survives_the_login_uow_rollback(
    db_session: AsyncSession,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    with pytest.raises(_FalloDeLogin):
        async with UnitOfWork(db_session):
            await registrar_intento_acceso_aislado(
                db_sessionmaker,
                email="ana@example.com",
                ip="127.0.0.1",
                exito=False,
            )
            raise _FalloDeLogin()

    async with db_sessionmaker() as verificacion:
        resultado = await verificacion.execute(select(IntentoAcceso))
        intento = resultado.scalar_one()

    assert intento.email == "ana@example.com"
    assert intento.ip == "127.0.0.1"
    assert intento.exito is False
    assert intento.cuando is not None


async def test_registrar_intento_persists_successful_attempts(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await registrar_intento_acceso_aislado(
        db_sessionmaker,
        email="ok@example.com",
        ip="10.0.0.5",
        exito=True,
    )

    async with db_sessionmaker() as verificacion:
        total = await verificacion.scalar(
            select(func.count()).select_from(IntentoAcceso)
        )

    assert total == 1


async def test_get_sessionmaker_returns_configured_factory() -> None:
    assert await get_sessionmaker() is async_session_factory
