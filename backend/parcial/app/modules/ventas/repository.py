"""Async repository for sales transactions with eager loading preventing N+1 queries."""

from collections.abc import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from parcial.app.core.repository import BaseRepository
from parcial.app.modules.ventas.models import DetalleVenta, Venta


class VentaRepository(BaseRepository[Venta]):
    """Repository managing sale transactions with eager relationships and flush-only operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Venta)

    async def obtener_por_id_con_detalles(self, venta_id: int) -> Venta | None:
        """Loads a sale with customer, staff seller, and lines items without N+1 queries.

        Critical Architecture Requirement (CONSIGNA_PARCIAL §3.5):
        - Joinedload on single relationships (cliente, usuario).
        - Selectinload on collections (detalles) with nested joinedload on libro.
        - Guarantees exactly 2 SQL queries regardless of line item count.
        """
        stmt = (
            select(Venta)
            .where(Venta.id == venta_id)
            .options(
                joinedload(Venta.cliente),
                joinedload(Venta.usuario),
                selectinload(Venta.detalles).joinedload(DetalleVenta.libro),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_paginado(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Venta]:
        """Returns paginated sales ordered by date descending."""
        stmt = (
            select(Venta)
            .order_by(Venta.fecha.desc(), Venta.id.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def contar_total(self) -> int:
        """Counts the total sales transactions recorded."""
        stmt = select(func.count()).select_from(Venta)
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def listar_por_cliente_paginado(
        self,
        cliente_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Venta]:
        """Returns paginated sales belonging to a specific customer."""
        stmt = (
            select(Venta)
            .where(Venta.cliente_id == cliente_id)
            .order_by(Venta.fecha.desc(), Venta.id.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def contar_por_cliente(self, cliente_id: int) -> int:
        """Counts total sales for a specific customer."""
        stmt = (
            select(func.count())
            .select_from(Venta)
            .where(Venta.cliente_id == cliente_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0
