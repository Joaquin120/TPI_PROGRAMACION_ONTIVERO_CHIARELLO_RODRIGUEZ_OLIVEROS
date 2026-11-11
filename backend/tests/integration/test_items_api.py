from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
import httpx
import pytest
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
async def isolated_items_db() -> AsyncGenerator[dict[int, Item], None]:
    """Dependency override fixture ensuring isolated, deterministic test DB state."""
    storage: dict[int, Item] = {}

    async def override_get_db() -> AsyncGenerator[FakeAsyncSession, None]:
        session = FakeAsyncSession(storage)
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield storage
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_create_item_success(
    client: httpx.AsyncClient,
    isolated_items_db: dict[int, Item],
) -> None:
    """Verifies POST /api/v1/items creates item and returns 201 Created."""
    payload = {
        "name": "Gaming Mouse",
        "description": "Ergonomic RGB mouse",
        "price": 59.99,
        "stock": 25,
        "is_active": True,
    }
    response = await client.post("/api/v1/items/", json=payload)
    if response.status_code == 307:
        response = await client.post("/api/v1/items", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Gaming Mouse"
    assert data["price"] == 59.99
    assert data["stock"] == 25
    assert data["is_active"] is True
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_item_negative_price_unprocessable_entity(
    client: httpx.AsyncClient,
    isolated_items_db: dict[int, Item],
) -> None:
    """Verifies POST /api/v1/items returns 422 Unprocessable Entity for negative price."""
    payload = {"name": "Bad Item", "price": -15.0, "stock": 5}
    response = await client.post("/api/v1/items/", json=payload)
    if response.status_code == 307:
        response = await client.post("/api/v1/items", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_items_with_pagination_and_filters(
    client: httpx.AsyncClient,
    isolated_items_db: dict[int, Item],
) -> None:
    """Verifies GET /api/v1/items returns 200 with list, total, and handles pagination + filter."""
    # Seed 3 items (2 active, 1 inactive)
    for i in range(1, 4):
        url = "/api/v1/items/"
        resp = await client.post(
            url,
            json={
                "name": f"Item {i}",
                "price": float(i * 10),
                "stock": i * 5,
                "is_active": i != 3,
            },
        )
        if resp.status_code == 307:
            await client.post(
                "/api/v1/items",
                json={
                    "name": f"Item {i}",
                    "price": float(i * 10),
                    "stock": i * 5,
                    "is_active": i != 3,
                },
            )

    # All items
    response = await client.get("/api/v1/items/")
    if response.status_code == 307:
        response = await client.get("/api/v1/items")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["skip"] == 0
    assert data["limit"] == 10

    # Pagination: skip=1, limit=1
    page_resp = await client.get("/api/v1/items/?skip=1&limit=1")
    if page_resp.status_code == 307:
        page_resp = await client.get("/api/v1/items?skip=1&limit=1")
    assert page_resp.status_code == 200
    page_data = page_resp.json()
    assert page_data["total"] == 3
    assert len(page_data["items"]) == 1
    assert page_data["skip"] == 1
    assert page_data["limit"] == 1

    # Filter active only
    active_resp = await client.get("/api/v1/items/?is_active=true")
    if active_resp.status_code == 307:
        active_resp = await client.get("/api/v1/items?is_active=true")
    assert active_resp.status_code == 200
    active_data = active_resp.json()
    assert active_data["total"] == 2
    assert all(it["is_active"] is True for it in active_data["items"])

    # Filter inactive only
    inactive_resp = await client.get("/api/v1/items/?is_active=false")
    if inactive_resp.status_code == 307:
        inactive_resp = await client.get("/api/v1/items?is_active=false")
    assert inactive_resp.status_code == 200
    inactive_data = inactive_resp.json()
    assert inactive_data["total"] == 1
    assert all(it["is_active"] is False for it in inactive_data["items"])


@pytest.mark.asyncio
async def test_get_item_by_id_success_and_not_found(
    client: httpx.AsyncClient,
    isolated_items_db: dict[int, Item],
) -> None:
    """Verifies GET /api/v1/items/{id} returns 200 for existing and 404 for missing item."""
    create_resp = await client.post(
        "/api/v1/items/",
        json={"name": "Headphones", "price": 89.0, "stock": 10},
    )
    if create_resp.status_code == 307:
        create_resp = await client.post(
            "/api/v1/items",
            json={"name": "Headphones", "price": 89.0, "stock": 10},
        )
    item_id = create_resp.json()["id"]

    # Existing
    get_resp = await client.get(f"/api/v1/items/{item_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Headphones"

    # Missing
    not_found_resp = await client.get("/api/v1/items/99999")
    assert not_found_resp.status_code == 404
    assert not_found_resp.json()["detail"] == "Item not found"


@pytest.mark.asyncio
async def test_put_item_full_update(
    client: httpx.AsyncClient,
    isolated_items_db: dict[int, Item],
) -> None:
    """Verifies PUT /api/v1/items/{id} performs full update or returns 404."""
    create_resp = await client.post(
        "/api/v1/items/",
        json={"name": "Old Monitor", "price": 150.0, "stock": 5},
    )
    if create_resp.status_code == 307:
        create_resp = await client.post(
            "/api/v1/items",
            json={"name": "Old Monitor", "price": 150.0, "stock": 5},
        )
    item_id = create_resp.json()["id"]

    update_payload = {
        "name": "New 4K Monitor",
        "description": "Ultra HD Display",
        "price": 299.99,
        "stock": 12,
        "is_active": False,
    }
    put_resp = await client.put(f"/api/v1/items/{item_id}", json=update_payload)
    assert put_resp.status_code == 200
    updated = put_resp.json()
    assert updated["name"] == "New 4K Monitor"
    assert updated["description"] == "Ultra HD Display"
    assert updated["price"] == 299.99
    assert updated["stock"] == 12
    assert updated["is_active"] is False

    # 404 on missing
    missing_put = await client.put("/api/v1/items/99999", json=update_payload)
    assert missing_put.status_code == 404


@pytest.mark.asyncio
async def test_patch_item_partial_update(
    client: httpx.AsyncClient,
    isolated_items_db: dict[int, Item],
) -> None:
    """Verifies PATCH /api/v1/items/{id} updates only provided fields or returns 404."""
    create_resp = await client.post(
        "/api/v1/items/",
        json={"name": "Desk Mat", "description": "Leather mat", "price": 25.0, "stock": 50},
    )
    if create_resp.status_code == 307:
        create_resp = await client.post(
            "/api/v1/items",
            json={"name": "Desk Mat", "description": "Leather mat", "price": 25.0, "stock": 50},
        )
    item_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/api/v1/items/{item_id}",
        json={"price": 19.99, "stock": 45},
    )
    assert patch_resp.status_code == 200
    patched = patch_resp.json()
    assert patched["price"] == 19.99
    assert patched["stock"] == 45
    assert patched["name"] == "Desk Mat"
    assert patched["description"] == "Leather mat"

    # 404 on missing
    missing_patch = await client.patch("/api/v1/items/99999", json={"price": 10.0})
    assert missing_patch.status_code == 404


@pytest.mark.asyncio
async def test_delete_item_success_and_not_found(
    client: httpx.AsyncClient,
    isolated_items_db: dict[int, Item],
) -> None:
    """Verifies DELETE /api/v1/items/{id} returns 204 on delete, 404 subsequently and on missing."""
    create_resp = await client.post(
        "/api/v1/items/",
        json={"name": "Temporary Item", "price": 10.0, "stock": 1},
    )
    if create_resp.status_code == 307:
        create_resp = await client.post(
            "/api/v1/items",
            json={"name": "Temporary Item", "price": 10.0, "stock": 1},
        )
    item_id = create_resp.json()["id"]

    # Delete
    del_resp = await client.delete(f"/api/v1/items/{item_id}")
    assert del_resp.status_code == 204

    # Subsequent GET returns 404
    get_resp = await client.get(f"/api/v1/items/{item_id}")
    assert get_resp.status_code == 404

    # Second DELETE returns 404
    del_again = await client.delete(f"/api/v1/items/{item_id}")
    assert del_again.status_code == 404
