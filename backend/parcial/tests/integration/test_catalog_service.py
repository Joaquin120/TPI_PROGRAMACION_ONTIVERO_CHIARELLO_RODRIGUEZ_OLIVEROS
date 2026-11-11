import pytest
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.libros.models import Autor, Editorial, Genero, Libro
from parcial.app.modules.libros.service import (
    actualizar_libro,
    crear_libro,
    eliminar_libro,
    listar_autores,
    listar_editoriales,
    listar_generos,
    listar_libros_paginado,
    listar_libros_por_autor,
    listar_libros_por_editorial,
    listar_libros_por_genero,
    listar_movimientos_libro,
    obtener_libro_por_id,
    reponer_stock,
)


async def test_listar_auxiliares(db_session: AsyncSession) -> None:
    autor = Autor(nombre="Cortázar", biografia="Escritor")
    ed = Editorial(nombre="Minotauro")
    gen = Genero(nombre="Relatos")
    db_session.add_all([autor, ed, gen])
    await db_session.commit()

    uow = UnitOfWork(db_session)
    autores = await listar_autores(uow)
    editoriales = await listar_editoriales(uow)
    generos = await listar_generos(uow)

    assert any(a.nombre == "Cortázar" for a in autores)
    assert any(e.nombre == "Minotauro" for e in editoriales)
    assert any(g.nombre == "Relatos" for g in generos)


async def test_listar_libros_paginado_and_detail(db_session: AsyncSession) -> None:
    autor = Autor(nombre="Borges")
    ed = Editorial(nombre="Sur")
    gen = Genero(nombre="Ficción")
    db_session.add_all([autor, ed, gen])
    await db_session.commit()

    libro = Libro(
        isbn="111-999-001",
        titulo="El jardín de senderos que se bifurcan",
        precio=Decimal("1500.00"),
        stock=10,
        autor_id=autor.id,
        editorial_id=ed.id,
        genero_id=gen.id,
    )
    db_session.add(libro)
    await db_session.commit()

    uow = UnitOfWork(db_session)
    res = await listar_libros_paginado(uow, page=1, size=10, titulo="jardín")
    assert res.total == 1
    assert res.items[0].titulo == "El jardín de senderos que se bifurcan"
    assert res.items[0].autor.nombre == "Borges"

    # Detail by ID
    detail = await obtener_libro_por_id(uow, libro.id)
    assert detail.id == libro.id
    assert detail.editorial.nombre == "Sur"

    # 404 for non-existent book
    with pytest.raises(HTTPException) as exc_info:
        await obtener_libro_por_id(uow, 999999)
    assert exc_info.value.status_code == 404


async def test_listar_libros_por_relaciones(db_session: AsyncSession) -> None:
    autor = Autor(nombre="Sábato")
    ed = Editorial(nombre="Seix Barral")
    gen = Genero(nombre="Ensayo")
    db_session.add_all([autor, ed, gen])
    await db_session.commit()

    libro = Libro(
        isbn="222-333-444",
        titulo="Sobre héroes y tumbas",
        precio=Decimal("2000.00"),
        stock=5,
        autor_id=autor.id,
        editorial_id=ed.id,
        genero_id=gen.id,
    )
    db_session.add(libro)
    await db_session.commit()

    uow = UnitOfWork(db_session)
    por_autor = await listar_libros_por_autor(uow, autor.id, page=1, size=10)
    assert por_autor.total == 1
    assert por_autor.items[0].id == libro.id

    por_ed = await listar_libros_por_editorial(uow, ed.id, page=1, size=10)
    assert por_ed.total == 1

    por_gen = await listar_libros_por_genero(uow, gen.id, page=1, size=10)
    assert por_gen.total == 1

    # Inexistent author 404
    with pytest.raises(HTTPException) as exc:
        await listar_libros_por_autor(uow, 99999, page=1, size=10)
    assert exc.value.status_code == 404


async def test_crear_libro_atomic_stock_and_conflict(db_session: AsyncSession) -> None:
    from parcial.app.modules.usuarios.models import Usuario
    from parcial.app.modules.libros.schemas import LibroCreateRequest
    from parcial.app.modules.libros.repository import MovimientoStockRepository

    admin = Usuario(email="catalog_admin@example.com", nombre="Admin", password_hash="hash")
    autor = Autor(nombre="Ernesto Sabato")
    ed = Editorial(nombre="Sudamericana")
    gen = Genero(nombre="Novela")
    db_session.add_all([admin, autor, ed, gen])
    await db_session.commit()

    uow = UnitOfWork(db_session)
    payload = LibroCreateRequest(
        isbn="978-950-07-1234-5",
        titulo="El Túnel",
        precio=Decimal("3500.00"),
        stock_inicial=12,
        autor_id=autor.id,
        editorial_id=ed.id,
        genero_id=gen.id,
    )
    async with uow:
        res = await crear_libro(uow, payload, admin_id=admin.id)

    assert res.id is not None
    assert res.titulo == "El Túnel"
    assert res.stock == 12

    # Verify atomic MovimientoStock created
    mov_repo = MovimientoStockRepository(db_session)
    movs = await mov_repo.get_by_libro_id(res.id)
    assert len(movs) == 1
    assert movs[0].cantidad == 12
    assert movs[0].motivo == "Stock inicial"
    assert movs[0].usuario_id == admin.id

    # Duplicate active ISBN -> 409
    with pytest.raises(HTTPException) as exc_info:
        async with uow:
            await crear_libro(uow, payload, admin_id=admin.id)
    assert exc_info.value.status_code == 409


