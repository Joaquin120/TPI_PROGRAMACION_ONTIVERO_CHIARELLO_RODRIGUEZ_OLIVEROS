import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.modules.libros.models import Autor, Editorial, Genero, Libro, MovimientoStock
from parcial.app.modules.libros.repository import (
    AutorRepository,
    EditorialRepository,
    GeneroRepository,
    LibroRepository,
    MovimientoStockRepository,
)


async def test_autor_repository_get_and_libros(db_session: AsyncSession) -> None:
    repo = AutorRepository(db_session)
    autor = await repo.add(Autor(nombre="Borges", biografia="Autor argentino"))
    await db_session.commit()

    found = await repo.get_by_id(autor.id)
    assert found is not None
    assert found.nombre == "Borges"

    # Add book for author
    ed = Editorial(nombre="Editorial Sur")
    gen = Genero(nombre="Ficción")
    db_session.add_all([ed, gen])
    await db_session.commit()

    libro = Libro(
        isbn="111-222-333",
        titulo="Ficciones",
        precio=1000,
        stock=5,
        autor_id=autor.id,
        editorial_id=ed.id,
        genero_id=gen.id,
    )
    db_session.add(libro)
    await db_session.commit()

    libros = await repo.get_libros_activos(autor.id)
    assert len(libros) == 1
    assert libros[0].titulo == "Ficciones"
    total = await repo.count_libros_activos(autor.id)
    assert total == 1


async def test_editorial_repository_get_all(db_session: AsyncSession) -> None:
    repo = EditorialRepository(db_session)
    await repo.add(Editorial(nombre="Editorial Sudamericana"))
    await db_session.commit()

    items = await repo.get_all()
    assert any(ed.nombre == "Editorial Sudamericana" for ed in items)


async def test_genero_repository_get_all(db_session: AsyncSession) -> None:
    repo = GeneroRepository(db_session)
    await repo.add(Genero(nombre="Ciencia Ficción"))
    await db_session.commit()

    items = await repo.get_all()
    assert any(g.nombre == "Ciencia Ficción" for g in items)


async def test_libro_repository_crud_filtering_and_soft_delete(db_session: AsyncSession) -> None:
    autor = Autor(nombre="Adolfo Bioy Casares")
    ed = Editorial(nombre="Emecé")
    gen1 = Genero(nombre="Fantástico")
    gen2 = Genero(nombre="Policial")
    db_session.add_all([autor, ed, gen1, gen2])
    await db_session.commit()

    libro1 = Libro(
        isbn="978-950-04-0001-1",
        titulo="La invención de Morel",
        precio=2500,
        stock=10,
        autor_id=autor.id,
        editorial_id=ed.id,
        genero_id=gen1.id,
    )
    libro2 = Libro(
        isbn="978-950-04-0002-2",
        titulo="Plan de evasión",
        precio=3000,
        stock=5,
        autor_id=autor.id,
        editorial_id=ed.id,
        genero_id=gen2.id,
    )
    repo = LibroRepository(db_session)
    await repo.add(libro1)
    await repo.add(libro2)
    await db_session.commit()

    # Eager loading check
    found = await repo.get_by_id(libro1.id)
    assert found is not None
    assert found.autor.nombre == "Adolfo Bioy Casares"
    assert found.editorial.nombre == "Emecé"
    assert found.genero.nombre == "Fantástico"

    # Filter by title (case-insensitive)
    libros_titulo = await repo.get_all_filtrado(titulo="morel")
    assert len(libros_titulo) == 1
    assert libros_titulo[0].id == libro1.id

    # Filter by genre
    libros_genero = await repo.get_all_filtrado(genero_id=gen2.id)
    assert len(libros_genero) == 1
    assert libros_genero[0].id == libro2.id

    # ISBN activo lookup
    activo = await repo.get_by_isbn_activo("978-950-04-0001-1")
    assert activo is not None
    assert activo.id == libro1.id

    # Soft delete
    await repo.soft_delete(libro1)
    await db_session.commit()

    # Normal get returns None
    assert await repo.get_by_id(libro1.id) is None
    # Filtered list excludes soft deleted
    libros_post_delete = await repo.get_all_filtrado()
    assert len(libros_post_delete) == 1
    assert libros_post_delete[0].id == libro2.id

    # ISBN activo lookup now returns None
    assert await repo.get_by_isbn_activo("978-950-04-0001-1") is None

    # Including deleted returns it
    recuperado = await repo.get_by_id_including_deleted(libro1.id)
    assert recuperado is not None
    assert recuperado.borrado_en is not None

    # Pessimistic lock lookup
    bloqueado = await repo.get_by_id_including_deleted_for_update(libro2.id)
    assert bloqueado is not None
    assert bloqueado.id == libro2.id


async def test_movimiento_stock_repository_ledger_and_sum(db_session: AsyncSession) -> None:
    from parcial.app.modules.usuarios.models import Usuario

    user = Usuario(email="stock_user@example.com", nombre="Stock Admin", password_hash="hash")
    autor = Autor(nombre="Cortázar")
    ed = Editorial(nombre="Sudamericana")
    gen = Genero(nombre="Cuentos")
    db_session.add_all([user, autor, ed, gen])
    await db_session.commit()

    libro = Libro(
        isbn="978-950-07-0001-1",
        titulo="Bestiario",
        precio=1800,
        stock=15,
        autor_id=autor.id,
        editorial_id=ed.id,
        genero_id=gen.id,
    )
    db_session.add(libro)
    await db_session.commit()

    repo = MovimientoStockRepository(db_session)
    mov1 = MovimientoStock(
        libro_id=libro.id,
        usuario_id=user.id,
        cantidad=10,
        motivo="Stock inicial",
    )
    mov2 = MovimientoStock(
        libro_id=libro.id,
        usuario_id=user.id,
        cantidad=5,
        motivo="Reposicion",
    )
    await repo.add(mov1)
    await repo.add(mov2)
    await db_session.commit()

    # Query chronological ledger
    items = await repo.get_by_libro_id(libro.id)
    assert len(items) == 2
    assert items[0].motivo == "Stock inicial"
    assert items[1].motivo == "Reposicion"

    count = await repo.count_by_libro_id(libro.id)
    assert count == 2

    total_stock = await repo.sum_cantidad_by_libro_id(libro.id)
    assert total_stock == 15


