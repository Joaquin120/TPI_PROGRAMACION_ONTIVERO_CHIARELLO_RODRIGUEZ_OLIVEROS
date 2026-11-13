"""Pruebas unitarias para el módulo idempotente `src.db.seed`."""

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.db.models.autor import Autor
from src.db.models.cliente import Cliente
from src.db.models.editorial import Editorial
from src.db.models.genero import Genero
from src.db.models.libro import Libro
from src.db.models.libro_autor import LibroAutor
from src.db.seed import run_seed, seed_database


class _FakeSeedResult:
    def __init__(self, item: Any | None) -> None:
        self._item = item

    def scalar_one_or_none(self) -> Any | None:
        return self._item


class FakeSeedAsyncSession:
    """Sesión asíncrona en memoria que simula consultas por clave natural y flushes."""

    def __init__(self) -> None:
        self.tables: dict[type[Any], list[Any]] = {
            Editorial: [],
            Genero: [],
            Autor: [],
            Libro: [],
            LibroAutor: [],
            Cliente: [],
        }
        self._next_ids: dict[type[Any], int] = {
            Editorial: 1,
            Genero: 1,
            Autor: 1,
            Libro: 1,
            Cliente: 1,
        }
        self._pending: list[Any] = []
        self.committed = 0

    def add(self, instance: Any) -> None:
        self._pending.append(instance)

    async def flush(self) -> None:
        for inst in self._pending:
            cls = type(inst)
            if cls in self._next_ids and getattr(inst, "id", None) is None:
                inst.id = self._next_ids[cls]
                self._next_ids[cls] += 1
            self.tables[cls].append(inst)
        self._pending.clear()

    async def commit(self) -> None:
        await self.flush()
        self.committed += 1

    async def execute(self, statement: Any) -> _FakeSeedResult:
        model = statement.column_descriptions[0]["entity"]
        crit = statement._where_criteria[0]
        col_name = crit.left.name
        expected_val = crit.right.value
        match = next(
            (row for row in self.tables[model] if getattr(row, col_name) == expected_val),
            None,
        )
        return _FakeSeedResult(match)


@pytest.mark.asyncio
async def test_seed_database_crea_registros_minimos_y_es_idempotente() -> None:
    """Verifica creación inicial completa y no duplicación ni alteración en re-ejecución."""
    session = FakeSeedAsyncSession()

    resumen_inicial = await seed_database(session)

    assert resumen_inicial["editoriales_creadas"] >= 3
    assert resumen_inicial["generos_creados"] >= 3
    assert resumen_inicial["autores_creados"] >= 3
    assert resumen_inicial["libros_creados"] >= 3
    assert resumen_inicial["clientes_creados"] >= 1
    assert len(session.tables[LibroAutor]) == len(session.tables[Libro])
    assert all(libro.stock >= 10 for libro in session.tables[Libro])
    assert session.committed == 1

    # Simular cambio posterior de precio (G-05) antes de reiniciar el servicio (G-07)
    libro_objetivo = session.tables[Libro][0]
    precio_actualizado = Decimal("99999.00")
    libro_objetivo.precio = precio_actualizado

    resumen_reintento = await seed_database(session)

    assert resumen_reintento == {
        "editoriales_creadas": 0,
        "generos_creados": 0,
        "autores_creados": 0,
        "libros_creados": 0,
        "clientes_creados": 0,
    }
    assert libro_objetivo.precio == precio_actualizado
    assert session.committed == 2


@pytest.mark.asyncio
async def test_run_seed_cierra_engine_al_finalizar() -> None:
    """Verifica que run_seed abra sesión desde factory y libere el engine."""
    fake_session = FakeSeedAsyncSession()
    fake_cm = AsyncMock()
    fake_cm.__aenter__.return_value = fake_session
    fake_cm.__aexit__.return_value = None

    fake_factory = MagicMock(return_value=fake_cm)
    fake_engine = MagicMock()
    fake_engine.dispose = AsyncMock()

    with patch("src.db.session.async_session_factory", fake_factory), patch(
        "src.db.session.engine", fake_engine
    ):
        resumen = await run_seed()

    assert resumen["libros_creados"] >= 3
    fake_engine.dispose.assert_awaited_once()
