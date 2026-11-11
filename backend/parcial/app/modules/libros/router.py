"""HTTP routes for public book catalog and administrative catalog/stock management."""

from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.database import get_session
from parcial.app.core.dependencies import get_usuario_actual, requiere_rol
from parcial.app.core.paginacion import PaginatedResponse, PaginationParams
from parcial.app.core.unit_of_work import UnitOfWork
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
from parcial.app.modules.usuarios.models import Usuario

catalogo_open_router = APIRouter(tags=["Catálogo Público"])
catalogo_admin_router = APIRouter(
    prefix="/libros",
    tags=["Administración de Catálogo y Stock"],
    dependencies=[Depends(requiere_rol("ADMIN"))],
)


# --- 1. Endpoints Públicos de Catálogo ---


@catalogo_open_router.get(
    "/libros",
    response_model=PaginatedResponse[LibroDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def get_libros(
    pagination: Annotated[PaginationParams, Depends()],
    titulo: Annotated[str | None, Query(description="Filtro opcional por título")] = None,
    genero_id: Annotated[int | None, Query(description="Filtro opcional por género")] = None,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[LibroDetailResponse]:
    """Public paginated book catalog excluding soft-deleted books."""
    uow = UnitOfWork(session)
    return await listar_libros_paginado(
        uow,
        page=pagination.page,
        size=pagination.size,
        titulo=titulo,
        genero_id=genero_id,
    )


@catalogo_open_router.get(
    "/libros/{id}",
    response_model=LibroDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_libro(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> LibroDetailResponse:
    """Public single book query by ID with relations."""
    uow = UnitOfWork(session)
    return await obtener_libro_por_id(uow, id)


@catalogo_open_router.get(
    "/autores",
    response_model=list[AutorResponse],
    status_code=status.HTTP_200_OK,
)
async def get_autores(
    session: AsyncSession = Depends(get_session),
) -> list[AutorResponse]:
    """Public list of authors."""
    uow = UnitOfWork(session)
    return await listar_autores(uow)


@catalogo_open_router.get(
    "/autores/{id}/libros",
    response_model=PaginatedResponse[LibroResponse],
    status_code=status.HTTP_200_OK,
)
async def get_libros_por_autor(
    id: int,
    pagination: Annotated[PaginationParams, Depends()],
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[LibroResponse]:
    """Public paginated list of active books by author."""
    uow = UnitOfWork(session)
    return await listar_libros_por_autor(uow, id, page=pagination.page, size=pagination.size)


@catalogo_open_router.get(
    "/editoriales",
    response_model=list[EditorialResponse],
    status_code=status.HTTP_200_OK,
)
async def get_editoriales(
    session: AsyncSession = Depends(get_session),
) -> list[EditorialResponse]:
    """Public list of publishers."""
    uow = UnitOfWork(session)
    return await listar_editoriales(uow)


@catalogo_open_router.get(
    "/editoriales/{id}/libros",
    response_model=PaginatedResponse[LibroResponse],
    status_code=status.HTTP_200_OK,
)
async def get_libros_por_editorial(
    id: int,
    pagination: Annotated[PaginationParams, Depends()],
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[LibroResponse]:
    """Public paginated list of active books by publisher."""
    uow = UnitOfWork(session)
    return await listar_libros_por_editorial(uow, id, page=pagination.page, size=pagination.size)


@catalogo_open_router.get(
    "/generos",
    response_model=list[GeneroResponse],
    status_code=status.HTTP_200_OK,
)
async def get_generos(
    session: AsyncSession = Depends(get_session),
) -> list[GeneroResponse]:
    """Public list of genres."""
    uow = UnitOfWork(session)
    return await listar_generos(uow)


@catalogo_open_router.get(
    "/generos/{id}/libros",
    response_model=PaginatedResponse[LibroResponse],
    status_code=status.HTTP_200_OK,
)
async def get_libros_por_genero(
    id: int,
    pagination: Annotated[PaginationParams, Depends()],
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[LibroResponse]:
    """Public paginated list of active books by genre."""
    uow = UnitOfWork(session)
    return await listar_libros_por_genero(uow, id, page=pagination.page, size=pagination.size)


# --- 2. Endpoints Administrativos de Catálogo y Stock ---


@catalogo_admin_router.post(
    "",
    response_model=LibroDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_libro(
    payload: LibroCreateRequest,
    usuario_actual: Usuario = Depends(get_usuario_actual),
    session: AsyncSession = Depends(get_session),
) -> LibroDetailResponse:
    """Creates a book and initial stock movement atomically (ADMIN only)."""
    uow = UnitOfWork(session)
    async with uow:
        return await crear_libro(uow, payload, admin_id=usuario_actual.id)


@catalogo_admin_router.patch(
    "/{id}",
    response_model=LibroDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def patch_libro(
    id: int,
    payload: LibroUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> LibroDetailResponse:
    """Updates book metadata. Direct stock modification is forbidden (ADMIN only)."""
    uow = UnitOfWork(session)
    async with uow:
        return await actualizar_libro(uow, id, payload)


@catalogo_admin_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_libro(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Soft deletes a book, freeing its ISBN (ADMIN only)."""
    uow = UnitOfWork(session)
    async with uow:
        await eliminar_libro(uow, id)


@catalogo_admin_router.post(
    "/{id}/reponer",
    response_model=LibroDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def post_reponer_stock(
    id: int,
    payload: ReponerStockRequest,
    usuario_actual: Usuario = Depends(get_usuario_actual),
    session: AsyncSession = Depends(get_session),
) -> LibroDetailResponse:
    """Replenishes stock with pessimistic lock and append-only ledger entry (ADMIN only)."""
    uow = UnitOfWork(session)
    async with uow:
        return await reponer_stock(uow, id, payload, admin_id=usuario_actual.id)


@catalogo_admin_router.get(
    "/{id}/movimientos",
    response_model=PaginatedResponse[MovimientoStockResponse],
    status_code=status.HTTP_200_OK,
)
async def get_movimientos(
    id: int,
    pagination: Annotated[PaginationParams, Depends()],
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[MovimientoStockResponse]:
    """Lists chronological stock movements for a book (ADMIN only)."""
    uow = UnitOfWork(session)
    return await listar_movimientos_libro(uow, id, page=pagination.page, size=pagination.size)

