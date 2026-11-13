from collections.abc import AsyncGenerator
from typing import Any
import httpx
import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError

from src.db.models.cliente import Cliente
from src.db.models.editorial import Editorial
from src.db.models.genero import Genero
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
        editoriales: dict[int, Editorial] | None = None,
        generos: dict[int, Genero] | None = None,
    ) -> None:
        self.clientes = clientes
        self.libros = libros
        self.ventas = ventas
        self.renglones = renglones
        self.editoriales = editoriales or {}
        self.generos = generos or {}
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
        target_isbn = None
        excluded_id = None
        for k, v in params.items():
            if "id" in k.lower() and isinstance(v, int):
                target_id = v

        if hasattr(statement, "_where_criteria"):
            for crit in statement._where_criteria:
                col = getattr(crit, "left", None)
                val_node = getattr(crit, "right", None)
                col_name = getattr(col, "name", None)
                val = getattr(val_node, "value", None)
                op_name = getattr(getattr(crit, "operator", None), "__name__", "")
                if col_name == "id" and isinstance(val, int):
                    if op_name == "ne":
                        excluded_id = val
                    else:
                        target_id = val
                elif col_name == "isbn" and isinstance(val, str):
                    target_isbn = val

        # Lookup in clientes table
        if "from clientes" in sql_str and target_id is not None:
            match = self.clientes.get(target_id)
            return FakeResult([match] if match else [])

        # Lookup in editoriales table
        if "from editoriales" in sql_str and target_id is not None:
            match = self.editoriales.get(target_id)
            return FakeResult([match] if match else [])

        # Lookup in generos table
        if "from generos" in sql_str and target_id is not None:
            match = self.generos.get(target_id)
            return FakeResult([match] if match else [])

        # Lookup in libros table
        if "from libros" in sql_str:
            if target_isbn is not None:
                matches = [
                    lib
                    for lib in self.libros.values()
                    if lib.isbn == target_isbn and (excluded_id is None or lib.id != excluded_id)
                ]
                return FakeResult(matches[:1])
            if target_id is not None:
                match = self.libros.get(target_id)
                return FakeResult([match] if match else [])
            return FakeResult(list(self.libros.values()))

        # Lookup in ventas table (single by ID or paginated list)
        if "from ventas" in sql_str:
            if target_id is not None:
                match = self.ventas.get(target_id)
                return FakeResult([match] if match else [])

            ordered = sorted(self.ventas.values(), key=lambda v: v.id, reverse=True)
            offset_val = getattr(getattr(statement, "_offset_clause", None), "value", None) or 0
            limit_val = getattr(getattr(statement, "_limit_clause", None), "value", None)
            if limit_val is not None:
                sliced = ordered[offset_val : offset_val + limit_val]
            else:
                sliced = ordered[offset_val:]
            return FakeResult(sliced)

        return FakeResult([])


@pytest_asyncio.fixture
async def ventas_db():
    clientes = {
        1: Cliente(id=1, nombre="Ana Beltrán", email="ana.beltran@example.com")
    }
    editoriales = {
        1: Editorial(id=1, nombre="Planeta"),
        2: Editorial(id=2, nombre="Sudamericana"),
    }
    generos = {
        1: Genero(id=1, nombre="Ficción"),
        2: Genero(id=2, nombre="Ensayo"),
    }
    libros = {
        1: Libro(
            id=1,
            titulo="El principito",
            isbn="978-84-376-0494-7",
            precio=1500.0,
            stock=10,
            editorial_id=1,
            genero_id=1,
            editorial=editoriales[1],
            genero=generos[1],
        ),
        2: Libro(
            id=2,
            titulo="Cuentos de terror",
            isbn="978-987-1111-22-3",
            precio=2000.0,
            stock=5,
            editorial_id=1,
            editorial=editoriales[1],
        ),
    }
    ventas = {}
    renglones = {}
    return {
        "clientes": clientes,
        "libros": libros,
        "ventas": ventas,
        "renglones": renglones,
        "editoriales": editoriales,
        "generos": generos,
    }


