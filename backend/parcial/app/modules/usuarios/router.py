"""HTTP routes for authentication and user administration."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.core.config import get_settings
from parcial.app.core.database import get_session, get_sessionmaker
from parcial.app.core.dependencies import get_usuario_actual
from parcial.app.core.security import (
    ACCESS_TOKEN_COOKIE,
    hash_password,
    verify_password,
)
from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.usuarios.models import Usuario
from parcial.app.modules.usuarios.repository import UsuarioRepository
from parcial.app.modules.usuarios.responses import usuario_con_roles
from parcial.app.modules.usuarios.schemas import (
    AuthYoResponse,
    CambiarPasswordRequest,
    LoginRequest,
    RegistroRequest,
    UsuarioConRolesResponse,
    UsuarioResponse,
)
from parcial.app.modules.usuarios.service import (
    CREDENCIALES_INVALIDAS,
    autenticar,
    cambiar_password as cambiar_password_service,
    registrar_cliente,
)

auth_router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _set_access_token_cookie(response: Response, token: str) -> None:
    """Stores the JWT in the only channel the API accepts: an HttpOnly cookie."""
    settings = get_settings()
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )


@auth_router.post(
    "/registro",
    response_model=UsuarioConRolesResponse,
    status_code=status.HTTP_201_CREATED,
)
async def registro(
    payload: RegistroRequest,
    session: AsyncSession = Depends(get_session),
) -> UsuarioConRolesResponse:
    """Registers a customer atomically (user + CLIENTE role + customer record)."""
    password_hash = await hash_password(payload.password)

    async with UnitOfWork(session) as uow:
        usuario, roles = await registrar_cliente(
            uow,
            email=payload.email,
            nombre=payload.nombre,
            password_hash=password_hash,
        )
        return usuario_con_roles(usuario, roles)


@auth_router.post(
    "/login",
    response_model=UsuarioConRolesResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    sessionmaker: async_sessionmaker[AsyncSession] = Depends(get_sessionmaker),
) -> UsuarioConRolesResponse:
    """Authenticates a user and issues the session cookie (never a body token)."""
    ip = request.client.host if request.client is not None else "desconocida"

    async with UnitOfWork(session) as uow:
        usuario, roles, token = await autenticar(
            uow,
            sessionmaker=sessionmaker,
            fictitious_password_hash=request.app.state.fictitious_password_hash,
            email=payload.email,
            password=payload.password,
            ip=ip,
        )

    _set_access_token_cookie(response, token)
    return usuario_con_roles(usuario, roles)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """Clears the session cookie; idempotent and safe without a session."""
    settings = get_settings()
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
    )


@auth_router.get("/yo", response_model=AuthYoResponse)
async def yo(
    request: Request,
    usuario: Usuario = Depends(get_usuario_actual),
    session: AsyncSession = Depends(get_session),
) -> AuthYoResponse:
    """Returns the authenticated identity with live and token-informative roles."""
    roles_vigentes = await UsuarioRepository(session).get_roles_vigentes(usuario.id)
    roles_token = list(getattr(request.state, "token_roles", []))
    return AuthYoResponse(
        usuario=UsuarioResponse.model_validate(usuario),
        roles_vigentes=roles_vigentes,
        roles_token=roles_token,
    )


@auth_router.post("/cambiar-password", status_code=status.HTTP_200_OK)
async def cambiar_password(
    payload: CambiarPasswordRequest,
    usuario: Usuario = Depends(get_usuario_actual),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Rotates the authenticated user's password (allowed with a pending flag)."""
    if not await verify_password(payload.password_actual, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=CREDENCIALES_INVALIDAS,
        )

    nuevo_hash = await hash_password(payload.password_nueva)

    async with UnitOfWork(session) as uow:
        await cambiar_password_service(
            uow,
            usuario=usuario,
            password_hash_nuevo=nuevo_hash,
        )

    return {"mensaje": "Contraseña actualizada correctamente"}
