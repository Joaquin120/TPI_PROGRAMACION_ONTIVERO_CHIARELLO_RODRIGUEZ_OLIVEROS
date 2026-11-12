from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.editorial import Editorial
from src.db.session import get_db
from src.schemas.libro import EditorialResponse

router = APIRouter(tags=["editoriales"])


@router.get(
    "/",
    response_model=list[EditorialResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todas las editoriales",
)
async def list_editoriales(
    db: AsyncSession = Depends(get_db),
) -> list[EditorialResponse]:
    """Retorna la lista de todas las editoriales ordenadas alfabéticamente."""
    stmt = select(Editorial).order_by(Editorial.nombre.asc())
    result = await db.execute(stmt)
    editoriales = result.scalars().all()
    return [EditorialResponse(id=e.id, nombre=e.nombre) for e in editoriales]

