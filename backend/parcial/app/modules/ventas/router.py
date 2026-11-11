"""HTTP routes for sales transactions, background receipt dispatch, and purchase history."""

from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.database import get_session
from parcial.app.core.dependencies import get_usuario_actual, requiere_rol
from parcial.app.core.paginacion import PaginatedResponse, PaginationParams
from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.usuarios.models import Usuario
from parcial.app.modules.ventas.schemas import (
    VentaCreateRequest,
    VentaDetailResponse,
    VentaResponse,
)
from parcial.app.modules.ventas.service import (
    VentaService,
    simular_notificacion_comprobante,
)

ventas_router = APIRouter(prefix="/ventas", tags=["Ventas"])
mis_ventas_router = APIRouter(tags=["Ventas del Cliente"])
venta_service = VentaService()


@ventas_router.post(
    "",
    response_model=VentaDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_rol("ADMIN", "VENDEDOR"))],
)
async def create_venta(
    datos: VentaCreateRequest,
    background_tasks: BackgroundTasks,
    usuario_actual: Annotated[Usuario, Depends(get_usuario_actual)],
    session: AsyncSession = Depends(get_session),
) -> VentaDetailResponse:
    """Records an atomic sale and dispatches receipt notification in the background."""
    async with UnitOfWork(session) as uow:
        venta = await venta_service.crear_venta(datos, usuario_actual.id, uow)

    # Enqueue background task strictly after commit
    email_destinatario = venta.cliente.email if venta.cliente else ""
    background_tasks.add_task(
        simular_notificacion_comprobante,
        venta.id,
        float(venta.total),
        email_destinatario,
    )
    return venta


@ventas_router.get(
    "",
    response_model=PaginatedResponse[VentaResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(requiere_rol("ADMIN", "VENDEDOR"))],
)
async def get_ventas(
    pagination: Annotated[PaginationParams, Depends()],
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[VentaResponse]:
    """Returns general paginated sales history (staff only)."""
    async with UnitOfWork(session) as uow:
        return await venta_service.listar_ventas_paginado(pagination, uow)


@ventas_router.get(
    "/{id}",
    response_model=VentaDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_venta_by_id(
    id: int,
    usuario_actual: Annotated[Usuario, Depends(get_usuario_actual)],
    session: AsyncSession = Depends(get_session),
) -> VentaDetailResponse:
    """Returns detailed sale without N+1 queries.

    Crucial Architectural Rule (CONSIGNA_PARCIAL §2.6):
    - NO requiere_rol on router level.
    - Ownership / staff authorization evaluated dynamically in the service layer.
    """
    async with UnitOfWork(session) as uow:
        return await venta_service.obtener_venta_por_id(id, usuario_actual, uow)


@mis_ventas_router.get(
    "/mis-ventas",
    response_model=PaginatedResponse[VentaResponse],
    status_code=status.HTTP_200_OK,
)
async def get_mis_ventas(
    pagination: Annotated[PaginationParams, Depends()],
    usuario_actual: Annotated[Usuario, Depends(get_usuario_actual)],
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[VentaResponse]:
    """Returns paginated purchases made by the authenticated customer."""
    async with UnitOfWork(session) as uow:
        return await venta_service.listar_mis_ventas(usuario_actual, pagination, uow)
