import os
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

# Configure test environment variables before module imports
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/tp_cap1a4_db",
)

import httpx
import pytest_asyncio

from src.db.models.item import Item
from src.db.session import get_db
from src.main import app


class FakeResult:
    """Emulates SQLAlchemy 2.0 Result object for AsyncSession."""

    def __init__(
        self,
        data: list[Any],
        is_scalar: bool = False,
        scalar_val: Any = None,
    ) -> None:
        self._data = data
        self._is_scalar = is_scalar
        self._scalar_val = scalar_val

    def scalar_one(self) -> Any:
        if self._is_scalar:
            return self._scalar_val
        if len(self._data) == 1:
            return self._data[0]
        raise ValueError("Expected exactly one result")

    def scalar_one_or_none(self) -> Any:
        if self._is_scalar:
            return self._scalar_val
        return self._data[0] if self._data else None

    def scalars(self) -> "FakeResult":
        return self

    def all(self) -> list[Any]:
        return list(self._data)


class FakeAsyncSession:
    """In-memory async session providing complete DB isolation without external PostgreSQL."""

    def __init__(self, storage: dict[int, Item]) -> None:
        self.storage = storage
        self._added: list[Item] = []
        self._deleted: list[Item] = []

    def add(self, instance: Item) -> None:
        self._added.append(instance)

    async def commit(self) -> None:
        for item in self._added:
            if getattr(item, "id", None) is None:
                new_id = max(self.storage.keys(), default=0) + 1
                item.id = new_id
            now = datetime.now(timezone.utc)
            if getattr(item, "created_at", None) is None:
                item.created_at = now
            item.updated_at = now
            self.storage[item.id] = item
        self._added.clear()

        for item in self._deleted:
            self.storage.pop(item.id, None)
        self._deleted.clear()

    async def refresh(self, instance: Item) -> None:
        now = datetime.now(timezone.utc)
        if getattr(instance, "created_at", None) is None:
            instance.created_at = now
        if getattr(instance, "updated_at", None) is None:
            instance.updated_at = now

    async def delete(self, instance: Item) -> None:
        self._deleted.append(instance)

    async def close(self) -> None:
        pass

    async def execute(self, statement: Any) -> FakeResult:
        sql_str = str(statement).lower()

        target_id: int | None = None
        filter_active: bool | None = None

        # Inspect statement criteria
        if hasattr(statement, "_where_criteria"):
            for crit in statement._where_criteria:
                col_name = getattr(getattr(crit, "left", None), "name", None)
                right = getattr(crit, "right", None)
                val = None
                if right is not None:
                    right_cls = right.__class__.__name__
                    if right_cls == "True_":
                        val = True
                    elif right_cls == "False_":
                        val = False
                    elif hasattr(right, "value"):
                        val = right.value
                    elif hasattr(right, "effective_value"):
                        val = getattr(right, "effective_value", None)

                if col_name == "id":
                    target_id = val
                elif col_name == "is_active":
                    filter_active = val

        # Fallback to compiled bind params if needed
        try:
            params = statement.compile().params
            for k, v in params.items():
                if "id" in k and isinstance(v, int):
                    target_id = v
                elif "is_active" in k and isinstance(v, bool):
                    filter_active = v
        except Exception:
            pass

        if target_id is not None:
            item = self.storage.get(target_id)
            return FakeResult([item] if item is not None else [])

        filtered = list(self.storage.values())
        if filter_active is not None:
            filtered = [it for it in filtered if it.is_active == filter_active]

        if "count" in sql_str:
            return FakeResult([], is_scalar=True, scalar_val=len(filtered))

        offset = getattr(statement, "_offset", None) or 0
        limit = getattr(statement, "_limit", None)

        if offset:
            filtered = filtered[offset:]
        if limit is not None:
            filtered = filtered[:limit]

        return FakeResult(filtered)


@pytest_asyncio.fixture
async def isolated_db() -> AsyncGenerator[dict[int, Item], None]:
    """Provides an isolated in-memory dictionary storage for items."""
    storage: dict[int, Item] = {}
    yield storage


@pytest_asyncio.fixture
async def isolated_items_db(isolated_db: dict[int, Item]) -> AsyncGenerator[dict[int, Item], None]:
    """Alias for backwards compatibility with test_items_api."""
    yield isolated_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Asynchronous HTTP test client using ASGITransport without global session override."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def async_client(isolated_db: dict[int, Item]) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Asynchronous HTTP test client with isolated DB session dependency override."""
    async def override_get_db() -> AsyncGenerator[FakeAsyncSession, None]:
        session = FakeAsyncSession(isolated_db)
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)
