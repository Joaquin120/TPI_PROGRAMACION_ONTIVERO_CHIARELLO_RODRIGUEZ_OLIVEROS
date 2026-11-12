from collections.abc import AsyncGenerator
from typing import Any
import httpx
import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError

from src.db.models.cliente import Cliente
from src.db.models.libro import Libro
from src.db.models.venta import Venta
from src.db.models.venta_renglon import VentaRenglon
from src.db.session import get_db
from src.main import app


class FakeResult:
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


class FakeVentasAsyncSession:
    """In-memory async session providing isolated DB operations for Ventas and related entities."""

    def __init__(
        self,
        clientes: dict[int, Cliente],
        libros: dict[int, Libro],
        ventas: dict[int, Venta],
        renglones: dict[int, VentaRenglon],
    ) -> None:
        self.clientes = clientes
        self.libros = libros
        self.ventas = ventas
        self.renglones = renglones
        self._added: list[Any] = []
        self._next_venta_id = max(ventas.keys(), default=0) + 1
        self._next_renglon_id = max(renglones.keys(), default=0) + 1

    def add(self, instance: Any) -> None:
        self._added.append(instance)

    async def commit(self) -> None:
        for inst in self._added:
            if isinstance(inst, Venta):
                if not getattr(inst, "id", None):
                    inst.id = self._next_venta_id
                    self._next_venta_id += 1
                self.ventas[inst.id] = inst
                for r in getattr(inst, "renglones", []):
                    if not getattr(r, "id", None):
                        r.id = self._next_renglon_id
                        self._next_renglon_id += 1
                    r.venta_id = inst.id
                    self.renglones[r.id] = r
            elif isinstance(inst, VentaRenglon):
                if not getattr(inst, "id", None):
                    inst.id = self._next_renglon_id
                    self._next_renglon_id += 1
                self.renglones[inst.id] = inst
        self._added.clear()

    async def rollback(self) -> None:
        self._added.clear()

    async def refresh(self, instance: Any) -> None:
        pass

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
        for k, v in params.items():
            if "id" in k.lower() and isinstance(v, int):
                target_id = v

        if hasattr(statement, "_where_criteria"):
            for crit in statement._where_criteria:
                col = getattr(crit, "left", None)
                val_node = getattr(crit, "right", None)
                col_name = getattr(col, "name", None)
                val = getattr(val_node, "value", None)
                if col_name == "id" and isinstance(val, int):
                    target_id = val

        # Lookup in clientes table
        if "from clientes" in sql_str and target_id is not None:
            match = self.clientes.get(target_id)
            return FakeResult([match] if match else [])

        # Lookup in libros table
        if "from libros" in sql_str and target_id is not None:
            match = self.libros.get(target_id)
            return FakeResult([match] if match else [])

        # Lookup in ventas table
        if "from ventas" in sql_str and target_id is not None:
            match = self.ventas.get(target_id)
            return FakeResult([match] if match else [])

        return FakeResult([])


@pytest_asyncio.fixture
async def ventas_db():
    clientes = {
        1: Cliente(id=1, nombre="Ana Beltrán", email="ana.beltran@example.com")
    }
    libros = {
        1: Libro(id=1, titulo="El principito", isbn="978-84-376-0494-7", precio=1500.0, stock=10, editorial_id=1),
        2: Libro(id=2, titulo="Cuentos de terror", isbn="978-987-1111-22-3", precio=2000.0, stock=5, editorial_id=1),
    }
    ventas = {}
    renglones = {}
    return {
        "clientes": clientes,
        "libros": libros,
        "ventas": ventas,
        "renglones": renglones,
    }


