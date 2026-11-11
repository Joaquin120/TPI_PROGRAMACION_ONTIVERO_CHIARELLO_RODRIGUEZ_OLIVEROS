"""Async repository for customer entities."""

from collections.abc import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.repository import BaseRepository
from parcial.app.modules.clientes.models import Cliente


class ClienteRepository(BaseRepository[Cliente]):
    """Repository for managing customer persistence with flush-only operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Cliente)

    async def obtener_por_email(self, email: str) -> Cliente | None:
        """Finds a customer by email address."""
        stmt = select(Cliente).where(Cliente.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def obtener_por_usuario_id(self, usuario_id: int) -> Cliente | None:
        """Finds a customer profile linked to a specific user account."""
        stmt = select(Cliente).where(Cliente.usuario_id == usuario_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_paginado(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Cliente]:
        """Returns paginated customer list ordered by ID."""
        stmt = select(Cliente).order_by(Cliente.id.asc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def contar_total(self) -> int:
        """Counts the total customer records."""
        stmt = select(func.count()).select_from(Cliente)
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0