@pytest_asyncio.fixture
async def ventas_client(ventas_db) -> AsyncGenerator[httpx.AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[FakeVentasAsyncSession, None]:
        session = FakeVentasAsyncSession(
            ventas_db["clientes"],
            ventas_db["libros"],
            ventas_db["ventas"],
            ventas_db["renglones"],
            ventas_db["editoriales"],
            ventas_db["generos"],
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


@pytest.mark.asyncio
async def test_listar_ventas_paginacion_y_detalle_200_404(ventas_client: httpx.AsyncClient) -> None:
    """Verifica GET /ventas/?limit=&offset= y GET /ventas/{id} incluyendo 404."""
    # Sin ventas aún
    empty_res = await ventas_client.get("/api/v1/ventas/?limit=20&offset=0")
    assert empty_res.status_code == 200
    assert empty_res.json() == []

    # Crear 3 ventas consecutivas
    for cantidad in (1, 2, 3):
        create_res = await ventas_client.post(
            "/api/v1/ventas/",
            json={"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": cantidad}]},
        )
        assert create_res.status_code == 201

    # Paginación descendente (más reciente primero): ids 3, 2, 1
    page_1 = await ventas_client.get("/ventas/?limit=2&offset=0")
    assert page_1.status_code == 200
    data_1 = page_1.json()
    assert [v["id"] for v in data_1] == [3, 2]
    assert data_1[0]["cliente_nombre"] == "Ana Beltrán"
    assert data_1[0]["total"] == 4500.0

    page_2 = await ventas_client.get("/ventas/?limit=2&offset=2")
    assert page_2.status_code == 200
    data_2 = page_2.json()
    assert [v["id"] for v in data_2] == [1]

    # Detalle existente
    detail_res = await ventas_client.get("/api/v1/ventas/2")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == 2
    assert detail["total"] == 3000.0
    assert detail["renglones"][0]["titulo"] == "El principito"
    assert detail["renglones"][0]["precio_unitario"] == 1500.0
    assert detail["renglones"][0]["subtotal"] == 3000.0

    # Detalle inexistente -> 404
    not_found = await ventas_client.get("/api/v1/ventas/999")
    assert not_found.status_code == 404


@pytest.mark.asyncio
async def test_invariante_precio_historico_caso_g05(ventas_client: httpx.AsyncClient) -> None:
    """Caso G-05 / RN-VEN-05: PATCH /libros/{id} cambia el precio futuro pero conserva ventas previas intactas."""
    # 1. Confirmar venta al precio original del catálogo ($1500 y $2000)
    venta_res = await ventas_client.post(
        "/api/v1/ventas/",
        json={
            "cliente_id": 1,
            "renglones": [
                {"libro_id": 1, "cantidad": 2},
                {"libro_id": 2, "cantidad": 1},
            ],
        },
    )
    assert venta_res.status_code == 201
    venta_id = venta_res.json()["id"]
    assert venta_res.json()["total"] == 5000.0

    # 2. Alterar el precio del libro 1 mediante PATCH /libros/1
    patch_res = await ventas_client.patch(
        "/api/v1/libros/1",
        json={"precio": 2750.00},
    )
    assert patch_res.status_code == 200
    assert float(patch_res.json()["precio"]) == 2750.0

    # 3. Consultar la venta histórica y verificar que sus importes NO cambiaron
    hist_res = await ventas_client.get(f"/api/v1/ventas/{venta_id}")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["total"] == 5000.0
    r_libro_1 = next(r for r in hist_data["renglones"] if r["libro_id"] == 1)
    assert r_libro_1["precio_unitario"] == 1500.0
    assert r_libro_1["subtotal"] == 3000.0

    # 4. Una nueva venta sí toma el nuevo precio ($2750)
    nueva_venta = await ventas_client.post(
        "/api/v1/ventas/",
        json={"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": 2}]},
    )
    assert nueva_venta.status_code == 201
    assert nueva_venta.json()["total"] == 5500.0
    assert nueva_venta.json()["renglones"][0]["precio_unitario"] == 2750.0


@pytest.mark.asyncio
async def test_patch_libro_validaciones_y_conflictos(ventas_client: httpx.AsyncClient) -> None:
    """Verifica 404, 409 ISBN duplicado y 422 en PATCH /libros/{id}."""
    not_found = await ventas_client.patch("/api/v1/libros/999", json={"precio": 100.0})
    assert not_found.status_code == 404

    dup_isbn = await ventas_client.patch("/libros/1", json={"isbn": "978-987-1111-22-3"})
    assert dup_isbn.status_code == 409

    bad_precio = await ventas_client.patch("/libros/1", json={"precio": -50})
    assert bad_precio.status_code == 422

    blank_titulo = await ventas_client.patch("/libros/1", json={"titulo": "   "})
    assert blank_titulo.status_code == 422


