from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.modules.usuarios.models import (
    AsignacionRol,
    EventoSeguridad,
    Usuario,
)
from parcial.app.modules.usuarios.repository import (
    EventoSeguridadRepository,
    UsuarioRepository,
)


async def _crear_usuario(
    session: AsyncSession,
    *,
    email: str,
    nombre: str = "Usuario",
) -> Usuario:
    usuario = Usuario(email=email, nombre=nombre, password_hash="$2b$04$hash-de-prueba")
    session.add(usuario)
    await session.commit()
    return usuario


async def test_get_by_email_returns_the_matching_user(
    db_session: AsyncSession,
) -> None:
    usuario = await _crear_usuario(db_session, email="ana@example.com")
    repo = UsuarioRepository(db_session)

    encontrado = await repo.get_by_email("ana@example.com")
    inexistente = await repo.get_by_email("nadie@example.com")

    assert encontrado is not None
    assert encontrado.id == usuario.id
    assert inexistente is None


async def test_get_roles_vigentes_excludes_revoked_and_expired_assignments(
    db_session: AsyncSession,
) -> None:
    usuario = await _crear_usuario(db_session, email="roles@example.com")
    ahora = datetime.now(timezone.utc)
    db_session.add_all(
        [
            AsignacionRol(usuario_id=usuario.id, rol="ADMIN"),
            AsignacionRol(
                usuario_id=usuario.id,
                rol="VENDEDOR",
                vence_en=ahora + timedelta(days=1),
            ),
            AsignacionRol(
                usuario_id=usuario.id,
                rol="CLIENTE",
                vence_en=ahora - timedelta(days=1),
            ),
            AsignacionRol(
                usuario_id=usuario.id,
                rol="CLIENTE",
                revocada_en=ahora,
            ),
        ]
    )
    await db_session.commit()
    repo = UsuarioRepository(db_session)

    roles = await repo.get_roles_vigentes(usuario.id)

    assert roles == ["ADMIN", "VENDEDOR"]


async def test_bloquear_admins_activos_only_locks_current_administrators(
    db_session: AsyncSession,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    primero = await _crear_usuario(db_session, email="admin1@example.com")
    segundo = await _crear_usuario(db_session, email="admin2@example.com")
    revocado = await _crear_usuario(db_session, email="revocado@example.com")
    vencido = await _crear_usuario(db_session, email="vencido@example.com")
    ahora = datetime.now(timezone.utc)
    db_session.add_all(
        [
            AsignacionRol(usuario_id=primero.id, rol="ADMIN"),
            AsignacionRol(usuario_id=segundo.id, rol="ADMIN"),
            AsignacionRol(usuario_id=revocado.id, rol="ADMIN", revocada_en=ahora),
            AsignacionRol(
                usuario_id=vencido.id,
                rol="ADMIN",
                vence_en=ahora - timedelta(hours=1),
            ),
        ]
    )
    await db_session.commit()
    repo = UsuarioRepository(db_session)

    bloqueadas = await repo.bloquear_admins_activos()

    assert {asignacion.usuario_id for asignacion in bloqueadas} == {
        primero.id,
        segundo.id,
    }

    # A concurrent transaction must not be able to lock the same rows.
    async with db_sessionmaker() as otra_sesion:
        with pytest.raises(DBAPIError):
            await otra_sesion.execute(
                select(AsignacionRol)
                .where(AsignacionRol.rol == "ADMIN")
                .with_for_update(nowait=True)
            )
        await otra_sesion.rollback()

    await db_session.rollback()


async def test_eventos_repository_lists_newest_first_with_pagination(
    db_session: AsyncSession,
) -> None:
    base = datetime.now(timezone.utc)
    db_session.add_all(
        [
            EventoSeguridad(
                cuando=base + timedelta(seconds=indice),
                actor="admin@example.com",
                accion=f"ACCION_{indice}",
            )
            for indice in range(25)
        ]
    )
    await db_session.commit()
    repo = EventoSeguridadRepository(db_session)

    primera_pagina = await repo.listar(skip=0, limit=20)
    segunda_pagina = await repo.listar(skip=20, limit=20)
    total = await repo.contar()

    assert [evento.accion for evento in primera_pagina[:2]] == [
        "ACCION_24",
        "ACCION_23",
    ]
    assert len(primera_pagina) == 20
    assert len(segunda_pagina) == 5
    assert total == 25
