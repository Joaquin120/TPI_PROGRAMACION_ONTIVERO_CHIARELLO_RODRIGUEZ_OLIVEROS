from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic async repository implementing CRUD with explicit flush() only."""

    def __init__(self, session: AsyncSession, model_cls: type[T]) -> None:
        self.session = session
        self.model_cls = model_cls

    async def get_by_id(self, id: Any) -> T | None:
        """Fetches a single entity by primary key."""
        return await self.session.get(self.model_cls, id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int | None = None,
    ) -> Sequence[T]:
        """Fetches all entities with optional pagination offset/limit."""
        stmt = select(self.model_cls).offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Returns the total number of records."""
        stmt = select(func.count()).select_from(self.model_cls)
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def add(self, entity: T) -> T:
        """Persists a new entity with flush() without committing the transaction."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: T) -> T:
        """Synchronizes modifications with flush() without committing the transaction."""
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        """Removes an entity from persistence with flush()."""
        await self.session.delete(entity)
        await self.session.flush()


class SoftDeleteRepository(BaseRepository[T]):
    """Repository specializing in soft-delete entities with 'borrado_en' column."""

    async def get_by_id(self, id: Any) -> T | None:
        """Fetches an active (not soft-deleted) entity by ID."""
        stmt = select(self.model_cls).where(
            getattr(self.model_cls, "id") == id,
            getattr(self.model_cls, "borrado_en").is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int | None = None,
    ) -> Sequence[T]:
        """Fetches all active entities excluding soft-deleted ones."""
        stmt = (
            select(self.model_cls)
            .where(getattr(self.model_cls, "borrado_en").is_(None))
            .offset(skip)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Returns the count of active (non-deleted) records."""
        stmt = (
            select(func.count())
            .select_from(self.model_cls)
            .where(getattr(self.model_cls, "borrado_en").is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def get_by_id_including_deleted(self, id: Any) -> T | None:
        """Fetches an entity by ID regardless of its soft-deletion status."""
        return await super().get_by_id(id)

    async def soft_delete(self, entity: T) -> T:
        """Marks the entity as deleted by setting borrado_en timestamp and flushing."""
        setattr(entity, "borrado_en", datetime.now(timezone.utc))
        await self.session.flush()
        return entity
