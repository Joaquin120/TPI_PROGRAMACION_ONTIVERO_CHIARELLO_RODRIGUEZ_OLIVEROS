from typing import Any, Self
from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Async Unit of Work managing atomic transactions without owning physical session lifecycle.

    Crucial Architectural Rule (CONSIGNA_PARCIAL §1):
    - Receives session from FastAPI's get_session dependency.
    - NEVER creates or closes physical session.
    - Commits on clean __aexit__, rolls back on unhandled exceptions.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._is_active: bool = False

    async def __aenter__(self) -> Self:
        self._is_active = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None:
        self._is_active = False
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        """Commits current transaction boundary."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rolls back current transaction boundary."""
        await self.session.rollback()
