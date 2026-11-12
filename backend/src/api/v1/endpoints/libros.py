from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models.libro import Libro
from src.db.models.libro_autor import LibroAutor
from src.db.session import get_db
from src.schemas.libro import LibroDetailResponse, LibroResponse

router = APIRouter(tags=["libros"])


@router.get(
    "/",
    response_model=list[LibroResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar catálogo de libros con paginación y búsqueda parcial por título",
)
async def list_libros(
    offset: int = Query(default=0, ge=0, description="Desplazamiento inicial"),
    limit: int = Query(default=20, ge=1, le=100, description="Cantidad máxima de libros"),
    titulo: str | None = Query(default=None, description="Filtro parcial por título"),
    db: AsyncSession = Depends(get_db),
) -> list[LibroResponse]:
    """Retorna la lista de libros del catálogo aplicando filtros y paginación."""
    stmt = (
        select(Libro)
        .options(selectinload(Libro.editorial), selectinload(Libro.genero))
        .offset(offset)
        .limit(limit)
        .order_by(Libro.id.asc())
    )

    if titulo and titulo.strip():
        filtro = f"%{titulo.strip().lower()}%"
        stmt = stmt.where(func.lower(Libro.titulo).ilike(filtro))

    result = await db.execute(stmt)
    libros = result.scalars().all()

    return [
        LibroResponse(
            id=libro.id,
            titulo=libro.titulo,
            isbn=libro.isbn,
            precio=libro.precio,
            stock=libro.stock,
            editorial=libro.editorial.nombre if libro.editorial else "Desconocida",
            genero=libro.genero.nombre if libro.genero else None,
        )
        for libro in libros
    ]


@router.get(
    "/{libro_id}",
    response_model=LibroDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalle completo de un libro incluyendo sus autores",
)
async def get_libro_detail(
    libro_id: int,
    db: AsyncSession = Depends(get_db),
) -> LibroDetailResponse:
    """Retorna el detalle completo de un libro por su ID junto con la lista de autores asociados."""
    stmt = (
        select(Libro)
        .options(
            selectinload(Libro.editorial),
            selectinload(Libro.genero),
            selectinload(Libro.autores_asociados).selectinload(LibroAutor.autor),
        )
        .where(Libro.id == libro_id)
    )

    result = await db.execute(stmt)
    libro = result.scalar_one_or_none()

    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Libro con ID {libro_id} no encontrado",
        )

    autores_response = [
        {
            "autor_id": la.autor_id,
            "nombre": la.autor.nombre if la.autor else "Autor desconocido",
            "rol": la.rol,
            "orden": la.orden,
        }
        for la in sorted(libro.autores_asociados, key=lambda x: x.orden)
    ]

    return LibroDetailResponse(
        id=libro.id,
        titulo=libro.titulo,
        isbn=libro.isbn,
        precio=libro.precio,
        stock=libro.stock,
        editorial_id=libro.editorial_id,
        editorial=libro.editorial.nombre if libro.editorial else None,
        genero_id=libro.genero_id,
        genero=libro.genero.nombre if libro.genero else None,
        autores=autores_response,
    )

