"""Domain services for catalog management, books, and stock operations."""

from decimal import Decimal
from fastapi import HTTPException, status

from parcial.app.core.paginacion import (
    PaginatedResponse,
    PaginationParams,
    crear_respuesta_paginada,
)
from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.libros.models import (
    Autor,
    Editorial,
    Genero,
    Libro,
    MovimientoStock,
)
from parcial.app.modules.libros.repository import (
    AutorRepository,
    EditorialRepository,
    GeneroRepository,
    LibroRepository,
    MovimientoStockRepository,
)
from parcial.app.modules.libros.schemas import (
    AutorResponse,
    EditorialResponse,
    GeneroResponse,
    LibroCreateRequest,
    LibroDetailResponse,
    LibroResponse,
    LibroUpdateRequest,
    MovimientoStockResponse,
    ReponerStockRequest,
)

LIBRO_NO_ENCONTRADO = "Libro no encontrado"
AUTOR_NO_ENCONTRADO = "Autor no encontrado"
EDITORIAL_NO_ENCONTRADA = "Editorial no encontrada"
GENERO_NO_ENCONTRADO = "Género no encontrado"
ISBN_DUPLICADO = "Ya existe un libro activo con ese ISBN"
LIBRO_BORRADO_CONFLICTO = "No se puede reponer stock de un libro dado de baja"


async def crear_libro(
    uow: UnitOfWork,
    payload: LibroCreateRequest,
    admin_id: int,
) -> LibroDetailResponse:
    """Creates a new book and initial stock ledger movement atomically."""
    # Validate foreign keys
    if await AutorRepository(uow.session).get_by_id(payload.autor_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=AUTOR_NO_ENCONTRADO)
    if await EditorialRepository(uow.session).get_by_id(payload.editorial_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EDITORIAL_NO_ENCONTRADA)
    if await GeneroRepository(uow.session).get_by_id(payload.genero_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GENERO_NO_ENCONTRADO)

    libro_repo = LibroRepository(uow.session)
    # Check duplicate active ISBN
    if await libro_repo.get_by_isbn_activo(payload.isbn) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ISBN_DUPLICADO,
        )

    libro = Libro(
        isbn=payload.isbn,
        titulo=payload.titulo,
        precio=payload.precio,
        stock=payload.stock_inicial,
        autor_id=payload.autor_id,
        editorial_id=payload.editorial_id,
        genero_id=payload.genero_id,
    )
    await libro_repo.add(libro)

    # Initial stock movement only if stock_inicial > 0 (ck_movimiento_stock_cantidad_no_cero forbids 0)
    if payload.stock_inicial > 0:
        mov_repo = MovimientoStockRepository(uow.session)
        mov = MovimientoStock(
            libro_id=libro.id,
            usuario_id=admin_id,
            cantidad=payload.stock_inicial,
            motivo="Stock inicial",
        )
        await mov_repo.add(mov)

    # Re-fetch with eager loaded relations
    libro_cargado = await libro_repo.get_by_id(libro.id)
    return LibroDetailResponse.model_validate(libro_cargado)


async def actualizar_libro(
    uow: UnitOfWork,
    id: int,
    payload: LibroUpdateRequest,
) -> LibroDetailResponse:
    """Updates book metadata fields. Direct modification of stock is not permitted."""
    libro_repo = LibroRepository(uow.session)
    libro = await libro_repo.get_by_id(id)
    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=LIBRO_NO_ENCONTRADO,
        )

    if payload.autor_id is not None:
        if await AutorRepository(uow.session).get_by_id(payload.autor_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=AUTOR_NO_ENCONTRADO)
        libro.autor_id = payload.autor_id

    if payload.editorial_id is not None:
        if await EditorialRepository(uow.session).get_by_id(payload.editorial_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EDITORIAL_NO_ENCONTRADA)
        libro.editorial_id = payload.editorial_id

    if payload.genero_id is not None:
        if await GeneroRepository(uow.session).get_by_id(payload.genero_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GENERO_NO_ENCONTRADO)
        libro.genero_id = payload.genero_id

    if payload.titulo is not None:
        libro.titulo = payload.titulo
    if payload.precio is not None:
        libro.precio = payload.precio

    await libro_repo.update(libro)
    libro_actualizado = await libro_repo.get_by_id(libro.id)
    return LibroDetailResponse.model_validate(libro_actualizado)


async def eliminar_libro(uow: UnitOfWork, id: int) -> None:
    """Soft deletes an active book. Subsequent queries will exclude it."""
    libro_repo = LibroRepository(uow.session)
    libro = await libro_repo.get_by_id(id)
    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=LIBRO_NO_ENCONTRADO,
        )
    await libro_repo.soft_delete(libro)


async def reponer_stock(
    uow: UnitOfWork,
    libro_id: int,
    payload: ReponerStockRequest,
    admin_id: int,
) -> LibroDetailResponse:
    """Restocks a book using a pessimistic lock and records an append-only movement.
    
    Rejects replenishment on soft-deleted books with HTTP 409 Conflict.
    """
    libro_repo = LibroRepository(uow.session)
    libro = await libro_repo.get_by_id_including_deleted_for_update(libro_id)
    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=LIBRO_NO_ENCONTRADO,
        )
    if libro.borrado_en is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=LIBRO_BORRADO_CONFLICTO,
        )

    libro.stock += payload.cantidad
    await libro_repo.update(libro)

    mov_repo = MovimientoStockRepository(uow.session)
    mov = MovimientoStock(
        libro_id=libro.id,
        usuario_id=admin_id,
        cantidad=payload.cantidad,
        motivo="Reposicion",
    )
    await mov_repo.add(mov)

    libro_cargado = await libro_repo.get_by_id(libro.id)
    return LibroDetailResponse.model_validate(libro_cargado)


