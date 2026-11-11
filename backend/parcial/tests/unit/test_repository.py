from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.base import Base
from parcial.app.core.repository import BaseRepository, SoftDeleteRepository


class SampleEntity(Base):
    __tablename__ = "sample_entity"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)


class SoftDeleteEntity(Base):
    __tablename__ = "soft_delete_entity"
    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    borrado_en = Column(DateTime(timezone=True), nullable=True)


@pytest.mark.asyncio
async def test_base_repository_add_calls_flush_never_commit() -> None:
    """Verifies add() flushes to session but never commits."""
    mock_session = AsyncMock(spec=AsyncSession)
    repo = BaseRepository[SampleEntity](mock_session, SampleEntity)

    entity = SampleEntity(id=1, name="Item 1")
    result = await repo.add(entity)

    assert result is entity
    mock_session.add.assert_called_once_with(entity)
    mock_session.flush.assert_awaited_once()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_base_repository_update_calls_flush_never_commit() -> None:
    """Verifies update() flushes to session but never commits."""
    mock_session = AsyncMock(spec=AsyncSession)
    repo = BaseRepository[SampleEntity](mock_session, SampleEntity)

    entity = SampleEntity(id=1, name="Updated")
    result = await repo.update(entity)

    assert result is entity
    mock_session.flush.assert_awaited_once()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_base_repository_delete() -> None:
    """Verifies delete() removes entity and flushes."""
    mock_session = AsyncMock(spec=AsyncSession)
    repo = BaseRepository[SampleEntity](mock_session, SampleEntity)

    entity = SampleEntity(id=1, name="To Delete")
    await repo.delete(entity)

    mock_session.delete.assert_awaited_once_with(entity)
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_base_repository_get_by_id() -> None:
    """Verifies get_by_id() delegates to session.get."""
    mock_session = AsyncMock(spec=AsyncSession)
    expected = SampleEntity(id=42, name="Found")
    mock_session.get.return_value = expected

    repo = BaseRepository[SampleEntity](mock_session, SampleEntity)
    res = await repo.get_by_id(42)

    assert res is expected
    mock_session.get.assert_awaited_once_with(SampleEntity, 42)


@pytest.mark.asyncio
async def test_soft_delete_repository_soft_delete() -> None:
    """Verifies soft_delete() sets borrado_en and flushes without commit."""
    mock_session = AsyncMock(spec=AsyncSession)
    repo = SoftDeleteRepository[SoftDeleteEntity](mock_session, SoftDeleteEntity)

    entity = SoftDeleteEntity(id=1, title="Active", borrado_en=None)
    assert entity.borrado_en is None

    result = await repo.soft_delete(entity)

    assert result.borrado_en is not None
    assert isinstance(result.borrado_en, datetime)
    mock_session.flush.assert_awaited_once()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_soft_delete_repository_including_deleted() -> None:
    """Verifies get_by_id_including_deleted() uses session.get directly."""
    mock_session = AsyncMock(spec=AsyncSession)
    deleted_entity = SoftDeleteEntity(
        id=99,
        title="Archived",
        borrado_en=datetime.now(timezone.utc),
    )
    mock_session.get.return_value = deleted_entity

    repo = SoftDeleteRepository[SoftDeleteEntity](mock_session, SoftDeleteEntity)
    res = await repo.get_by_id_including_deleted(99)

    assert res is deleted_entity
    mock_session.get.assert_awaited_once_with(SoftDeleteEntity, 99)
