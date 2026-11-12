from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.autor import Autor
from src.db.session import get_db
from src.schemas.libro import AutorResponse

router = APIRouter(tags=["autores"])


@router.get(
    "/",
    response_model=list[AutorResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todos los autores",
)
async def list_autores(
    db: AsyncSession = Depends(get_db),
) -> list[AutorResponse]:
    """Retorna la lista de todos los autores registrados."""
    stmt = select(Autor).order_by(Autor.nombre.asc())
    result = await db.execute(stmt)
    autores = result.scalars().all()
    return [AutorResponse(id=a.id, nombre=a.nombre, biografia=a.biografia) for a in autores]


@router.get(
    "/{autor_id}",
    response_model=AutorResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener un autor por ID",
)
async def get_autor(
    autor_id: int,
    db: AsyncSession = Depends(get_db),
) -> AutorResponse:
    """Retorna la información de un autor específico o 404 si no existe."""
    stmt = select(Autor).where(Autor.id == autor_id)
    result = await db.execute(stmt)
    autor = result.scalar_one_or_none()
    if autor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Autor con ID {autor_id} no encontrado",
        )
    return AutorResponse(id=autor.id, nombre=autor.nombre, biografia=autor.biografia)

