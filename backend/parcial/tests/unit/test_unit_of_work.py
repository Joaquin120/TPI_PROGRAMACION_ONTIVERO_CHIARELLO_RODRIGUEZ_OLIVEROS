from unittest.mock import AsyncMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.unit_of_work import UnitOfWork


@pytest.mark.asyncio
async def test_unit_of_work_commits_on_clean_exit() -> None:
    """Verifies that clean exit from UoW context manager calls commit and never close."""
    mock_session = AsyncMock(spec=AsyncSession)
    uow = UnitOfWork(mock_session)

    async with uow as context:
        assert context is uow
        assert uow._is_active is True

    assert uow._is_active is False
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_not_called()
    mock_session.close.assert_not_called()


@pytest.mark.asyncio
async def test_unit_of_work_rolls_back_on_exception() -> None:
    """Verifies that an exception in UoW context triggers rollback, re-raises, and never closes session."""
    mock_session = AsyncMock(spec=AsyncSession)
    uow = UnitOfWork(mock_session)

    with pytest.raises(ValueError, match="Domain failure"):
        async with uow:
            raise ValueError("Domain failure")

    assert uow._is_active is False
    mock_session.rollback.assert_awaited_once()
    mock_session.commit.assert_not_called()
    mock_session.close.assert_not_called()


@pytest.mark.asyncio
async def test_unit_of_work_explicit_commit_and_rollback() -> None:
    """Verifies explicit commit and rollback methods delegate to session."""
    mock_session = AsyncMock(spec=AsyncSession)
    uow = UnitOfWork(mock_session)

    await uow.commit()
    mock_session.commit.assert_awaited_once()

    await uow.rollback()
    mock_session.rollback.assert_awaited_once()
