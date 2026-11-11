"""Async repositories for users, role assignments and security audit events."""

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.core.repository import BaseRepository
from parcial.app.modules.usuarios.models import (
    AsignacionRol,
    EventoSeguridad,
    IntentoAcceso,
    Usuario,
)


class UsuarioRepository(BaseRepository[Usuario]):
    """User queries plus the dynamic RBAC lookups required on every request."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Usuario)

    async def get_by_email(self, email: str) -> Usuario | None:
        """Fetches a user by exact email, returning None when absent."""
        stmt = select(Usuario).where(Usuario.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_roles_vigentes(self, usuario_id: int) -> list[str]:
        """Returns role names with a live assignment for the given user."""
        ahora = datetime.now(timezone.utc)
        stmt = (
            select(AsignacionRol.rol)
            .where(
                AsignacionRol.usuario_id == usuario_id,
                AsignacionRol.revocada_en.is_(None),
                or_(
                    AsignacionRol.vence_en.is_(None),
                    AsignacionRol.vence_en > ahora,
                ),
            )
            .order_by(AsignacionRol.rol)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bloquear_admins_activos(self) -> Sequence[AsignacionRol]:
        """Locks every active ADMIN assignment to protect the last administrator.

        The ``SELECT ... FOR UPDATE`` keeps two concurrent revocations from both
        observing a non-zero administrator count and leaving the system without
        any active ADMIN.
        """
        ahora = datetime.now(timezone.utc)
        stmt = (
            select(AsignacionRol)
            .where(
                AsignacionRol.rol == "ADMIN",
                AsignacionRol.revocada_en.is_(None),
                or_(
                    AsignacionRol.vence_en.is_(None),
                    AsignacionRol.vence_en > ahora,
                ),
            )
            .order_by(AsignacionRol.id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class AsignacionRolRepository(BaseRepository[AsignacionRol]):
    """Role-assignment queries backing the administrative role endpoints."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AsignacionRol)

    async def listar_por_usuario(
        self,
        usuario_id: int,
        skip: int = 0,
        limit: int | None = None,
    ) -> Sequence[AsignacionRol]:
        """Returns every assignment of a user, newest first."""
        stmt = (
            select(AsignacionRol)
            .where(AsignacionRol.usuario_id == usuario_id)
            .order_by(AsignacionRol.id.desc())
            .offset(skip)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def contar_por_usuario(self, usuario_id: int) -> int:
        """Returns the total number of assignments of a user (history included)."""
        stmt = (
            select(func.count())
            .select_from(AsignacionRol)
            .where(AsignacionRol.usuario_id == usuario_id)
        )
        return int(await self.session.scalar(stmt) or 0)

    async def get_activa(self, usuario_id: int, rol: str) -> AsignacionRol | None:
        """Finds a live assignment for ``(usuario_id, rol)``, if any."""
        ahora = datetime.now(timezone.utc)
        stmt = select(AsignacionRol).where(
            AsignacionRol.usuario_id == usuario_id,
            AsignacionRol.rol == rol,
            AsignacionRol.revocada_en.is_(None),
            or_(
                AsignacionRol.vence_en.is_(None),
                AsignacionRol.vence_en > ahora,
            ),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_activa_for_update(self, usuario_id: int, rol: str) -> AsignacionRol | None:
        """Finds a live assignment with row locking."""
        ahora = datetime.now(timezone.utc)
        stmt = (
            select(AsignacionRol)
            .where(
                AsignacionRol.usuario_id == usuario_id,
                AsignacionRol.rol == rol,
                AsignacionRol.revocada_en.is_(None),
                or_(
                    AsignacionRol.vence_en.is_(None),
                    AsignacionRol.vence_en > ahora,
                ),
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_admins_activos_for_update(self) -> Sequence[AsignacionRol]:
        """Locks and returns all active ADMIN assignments."""
        ahora = datetime.now(timezone.utc)
        stmt = (
            select(AsignacionRol)
            .where(
                AsignacionRol.rol == "ADMIN",
                AsignacionRol.revocada_en.is_(None),
                or_(
                    AsignacionRol.vence_en.is_(None),
                    AsignacionRol.vence_en > ahora,
                ),
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class IntentoAccesoRepository(BaseRepository[IntentoAcceso]):
    """Read side of the login-attempt log used by the rate limiter."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, IntentoAcceso)

    async def contar_fallos_recientes(
        self,
        email: str,
        ip: str,
        ventana_segundos: int,
    ) -> int:
        """Counts failed attempts for ``(email, ip)`` inside the sliding window."""
        desde = datetime.now(timezone.utc) - timedelta(seconds=ventana_segundos)
        stmt = (
            select(func.count())
            .select_from(IntentoAcceso)
            .where(
                IntentoAcceso.email == email,
                IntentoAcceso.ip == ip,
                IntentoAcceso.exito.is_(False),
                IntentoAcceso.cuando >= desde,
            )
        )
        return int(await self.session.scalar(stmt) or 0)


class EventoSeguridadRepository(BaseRepository[EventoSeguridad]):
    """Security audit event queries for the administrative listing."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, EventoSeguridad)

    async def registrar(self, *, actor: str, accion: str) -> EventoSeguridad:
        """Stages a security event in the caller's transaction (flush, no commit)."""
        evento = EventoSeguridad(actor=actor, accion=accion)
        return await self.add(evento)

    async def listar(
        self,
        skip: int = 0,
        limit: int | None = None,
    ) -> Sequence[EventoSeguridad]:
        """Returns events newest-first with optional offset/limit pagination."""
        stmt = (
            select(EventoSeguridad)
            .order_by(EventoSeguridad.cuando.desc(), EventoSeguridad.id.desc())
            .offset(skip)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def contar(self) -> int:
        """Returns the total number of security events."""
        return await self.count()


async def registrar_intento_acceso_aislado(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    email: str,
    ip: str,
    exito: bool,
) -> None:
    """Persists one login attempt outside the login transaction.

    Obligatory three-point rationale (CONSIGNA_PARCIAL §2, design decision #2):
    1. What it does differently: opens its own session from the injected
       ``async_sessionmaker``, writes the row, forces ``commit()`` and closes
       the session; it never uses the request-scoped Unit of Work.
    2. Why it does not share the transaction: a failed login rolls back the
       request UoW, which would erase the attempt and prevent the 60-second
       rate-limit counter from ever accumulating failures.
    3. Cost: the committed row survives even when the request fails, so the
       table grows with rejected attempts, and each attempt consumes one extra
       pooled connection for the duration of its own transaction.
    """
    async with sessionmaker() as session:
        session.add(IntentoAcceso(email=email, ip=ip, exito=exito))
        await session.commit()