async def test_actualizar_libro_fields_and_404(db_session: AsyncSession) -> None:
    from parcial.app.modules.libros.schemas import LibroUpdateRequest

    autor = Autor(nombre="Bioy")
    ed = Editorial(nombre="Sur")
    gen = Genero(nombre="Ciencia Ficción")
    db_session.add_all([autor, ed, gen])
    await db_session.commit()

    libro = Libro(
        isbn="978-000-111-222-3",
        titulo="Dormir al sol",
        precio=Decimal("1000.00"),
        stock=20,
        autor_id=autor.id,
        editorial_id=ed.id,
        genero_id=gen.id,
    )
    db_session.add(libro)
    await db_session.commit()

    uow = UnitOfWork(db_session)
    async with uow:
        actualizado = await actualizar_libro(
            uow,
            libro.id,
            LibroUpdateRequest(titulo="Dormir al sol (Edición Definitiva)", precio=Decimal("1250.00")),
        )

    assert actualizado.titulo == "Dormir al sol (Edición Definitiva)"
    assert actualizado.precio == Decimal("1250.00")
    assert actualizado.stock == 20  # stock untouched

    # 404 on absent
    with pytest.raises(HTTPException) as exc:
        async with uow:
            await actualizar_libro(uow, 88888, LibroUpdateRequest(titulo="Nuevo"))
    assert exc.value.status_code == 404


async def test_eliminar_libro_soft_delete_and_isbn_reuse(db_session: AsyncSession) -> None:
    from parcial.app.modules.usuarios.models import Usuario
    from parcial.app.modules.libros.schemas import LibroCreateRequest

    admin = Usuario(email="del_admin@example.com", nombre="Del Admin", password_hash="hash")
    autor = Autor(nombre="Quiroga")
    ed = Editorial(nombre="Losada")
    gen = Genero(nombre="Cuentos")
    db_session.add_all([admin, autor, ed, gen])
    await db_session.commit()
    admin_id = admin.id
    autor_id = autor.id
    ed_id = ed.id
    gen_id = gen.id

    uow = UnitOfWork(db_session)
    payload = LibroCreateRequest(
        isbn="978-950-03-9999-9",
        titulo="Cuentos de la selva",
        precio=Decimal("1800.00"),
        stock_inicial=5,
        autor_id=autor_id,
        editorial_id=ed_id,
        genero_id=gen_id,
    )
    async with uow:
        creado = await crear_libro(uow, payload, admin_id=admin_id)

    # Soft delete
    async with uow:
        await eliminar_libro(uow, creado.id)

    # Re-deleting returns 404
    with pytest.raises(HTTPException) as exc1:
        async with uow:
            await eliminar_libro(uow, creado.id)
    assert exc1.value.status_code == 404

    # New book creation with exact SAME ISBN is accepted
    async with uow:
        nuevo = await crear_libro(uow, payload, admin_id=admin_id)


    assert nuevo.id != creado.id
    assert nuevo.isbn == "978-950-03-9999-9"
    assert nuevo.borrado_en is None


async def test_reponer_stock_and_conflict_on_deleted(db_session: AsyncSession) -> None:
    from parcial.app.modules.usuarios.models import Usuario
    from parcial.app.modules.libros.schemas import LibroCreateRequest, ReponerStockRequest

    admin = Usuario(email="restock_admin@example.com", nombre="Admin", password_hash="hash")
    autor = Autor(nombre="García Márquez")
    ed = Editorial(nombre="Sudamericana")
    gen = Genero(nombre="Realismo Mágico")
    db_session.add_all([admin, autor, ed, gen])
    await db_session.commit()
    admin_id = admin.id
    autor_id = autor.id
    ed_id = ed.id
    gen_id = gen.id

    uow = UnitOfWork(db_session)
    async with uow:
        libro = await crear_libro(
            uow,
            LibroCreateRequest(
                isbn="978-950-07-7777-7",
                titulo="Cien años de soledad",
                precio=Decimal("4000.00"),
                stock_inicial=10,
                autor_id=autor_id,
                editorial_id=ed_id,
                genero_id=gen_id,
            ),
            admin_id=admin_id,
        )

    # Restock active book
    async with uow:
        actualizado = await reponer_stock(
            uow,
            libro.id,
            ReponerStockRequest(cantidad=15),
            admin_id=admin_id,
        )
    assert actualizado.stock == 25

    # Check ledger history
    movs = await listar_movimientos_libro(uow, libro.id, page=1, size=10)
    assert movs.total == 2
    assert movs.items[0].motivo == "Stock inicial"
    assert movs.items[1].motivo == "Reposicion"
    assert movs.items[1].cantidad == 15

    # Soft delete book
    async with uow:
        await eliminar_libro(uow, libro.id)

    # Restock soft deleted book must fail with 409 Conflict
    with pytest.raises(HTTPException) as exc_409:
        async with uow:
            await reponer_stock(
                uow,
                libro.id,
                ReponerStockRequest(cantidad=5),
                admin_id=admin_id,
            )
    assert exc_409.value.status_code == 409

    # Restock non-existent book fails with 404
    with pytest.raises(HTTPException) as exc_404:
        async with uow:
            await reponer_stock(
                uow,
                77777,
                ReponerStockRequest(cantidad=5),
                admin_id=admin_id,
            )
    assert exc_404.value.status_code == 404




