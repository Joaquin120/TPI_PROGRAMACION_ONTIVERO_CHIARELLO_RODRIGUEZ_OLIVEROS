from collections.abc import AsyncGenerator
from typing import Any
import httpx
import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError

from src.db.models.cliente import Cliente
from src.db.session import get_db
from src.main import app


class FakeResult:
    """Emulates SQLAlchemy 2.0 Result object for AsyncSession in client tests."""

    def __init__(self, data: list[Any], is_scalar: bool = False, scalar_val: Any = None) -> None:
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


class FakeClienteAsyncSession:
    """In-memory async session providing isolated DB operations for Cliente."""

    def __init__(self, storage: dict[int, Cliente]) -> None:
        self.storage = storage
        self._added: list[Cliente] = []
        self._next_id = max(storage.keys(), default=0) + 1

    def add(self, instance: Cliente) -> None:
        self._added.append(instance)

    async def commit(self) -> None:
        for inst in self._added:
            # Check unique constraint on email
            for existing in self.storage.values():
                if existing.email == inst.email and existing.id != getattr(inst, "id", None):
                    raise IntegrityError("duplicate email", params={}, orig=Exception("unique constraint"))
            if not getattr(inst, "id", None):
                inst.id = self._next_id
                self._next_id += 1
            self.storage[inst.id] = inst
        self._added.clear()

    async def rollback(self) -> None:
        self._added.clear()

    async def refresh(self, instance: Cliente) -> None:
        if instance.id in self.storage:
            stored = self.storage[instance.id]
            instance.nombre = stored.nombre
            instance.email = stored.email

    async def close(self) -> None:
        pass

    async def execute(self, statement: Any) -> FakeResult:
        sql_str = str(statement).lower()
        params = {}
        try:
            compiled = statement.compile()
            params = compiled.params or {}
        except Exception:
            params = getattr(statement, "_params", {})

        target_id = None
        target_email = None

        for k, v in params.items():
            if "id" in k.lower() and isinstance(v, int):
                target_id = v
            elif "email" in k.lower() and isinstance(v, str):
                target_email = v

        if hasattr(statement, "_where_criteria"):
            for crit in statement._where_criteria:
                col = getattr(crit, "left", None)
                val_node = getattr(crit, "right", None)
                col_name = getattr(col, "name", None)
                val = getattr(val_node, "value", None)
                if col_name == "id" and isinstance(val, int):
                    target_id = val
                elif col_name == "email" and isinstance(val, str):
                    target_email = val

        if target_id is not None:
            match = self.storage.get(target_id)
            return FakeResult([match] if match else [])

        if target_email is not None:
            match = next((c for c in self.storage.values() if c.email == target_email), None)
            return FakeResult([match] if match else [])

        # Handle list all: SELECT ... FROM clientes
        if "from clientes" in sql_str:
            items = list(self.storage.values())
            return FakeResult(items)

        return FakeResult([])


@pytest_asyncio.fixture
async def cliente_storage() -> dict[int, Cliente]:
    """Isolated dictionary storage pre-seeded with 1 sample client."""
    c1 = Cliente(id=1, nombre="Ana Beltrán", email="ana.beltran@example.com")
    return {1: c1}


@pytest_asyncio.fixture
async def cliente_client(cliente_storage: dict[int, Cliente]) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client with FakeClienteAsyncSession dependency override."""
    async def override_get_db() -> AsyncGenerator[FakeClienteAsyncSession, None]:
        session = FakeClienteAsyncSession(cliente_storage)
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


@pytest.mark.asyncio
async def test_create_cliente_success_201(cliente_client: httpx.AsyncClient) -> None:
    """Verifies POST /api/v1/clientes/ creates a new client and returns 201 Created."""
    payload = {"nombre": "Carlos Gómez", "email": "carlos.gomez@example.com"}
    response = await cliente_client.post("/api/v1/clientes/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 2
    assert data["nombre"] == "Carlos Gómez"
    assert data["email"] == "carlos.gomez@example.com"


@pytest.mark.asyncio
async def test_create_cliente_duplicate_email_409(cliente_client: httpx.AsyncClient) -> None:
    """Verifies POST /api/v1/clientes/ returns 409 Conflict when email is duplicated (RN-CLI-01)."""
    payload = {"nombre": "Ana Duplicada", "email": "ana.beltran@example.com"}
    response = await cliente_client.post("/api/v1/clientes/", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "ya se encuentra registrado" in data["detail"].lower()


@pytest.mark.asyncio
async def test_create_cliente_validation_error_422(cliente_client: httpx.AsyncClient) -> None:
    """Verifies POST /api/v1/clientes/ returns 422 Unprocessable Entity on invalid payload (RN-CLI-02)."""
    # Empty nombre
    res_empty = await cliente_client.post("/api/v1/clientes/", json={"nombre": "  ", "email": "valid@email.com"})
    assert res_empty.status_code == 422

    # Invalid email syntax
    res_email = await cliente_client.post("/api/v1/clientes/", json={"nombre": "Marcos", "email": "not-valid-email"})
    assert res_email.status_code == 422


@pytest.mark.asyncio
async def test_get_cliente_by_id_success_200(cliente_client: httpx.AsyncClient) -> None:
    """Verifies GET /api/v1/clientes/{id} returns 200 OK with client details."""
    response = await cliente_client.get("/api/v1/clientes/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["nombre"] == "Ana Beltrán"
    assert data["email"] == "ana.beltran@example.com"


@pytest.mark.asyncio
async def test_get_cliente_by_id_not_found_404(cliente_client: httpx.AsyncClient) -> None:
    """Verifies GET /api/v1/clientes/{id} returns 404 Not Found for nonexistent ID."""
    response = await cliente_client.get("/api/v1/clientes/999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_list_clientes_200(cliente_client: httpx.AsyncClient) -> None:
    """Verifies GET /api/v1/clientes/ returns 200 OK and list of clients."""
    response = await cliente_client.get("/api/v1/clientes/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["nombre"] == "Ana Beltrán"


@pytest.mark.asyncio
async def test_cliente_routes_prefix_aliases(cliente_client: httpx.AsyncClient) -> None:
    """Verifies /clientes/ alias endpoints work without /api/v1 prefix."""
    res_list = await cliente_client.get("/clientes/")
    assert res_list.status_code == 200

    res_get = await cliente_client.get("/clientes/1")
    assert res_get.status_code == 200
