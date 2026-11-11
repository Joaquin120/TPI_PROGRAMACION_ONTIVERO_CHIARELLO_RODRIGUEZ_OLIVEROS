"""Async repositories for books, authors, publishers, genres, and stock movements."""

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from parcial.app.core.repository import BaseRepository, SoftDeleteRepository
from parcial.app.modules.libros.models import (
    Autor,
    Editorial,
    Genero,
    Libro,
    MovimientoStock,
)


class AutorRepository(BaseRepository[Autor]):
    """Repository for authors."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Autor)

    async def get_libros_activos(
        self,
        autor_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Libro]:
        """Returns active books by author."""
        stmt = (
            select(Libro)
            .where(Libro.autor_id == autor_id, Libro.borrado_en.is_(None))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_libros_activos(self, autor_id: int) -> int:
        """Counts active books by author."""
        stmt = (
            select(func.count())
            .select_from(Libro)
            .where(Libro.autor_id == autor_id, Libro.borrado_en.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0


class EditorialRepository(BaseRepository[Editorial]):
    """Repository for publishers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Editorial)

    async def get_libros_activos(
        self,
        editorial_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Libro]:
        """Returns active books by publisher."""
        stmt = (
            select(Libro)
            .where(Libro.editorial_id == editorial_id, Libro.borrado_en.is_(None))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_libros_activos(self, editorial_id: int) -> int:
        """Counts active books by publisher."""
        stmt = (
            select(func.count())
            .select_from(Libro)
            .where(Libro.editorial_id == editorial_id, Libro.borrado_en.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0


class GeneroRepository(BaseRepository[Genero]):
    """Repository for book genres."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Genero)

    async def get_libros_activos(
        self,
        genero_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Libro]:
        """Returns active books by genre."""
        stmt = (
            select(Libro)
            .where(Libro.genero_id == genero_id, Libro.borrado_en.is_(None))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_libros_activos(self, genero_id: int) -> int:
        """Counts active books by genre."""
        stmt = (
            select(func.count())
            .select_from(Libro)
            .where(Libro.genero_id == genero_id, Libro.borrado_en.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0


class LibroRepository(SoftDeleteRepository[Libro]):
    """Repository for books with soft delete, eager loading, and filtering."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Libro)

    async def get_by_id(self, id: Any) -> Libro | None:
        """Fetches active book by ID with relationships eagerly loaded."""
        stmt = (
            select(Libro)
            .options(
                joinedload(Libro.autor),
                joinedload(Libro.editorial),
                joinedload(Libro.genero),
            )
            .where(Libro.id == id, Libro.borrado_en.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_id_including_deleted_for_update(self, id: int) -> Libro | None:
        """Fetches book by ID including deleted, with exclusive lock (FOR UPDATE)."""
        stmt = (
            select(Libro)
            .where(Libro.id == id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_isbn_activo(self, isbn: str) -> Libro | None:
        """Fetches active book by exact ISBN."""
        stmt = select(Libro).where(Libro.isbn == isbn, Libro.borrado_en.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_filtrado(
        self,
        skip: int = 0,
        limit: int = 20,
        titulo: str | None = None,
        genero_id: int | None = None,
    ) -> Sequence[Libro]:
        """Fetches active books with optional title ILIKE and genre filters."""
        stmt = (
            select(Libro)
            .options(
                joinedload(Libro.autor),
                joinedload(Libro.editorial),
                joinedload(Libro.genero),
            )
            .where(Libro.borrado_en.is_(None))
        )
        if titulo is not None and titulo.strip():
            stmt = stmt.where(Libro.titulo.ilike(f"%{titulo.strip()}%"))
        if genero_id is not None:
            stmt = stmt.where(Libro.genero_id == genero_id)

        stmt = stmt.order_by(Libro.id.asc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()

    async def count_filtrado(
        self,
        titulo: str | None = None,
        genero_id: int | None = None,
    ) -> int:
        """Counts active books matching the filters."""
        stmt = (
            select(func.count())
            .select_from(Libro)
            .where(Libro.borrado_en.is_(None))
        )
        if titulo is not None and titulo.strip():
            stmt = stmt.where(Libro.titulo.ilike(f"%{titulo.strip()}%"))
        if genero_id is not None:
            stmt = stmt.where(Libro.genero_id == genero_id)

        result = await self.session.execute(stmt)
        return result.scalar_one() or 0


class MovimientoStockRepository(BaseRepository[MovimientoStock]):
    """Repository for append-only stock movement ledger entries."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MovimientoStock)

    async def get_by_libro_id(
        self,
        libro_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[MovimientoStock]:
        """Returns chronological list of stock movements for a book."""
        stmt = (
            select(MovimientoStock)
            .where(MovimientoStock.libro_id == libro_id)
            .order_by(MovimientoStock.cuando.asc(), MovimientoStock.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_libro_id(self, libro_id: int) -> int:
        """Counts stock movements for a book."""
        stmt = (
            select(func.count())
            .select_from(MovimientoStock)
            .where(MovimientoStock.libro_id == libro_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def sum_cantidad_by_libro_id(self, libro_id: int) -> int:
        """Calculates total accumulated stock quantity from all ledger entries."""
        stmt = (
            select(func.coalesce(func.sum(MovimientoStock.cantidad), 0))
            .where(MovimientoStock.libro_id == libro_id)
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)
