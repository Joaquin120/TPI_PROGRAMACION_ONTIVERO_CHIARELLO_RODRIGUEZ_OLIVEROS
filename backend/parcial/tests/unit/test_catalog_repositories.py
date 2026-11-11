from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.modules import models  # noqa: F401
from parcial.app.modules.libros.models import Autor, Editorial, Genero
from parcial.app.modules.libros.repository import (
    AutorRepository,
    EditorialRepository,
    GeneroRepository,
    LibroRepository,
)


@pytest.mark.asyncio
async def test_autor_repository_methods_call_session() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = AutorRepository(session)

    autor = Autor(id=1, nombre="Borges")
    await repo.add(autor)
    session.add.assert_called_once_with(autor)
    session.flush.assert_awaited_once()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    libros = await repo.get_libros_activos(autor_id=1, skip=0, limit=10)
    assert libros == []
    session.execute.assert_awaited()


@pytest.mark.asyncio
async def test_editorial_repository_methods_call_session() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = EditorialRepository(session)

    ed = Editorial(id=1, nombre="Sur")
    await repo.add(ed)
    session.add.assert_called_once_with(ed)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    libros = await repo.get_libros_activos(editorial_id=1, skip=0, limit=10)
    assert libros == []


@pytest.mark.asyncio
async def test_genero_repository_methods_call_session() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = GeneroRepository(session)

    gen = Genero(id=1, nombre="Ficción")
    await repo.add(gen)
    session.add.assert_called_once_with(gen)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    libros = await repo.get_libros_activos(genero_id=1, skip=0, limit=10)
    assert libros == []


@pytest.mark.asyncio
async def test_libro_repository_unit_calls() -> None:
    session = AsyncMock(spec=AsyncSession)
    repo = LibroRepository(session)

    mock_result = MagicMock()
    mock_result.unique.return_value.scalars.return_value.all.return_value = []
    mock_result.scalar_one.return_value = 0
    session.execute.return_value = mock_result

    libros = await repo.get_all_filtrado(titulo="test", genero_id=2)
    assert libros == []
    count = await repo.count_filtrado(titulo="test", genero_id=2)
    assert count == 0

