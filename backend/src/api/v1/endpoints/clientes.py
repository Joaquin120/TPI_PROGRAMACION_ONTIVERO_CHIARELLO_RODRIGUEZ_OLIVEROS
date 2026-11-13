from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.cliente import Cliente
from src.db.session import get_db
from src.schemas.cliente import ClienteCreate, ClienteResponse

router = APIRouter(tags=["clientes"])


@router.post(
    "/",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo cliente",
)
async def create_cliente(
    cliente_in: ClienteCreate,
    db: AsyncSession = Depends(get_db),
) -> ClienteResponse:
    """Registra y persiste un cliente con nombre y email único (RN-CLI-01, RN-CLI-02)."""
    # 1. Comprobación previa de email único
    stmt = select(Cliente).where(Cliente.email == cliente_in.email)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El correo electrónico '{cliente_in.email}' ya se encuentra registrado",
        )

    # 2. Creación y persistencia
    cliente = Cliente(
        nombre=cliente_in.nombre,
        email=cliente_in.email,
    )
    db.add(cliente)

    try:
        await db.commit()
        await db.refresh(cliente)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El correo electrónico '{cliente_in.email}' ya se encuentra registrado",
        )

    return cliente


@router.get(
    "/{id}",
    response_model=ClienteResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar un cliente por su ID",
)
async def get_cliente_by_id(
    id: int,
    db: AsyncSession = Depends(get_db),
) -> ClienteResponse:
    """Retorna los datos de un cliente o 404 si no existe."""
    stmt = select(Cliente).where(Cliente.id == id)
    cliente = (await db.execute(stmt)).scalar_one_or_none()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {id} no encontrado",
        )
    return cliente


@router.get(
    "/",
    response_model=list[ClienteResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar clientes registrados",
)
async def list_clientes(
    db: AsyncSession = Depends(get_db),
) -> list[ClienteResponse]:
    """Retorna la lista de todos los clientes registrados."""
    stmt = select(Cliente).order_by(Cliente.id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
