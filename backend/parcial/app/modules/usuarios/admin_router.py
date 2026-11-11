"""Administrative routes for staff and role management (protected group)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.database import get_session
from parcial.app.core.dependencies import get_usuario_actual, requiere_rol
from parcial.app.core.paginacion import PaginationParams, PaginatedResponse, crear_respuesta_paginada
from parcial.app.core.security import hash_password
from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.usuarios.models import Usuario
from parcial.app.modules.usuarios.repository import EventoSeguridadRepository
from parcial.app.modules.usuarios.responses import usuario_con_roles
from parcial.app.modules.usuarios.schemas import (
    AsignacionRolResponse,
    EventoSeguridadResponse,
    RolAsignacionRequest,
    UsuarioConRolesResponse,
    UsuarioCreateRequest,
)
from parcial.app.modules.usuarios.service import (
    asignar_rol as asignar_rol_service,
    crear_personal,
    listar_asignaciones,
    revocar_rol as revocar_rol_service,
)

solo_admin = requiere_rol("ADMIN")

admin_router = APIRouter(
    prefix="/usuarios",
    tags=["Administración"],
    dependencies=[Depends(solo_admin)],
)


@admin_router.post(
    "",
    response_model=UsuarioConRolesResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_usuario(
    payload: UsuarioCreateRequest,
    admin: Usuario = Depends(get_usuario_actual),
    session: AsyncSession = Depends(get_session),
) -> UsuarioConRolesResponse:
    """Creates a staff user with a temporary password and a staff role."""
    password_hash = await hash_password(payload.password)

    async with UnitOfWork(session) as uow:
        usuario, roles = await crear_personal(
            uow,
            email=payload.email,
            nombre=payload.nombre,
            password_hash=password_hash,
            rol=payload.rol,
            otorgada_por=admin.id,
            actor=admin.email,
        )
        return usuario_con_roles(usuario, roles)


@admin_router.get(
    "/{usuario_id}/roles",
    response_model=PaginatedResponse[AsignacionRolResponse],
)
async def listar_roles(
    usuario_id: int,
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[AsignacionRolResponse]:
    """Lists a user's role assignments using the standard pagination envelope."""
    async with UnitOfWork(session) as uow:
        items, total = await listar_asignaciones(
            uow,
            usuario_id=usuario_id,
            skip=pagination.skip,
            limit=pagination.size,
        )

    return crear_respuesta_paginada(
        [AsignacionRolResponse.model_validate(asignacion) for asignacion in items],
        total,
        pagination.page,
        pagination.size,
    )


@admin_router.post(
    "/{usuario_id}/roles",
    response_model=AsignacionRolResponse,
    status_code=status.HTTP_201_CREATED,
)
async def asignar_rol(
    usuario_id: int,
    payload: RolAsignacionRequest,
    admin: Usuario = Depends(get_usuario_actual),
    session: AsyncSession = Depends(get_session),
) -> AsignacionRolResponse:
    """Grants a role with a required future, timezone-aware expiration."""
    async with UnitOfWork(session) as uow:
        asignacion = await asignar_rol_service(
            uow,
            usuario_id=usuario_id,
            rol=payload.rol,
            vence_en=payload.vence_en,
            otorgada_por=admin.id,
            actor=admin.email,
        )
        return AsignacionRolResponse.model_validate(asignacion)


@admin_router.delete(
    "/{usuario_id}/roles/{rol}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revocar_rol(
    usuario_id: int,
    rol: str,
    admin: Usuario = Depends(get_usuario_actual),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Revokes a live role assignment, protecting the last active administrator."""
    async with UnitOfWork(session) as uow:
        await revocar_rol_service(
            uow,
            usuario_id=usuario_id,
            rol=rol,
            actor_id=admin.id,
            actor_email=admin.email,
        )


eventos_router = APIRouter(
    prefix="/eventos",
    tags=["Administración"],
    dependencies=[Depends(solo_admin)],
)


@eventos_router.get(
    "",
    response_model=PaginatedResponse[EventoSeguridadResponse],
)
async def listar_eventos(
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[EventoSeguridadResponse]:
    """Lists security audit events using the standard pagination envelope."""
    async with UnitOfWork(session) as uow:
        repo = EventoSeguridadRepository(uow.session)
        items = await repo.listar(skip=pagination.skip, limit=pagination.size)
        total = await repo.contar()

    return crear_respuesta_paginada(
        [EventoSeguridadResponse.model_validate(evento) for evento in items],
        total,
        pagination.page,
        pagination.size,
    )