@pytest.mark.asyncio
async def test_listar_ventas_paginacion_parametros_invalidos_422(ventas_client: httpx.AsyncClient) -> None:
    """Verifica rechazo 422 en GET /ventas/ cuando limit o offset violan los límites."""
    assert (await ventas_client.get("/api/v1/ventas/?limit=0")).status_code == 422
    assert (await ventas_client.get("/api/v1/ventas/?limit=101")).status_code == 422
    assert (await ventas_client.get("/api/v1/ventas/?offset=-1")).status_code == 422


@pytest.mark.asyncio
async def test_patch_libro_relaciones_y_payload_vacio(ventas_client: httpx.AsyncClient) -> None:
    """Verifica actualización de editorial_id, genero_id (incluyendo null), {} y rechazos 422."""
    res_rel = await ventas_client.patch(
        "/api/v1/libros/1",
        json={"editorial_id": 2, "genero_id": 2},
    )
    assert res_rel.status_code == 200
    data_rel = res_rel.json()
    assert data_rel["editorial_id"] == 2
    assert data_rel["editorial"] == "Sudamericana"
    assert data_rel["genero_id"] == 2
    assert data_rel["genero"] == "Ensayo"

    res_null_gen = await ventas_client.patch("/api/v1/libros/1", json={"genero_id": None})
    assert res_null_gen.status_code == 200
    assert res_null_gen.json()["genero_id"] is None
    assert res_null_gen.json()["genero"] is None

    res_empty = await ventas_client.patch("/api/v1/libros/1", json={})
    assert res_empty.status_code == 200
    assert res_empty.json()["titulo"] == "El principito"

    assert (await ventas_client.patch("/libros/1", json={"editorial_id": 999})).status_code == 422
    assert (await ventas_client.patch("/libros/1", json={"genero_id": 999})).status_code == 422
    assert (await ventas_client.patch("/libros/1", json={"editorial_id": None})).status_code == 422


@pytest.mark.asyncio
async def test_post_venta_recarga_relaciones_tras_commit_y_refresh(ventas_db) -> None:
    """Regresión: verifica que create_venta recargue cliente y renglones vía selectinload tras commit/refresh."""
    assert Venta.cliente.property.lazy == "selectin"

    class RefreshExpiringVentasSession(FakeVentasAsyncSession):
        def __init__(self, data: dict[str, Any]) -> None:
            super().__init__(
                data["clientes"],
                data["libros"],
                data["ventas"],
                data["renglones"],
                data["editoriales"],
                data["generos"],
            )
            self._expired_snapshots: dict[int, tuple[Any, list[Any]]] = {}

        async def refresh(self, instance: Any) -> None:
            if isinstance(instance, Venta) and instance.id is not None:
                self._expired_snapshots[instance.id] = (
                    instance.cliente,
                    list(instance.renglones),
                )
                instance.cliente = None  # type: ignore[assignment]
                instance.renglones = []

        async def execute(self, statement: Any) -> FakeResult:
            result = await super().execute(statement)
            sql_str = str(statement).lower()
            has_eager_options = len(getattr(statement, "_with_options", ())) >= 2
            if "from ventas" in sql_str and has_eager_options:
                for v in result._data:
                    if isinstance(v, Venta) and v.id in self._expired_snapshots:
                        cli, rengs = self._expired_snapshots.pop(v.id)
                        v.cliente = cli
                        v.renglones = rengs
            return result

    session = RefreshExpiringVentasSession(ventas_db)

    async def override_get_db() -> AsyncGenerator[FakeVentasAsyncSession, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            res = await client.post(
                "/api/v1/ventas/",
                json={"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": 2}]},
            )
        assert res.status_code == 201
        data = res.json()
        assert data["cliente_nombre"] == "Ana Beltrán"
        assert len(data["renglones"]) == 1
        assert data["renglones"][0]["titulo"] == "El principito"
        assert data["total"] == 3000.0
    finally:
        app.dependency_overrides.pop(get_db, None)