async def listar_movimientos_libro(
    uow: UnitOfWork,
    libro_id: int,
    page: int = 1,
    size: int = 20,
) -> PaginatedResponse[MovimientoStockResponse]:
    """Returns paginated chronological movements for a given book."""
    libro_repo = LibroRepository(uow.session)
    libro = await libro_repo.get_by_id_including_deleted(libro_id)
    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=LIBRO_NO_ENCONTRADO,
        )

    mov_repo = MovimientoStockRepository(uow.session)
    skip = (page - 1) * size
    total = await mov_repo.count_by_libro_id(libro_id)
    movimientos = await mov_repo.get_by_libro_id(libro_id, skip=skip, limit=size)
    items = [MovimientoStockResponse.model_validate(m) for m in movimientos]
    return crear_respuesta_paginada(items=items, total=total, page=page, size=size)





async def listar_autores(uow: UnitOfWork) -> list[AutorResponse]:
    """Returns all authors."""
    repo = AutorRepository(uow.session)
    autores = await repo.get_all()
    return [AutorResponse.model_validate(a) for a in autores]


async def listar_editoriales(uow: UnitOfWork) -> list[EditorialResponse]:
    """Returns all publishers."""
    repo = EditorialRepository(uow.session)
    editoriales = await repo.get_all()
    return [EditorialResponse.model_validate(e) for e in editoriales]


async def listar_generos(uow: UnitOfWork) -> list[GeneroResponse]:
    """Returns all book genres."""
    repo = GeneroRepository(uow.session)
    generos = await repo.get_all()
    return [GeneroResponse.model_validate(g) for g in generos]


async def listar_libros_paginado(
    uow: UnitOfWork,
    page: int = 1,
    size: int = 20,
    titulo: str | None = None,
    genero_id: int | None = None,
) -> PaginatedResponse[LibroDetailResponse]:
    """Returns paginated active books with filters and joined relations."""
    repo = LibroRepository(uow.session)
    skip = (page - 1) * size
    total = await repo.count_filtrado(titulo=titulo, genero_id=genero_id)
    libros = await repo.get_all_filtrado(skip=skip, limit=size, titulo=titulo, genero_id=genero_id)
    items = [LibroDetailResponse.model_validate(libro) for libro in libros]
    return crear_respuesta_paginada(items=items, total=total, page=page, size=size)


async def obtener_libro_por_id(uow: UnitOfWork, id: int) -> LibroDetailResponse:
    """Returns an active book by ID with full details, or raises 404."""
    repo = LibroRepository(uow.session)
    libro = await repo.get_by_id(id)
    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=LIBRO_NO_ENCONTRADO,
        )
    return LibroDetailResponse.model_validate(libro)


async def listar_libros_por_autor(
    uow: UnitOfWork,
    autor_id: int,
    page: int = 1,
    size: int = 20,
) -> PaginatedResponse[LibroResponse]:
    """Returns paginated active books for a specific author."""
    autor_repo = AutorRepository(uow.session)
    autor = await autor_repo.get_by_id(autor_id)
    if autor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=AUTOR_NO_ENCONTRADO,
        )
    skip = (page - 1) * size
    total = await autor_repo.count_libros_activos(autor_id)
    libros = await autor_repo.get_libros_activos(autor_id, skip=skip, limit=size)
    items = [LibroResponse.model_validate(l) for l in libros]
    return crear_respuesta_paginada(items=items, total=total, page=page, size=size)


async def listar_libros_por_editorial(
    uow: UnitOfWork,
    editorial_id: int,
    page: int = 1,
    size: int = 20,
) -> PaginatedResponse[LibroResponse]:
    """Returns paginated active books for a specific publisher."""
    ed_repo = EditorialRepository(uow.session)
    editorial = await ed_repo.get_by_id(editorial_id)
    if editorial is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=EDITORIAL_NO_ENCONTRADA,
        )
    skip = (page - 1) * size
    total = await ed_repo.count_libros_activos(editorial_id)
    libros = await ed_repo.get_libros_activos(editorial_id, skip=skip, limit=size)
    items = [LibroResponse.model_validate(l) for l in libros]
    return crear_respuesta_paginada(items=items, total=total, page=page, size=size)


async def listar_libros_por_genero(
    uow: UnitOfWork,
    genero_id: int,
    page: int = 1,
    size: int = 20,
) -> PaginatedResponse[LibroResponse]:
    """Returns paginated active books for a specific genre."""
    gen_repo = GeneroRepository(uow.session)
    genero = await gen_repo.get_by_id(genero_id)
    if genero is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=GENERO_NO_ENCONTRADO,
        )
    skip = (page - 1) * size
    total = await gen_repo.count_libros_activos(genero_id)
    libros = await gen_repo.get_libros_activos(genero_id, skip=skip, limit=size)
    items = [LibroResponse.model_validate(l) for l in libros]
    return crear_respuesta_paginada(items=items, total=total, page=page, size=size)
