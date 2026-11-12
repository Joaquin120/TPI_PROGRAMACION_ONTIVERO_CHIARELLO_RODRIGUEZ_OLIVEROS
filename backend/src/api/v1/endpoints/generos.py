from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.genero import Genero
from src.db.session import get_db
from src.schemas.libro import GeneroResponse

router = APIRouter(tags=["generos"])


@router.get(
    "/",
    response_model=list[GeneroResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todos los géneros literarios",
)
async def list_generos(
    db: AsyncSession = Depends(get_db),
) -> list[GeneroResponse]:
    """Retorna la lista de géneros literarios disponibles."""
    stmt = select(Genero).order_by(Genero.nombre.asc())
    result = await db.execute(stmt)
    generos = result.scalars().all()
    return [GeneroResponse(id=g.id, nombre=g.nombre) for g in generos]

