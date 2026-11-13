from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models.autor import Autor
from src.db.models.editorial import Editorial
from src.db.models.genero import Genero
from src.db.models.libro import Libro
from src.db.models.libro_autor import LibroAutor
from src.db.session import get_db
from src.schemas.libro import (
    LibroCreate,
    LibroDetailResponse,
    LibroResponse,
    LibroUpdate,
)

router = APIRouter(tags=["libros"])


@router.post(
    "/",
    response_model=LibroDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo libro con sus autorías",
)
async def create_libro(
    libro_in: LibroCreate,
    db: AsyncSession = Depends(get_db),
) -> LibroDetailResponse:
    """Crea y persiste un nuevo libro junto con sus relaciones de autoría de forma atómica."""
    # 1. Verificar si el ISBN ya existe (RN-LIB-01)
    stmt_isbn = select(Libro).where(Libro.isbn == libro_in.isbn.strip())
    existing_libro = (await db.execute(stmt_isbn)).scalar_one_or_none()
    if existing_libro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El ISBN '{libro_in.isbn}' ya se encuentra registrado",
        )

    # 2. Verificar existencia de la editorial
    stmt_ed = select(Editorial).where(Editorial.id == libro_in.editorial_id)
    editorial = (await db.execute(stmt_ed)).scalar_one_or_none()
    if not editorial:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La editorial con ID {libro_in.editorial_id} no existe",
        )

    # 3. Verificar existencia del género si fue provisto
    genero = None
    if libro_in.genero_id is not None:
        stmt_gen = select(Genero).where(Genero.id == libro_in.genero_id)
        genero = (await db.execute(stmt_gen)).scalar_one_or_none()
        if not genero:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"El género con ID {libro_in.genero_id} no existe",
            )

    # 4. Verificar autores
    autores_map = {}
    for item in libro_in.autores:
        stmt_aut = select(Autor).where(Autor.id == item.autor_id)
        autor = (await db.execute(stmt_aut)).scalar_one_or_none()
        if not autor:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"El autor con ID {item.autor_id} no existe",
            )
        autores_map[item.autor_id] = autor

    # 5. Persistencia transaccional
    try:
        nuevo_libro = Libro(
            titulo=libro_in.titulo.strip(),
            isbn=libro_in.isbn.strip(),
            precio=libro_in.precio,
            stock=libro_in.stock,
            editorial_id=libro_in.editorial_id,
            genero_id=libro_in.genero_id,
        )
        db.add(nuevo_libro)
        await db.flush()

        autores_resp = []
        for item in libro_in.autores:
            la = LibroAutor(
                libro_id=nuevo_libro.id,
                autor_id=item.autor_id,
                rol=item.rol,
                orden=item.orden,
            )
            db.add(la)
            autores_resp.append(
                {
                    "autor_id": item.autor_id,
                    "nombre": autores_map[item.autor_id].nombre,
                    "rol": item.rol,
                    "orden": item.orden,
                }
            )

        await db.commit()
        await db.refresh(nuevo_libro)

        return LibroDetailResponse(
            id=nuevo_libro.id,
            titulo=nuevo_libro.titulo,
            isbn=nuevo_libro.isbn,
            precio=nuevo_libro.precio,
            stock=nuevo_libro.stock,
            editorial_id=nuevo_libro.editorial_id,
            editorial=editorial.nombre,
            genero_id=nuevo_libro.genero_id,
            genero=genero.nombre if genero else None,
            autores=autores_resp,
        )

    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflicto de integridad: {exc.orig}",
        ) from exc


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


def _build_libro_detail_response(libro: Libro) -> LibroDetailResponse:
    """Construye la respuesta detallada de un libro incluyendo autores ordenados."""
    autores_response = [
        {
            "autor_id": la.autor_id,
            "nombre": la.autor.nombre if la.autor else "Autor desconocido",
            "rol": la.rol,
            "orden": la.orden,
        }
        for la in sorted(getattr(libro, "autores_asociados", []), key=lambda x: x.orden)
    ]

    return LibroDetailResponse(
        id=libro.id,
        titulo=libro.titulo,
        isbn=libro.isbn,
        precio=libro.precio,
        stock=libro.stock,
        editorial_id=libro.editorial_id,
        editorial=libro.editorial.nombre if getattr(libro, "editorial", None) else None,
        genero_id=libro.genero_id,
        genero=libro.genero.nombre if getattr(libro, "genero", None) else None,
        autores=autores_response,
    )


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

    return _build_libro_detail_response(libro)


@router.patch(
    "/{libro_id}",
    response_model=LibroDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar parcialmente un libro (ej. precio o stock) sin alterar ventas históricas",
)
async def update_libro(
    libro_id: int,
    libro_in: LibroUpdate,
    db: AsyncSession = Depends(get_db),
) -> LibroDetailResponse:
    """Actualiza parcialmente los atributos de un libro en el catálogo (G-05 / RN-VEN-05)."""
    stmt = (
        select(Libro)
        .options(
            selectinload(Libro.editorial),
            selectinload(Libro.genero),
            selectinload(Libro.autores_asociados).selectinload(LibroAutor.autor),
        )
        .where(Libro.id == libro_id)
    )
    libro = (await db.execute(stmt)).scalar_one_or_none()

    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Libro con ID {libro_id} no encontrado",
        )

    fields_set = libro_in.model_fields_set

    if "titulo" in fields_set:
        if libro_in.titulo is None or not libro_in.titulo.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El título del libro no puede estar vacío",
            )
        libro.titulo = libro_in.titulo.strip()

    if "isbn" in fields_set:
        if libro_in.isbn is None or not libro_in.isbn.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El ISBN del libro no puede estar vacío",
            )
        nuevo_isbn = libro_in.isbn.strip()
        if nuevo_isbn != libro.isbn:
            stmt_isbn = select(Libro).where(Libro.isbn == nuevo_isbn, Libro.id != libro_id)
            existente = (await db.execute(stmt_isbn)).scalar_one_or_none()
            if existente is not None and existente.id != libro_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El ISBN '{nuevo_isbn}' ya se encuentra registrado",
                )
        libro.isbn = nuevo_isbn

    if "precio" in fields_set:
        if libro_in.precio is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El precio del libro no puede ser nulo",
            )
        libro.precio = libro_in.precio

    if "stock" in fields_set:
        if libro_in.stock is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El stock del libro no puede ser nulo",
            )
        libro.stock = libro_in.stock

    if "editorial_id" in fields_set:
        if libro_in.editorial_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La editorial del libro no puede ser nula",
            )
        stmt_ed = select(Editorial).where(Editorial.id == libro_in.editorial_id)
        editorial = (await db.execute(stmt_ed)).scalar_one_or_none()
        if not editorial:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"La editorial con ID {libro_in.editorial_id} no existe",
            )
        libro.editorial_id = libro_in.editorial_id
        libro.editorial = editorial

    if "genero_id" in fields_set:
        if libro_in.genero_id is None:
            libro.genero_id = None
            libro.genero = None
        else:
            stmt_gen = select(Genero).where(Genero.id == libro_in.genero_id)
            genero = (await db.execute(stmt_gen)).scalar_one_or_none()
            if not genero:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"El género con ID {libro_in.genero_id} no existe",
                )
            libro.genero_id = libro_in.genero_id
            libro.genero = genero

    try:
        await db.commit()
        await db.refresh(libro)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflicto de integridad al actualizar el libro: {exc.orig}",
        ) from exc

    return _build_libro_detail_response(libro)