@pytest_asyncio.fixture
async def ventas_client(ventas_db) -> AsyncGenerator[httpx.AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[FakeVentasAsyncSession, None]:
        session = FakeVentasAsyncSession(
            ventas_db["clientes"],
            ventas_db["libros"],
            ventas_db["ventas"],
            ventas_db["renglones"],
        )
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
async def test_crear_venta_exitosa_201_caso_g04(ventas_client: httpx.AsyncClient) -> None:
    """Caso G-04: Registro de venta válida con 2 renglones, cálculo oficial y congelamiento de precios."""
    payload = {
        "cliente_id": 1,
        "renglones": [
            {"libro_id": 1, "cantidad": 2},
            {"libro_id": 2, "cantidad": 1},
        ],
    }
    response = await ventas_client.post("/api/v1/ventas/", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["id"] == 1
    assert data["cliente_id"] == 1
    assert data["cliente_nombre"] == "Ana Beltrán"
    assert "fecha" in data
    # Libro 1: 2 * 1500 = 3000, Libro 2: 1 * 2000 = 2000 => Total = 5000 (RN-VEN-06)
    assert data["total"] == 5000.0
    assert len(data["renglones"]) == 2

    r1 = next(r for r in data["renglones"] if r["libro_id"] == 1)
    assert r1["cantidad"] == 2
    assert r1["precio_unitario"] == 1500.0
    assert r1["subtotal"] == 3000.0

    r2 = next(r for r in data["renglones"] if r["libro_id"] == 2)
    assert r2["cantidad"] == 1
    assert r2["precio_unitario"] == 2000.0
    assert r2["subtotal"] == 2000.0


@pytest.mark.asyncio
async def test_crear_venta_cliente_inexistente_409_caso_g06(ventas_client: httpx.AsyncClient) -> None:
    """Caso G-06: Venta rechazada con 409 Conflict si el cliente no existe (RN-VEN-01)."""
    payload = {
        "cliente_id": 999,
        "renglones": [{"libro_id": 1, "cantidad": 1}],
    }
    response = await ventas_client.post("/api/v1/ventas/", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "cliente" in data["detail"].lower()


@pytest.mark.asyncio
async def test_crear_venta_libro_inexistente_409(ventas_client: httpx.AsyncClient) -> None:
    """Venta rechazada con 409 Conflict si algún libro no existe (RN-VEN-01)."""
    payload = {
        "cliente_id": 1,
        "renglones": [{"libro_id": 999, "cantidad": 1}],
    }
    response = await ventas_client.post("/api/v1/ventas/", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "libro" in data["detail"].lower()


@pytest.mark.asyncio
async def test_crear_venta_libro_duplicado_422_caso_g06(ventas_client: httpx.AsyncClient) -> None:
    """Caso G-06: Venta rechazada con 422 si se repite el mismo libro en más de un renglón (RN-VEN-04)."""
    payload = {
        "cliente_id": 1,
        "renglones": [
            {"libro_id": 1, "cantidad": 1},
            {"libro_id": 1, "cantidad": 2},
        ],
    }
    response = await ventas_client.post("/api/v1/ventas/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_crear_venta_sin_renglones_o_cantidad_invalida_422(ventas_client: httpx.AsyncClient) -> None:
    """Venta rechazada con 422 si no hay renglones o cantidad <= 0 (RN-VEN-02, RN-VEN-03)."""
    # Sin renglones
    res_vacia = await ventas_client.post("/api/v1/ventas/", json={"cliente_id": 1, "renglones": []})
    assert res_vacia.status_code == 422

    # Cantidad 0
    res_cero = await ventas_client.post(
        "/api/v1/ventas/",
        json={"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": 0}]},
    )
    assert res_cero.status_code == 422


@pytest.mark.asyncio
async def test_ventas_prefix_alias(ventas_client: httpx.AsyncClient) -> None:
    """Verifica que el endpoint responda tanto en /ventas/ como en /api/v1/ventas/."""
    payload = {
        "cliente_id": 1,
        "renglones": [{"libro_id": 1, "cantidad": 1}],
    }
    response = await ventas_client.post("/ventas/", json=payload)
    assert response.status_code == 201
