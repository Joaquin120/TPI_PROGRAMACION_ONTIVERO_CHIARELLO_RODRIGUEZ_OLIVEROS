"""HTTP routes for customer management and profile linking."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.database import get_session
from parcial.app.core.dependencies import get_usuario_actual, requiere_rol
from parcial.app.core.paginacion import PaginatedResponse, PaginationParams
from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.clientes.schemas import (
    ClienteCreateRequest,
    ClienteResponse,
    ClienteUpdateRequest,
)
from parcial.app.modules.clientes.service import ClienteService
from parcial.app.modules.usuarios.models import Usuario
from parcial.app.modules.ventas.schemas import VentaResponse

clientes_router = APIRouter(prefix="/clientes", tags=["Gestión de Clientes"])
cliente_service = ClienteService()


@clientes_router.post(
    "",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_rol("ADMIN", "VENDEDOR"))],
)
async def create_cliente(
    datos: ClienteCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> ClienteResponse:
    """Creates a new customer record (staff only)."""
    async with UnitOfWork(session) as uow:
        return await cliente_service.crear_cliente(datos, uow)


@clientes_router.get(
    "",
    response_model=PaginatedResponse[ClienteResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(requiere_rol("ADMIN", "VENDEDOR"))],
)
async def get_clientes(
    pagination: Annotated[PaginationParams, Depends()],
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[ClienteResponse]:
    """Returns paginated customer directory (staff only)."""
    async with UnitOfWork(session) as uow:
        return await cliente_service.listar_clientes_paginado(pagination, uow)


@clientes_router.get(
    "/{id}",
    response_model=ClienteResponse,
    status_code=status.HTTP_200_OK,
)
async def get_cliente_by_id(
    id: int,
    usuario_actual: Annotated[Usuario, Depends(get_usuario_actual)],
    session: AsyncSession = Depends(get_session),
) -> ClienteResponse:
    """Returns customer details if staff or the account owner."""
    async with UnitOfWork(session) as uow:
        cliente = await cliente_service.obtener_cliente_por_id(id, uow)

    roles_vigentes = {r.rol for r in usuario_actual.roles if r.es_vigente}
    es_personal = bool(roles_vigentes & {"ADMIN", "VENDEDOR"})
    es_titular = (cliente.usuario_id == usuario_actual.id)

    if not (es_personal or es_titular):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado a la ficha de cliente solicitada",
        )
    return cliente


@clientes_router.patch(
    "/{id}",
    response_model=ClienteResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(requiere_rol("ADMIN", "VENDEDOR"))],
)
async def update_cliente(
    id: int,
    datos: ClienteUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> ClienteResponse:
    """Partially updates customer details (staff only)."""
    async with UnitOfWork(session) as uow:
        return await cliente_service.actualizar_cliente(id, datos, uow)


@clientes_router.post(
    "/{id}/perfil",
    response_model=ClienteResponse,
    status_code=status.HTTP_200_OK,
)
async def link_customer_profile(
    id: int,
    usuario_actual: Annotated[Usuario, Depends(get_usuario_actual)],
    session: AsyncSession = Depends(get_session),
) -> ClienteResponse:
    """Links the authenticated user account to an unassigned customer profile."""
    async with UnitOfWork(session) as uow:
        return await cliente_service.vincular_perfil(id, usuario_actual.id, uow)


@clientes_router.get(
    "/{id}/ventas",
    response_model=PaginatedResponse[VentaResponse],
    status_code=status.HTTP_200_OK,
)
async def get_cliente_ventas(
    id: int,
    pagination: Annotated[PaginationParams, Depends()],
    usuario_actual: Annotated[Usuario, Depends(get_usuario_actual)],
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[VentaResponse]:
    """Returns paginated sales history for a customer if staff or the account owner."""
    async with UnitOfWork(session) as uow:
        cliente = await cliente_service.obtener_cliente_por_id(id, uow)

        roles_vigentes = {r.rol for r in usuario_actual.roles if r.es_vigente}
        es_personal = bool(roles_vigentes & {"ADMIN", "VENDEDOR"})
        es_titular = (cliente.usuario_id == usuario_actual.id)

        if not (es_personal or es_titular):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado a las ventas del cliente solicitado",
            )

        return await cliente_service.listar_ventas_cliente_paginado(id, pagination, uow)
