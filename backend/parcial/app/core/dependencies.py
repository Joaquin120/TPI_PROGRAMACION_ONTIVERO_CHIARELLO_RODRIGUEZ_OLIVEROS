from typing import Any, Awaitable, Callable

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.database import get_session
from parcial.app.core.security import ACCESS_TOKEN_COOKIE, decodificar_token
from parcial.app.modules.usuarios.models import Usuario
from parcial.app.modules.usuarios.repository import UsuarioRepository

NO_AUTENTICADO = "No autenticado"
ACCESO_DENEGADO = "Acceso denegado"


def _no_autenticado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=NO_AUTENTICADO,
    )


async def get_usuario_actual(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Usuario:
    """Resolves the authenticated user exclusively from the session cookie.

    Crucial Rule (CONSIGNA_PARCIAL §2.4, design decision #6):
    - ``Authorization: Bearer`` is rejected even when a valid cookie is present.
    - A missing, malformed, expired or invalid token yields HTTP 401.
    - Users deactivated after the token was issued are also rejected.
    """
    if request.headers.get("authorization") is not None:
        raise _no_autenticado()

    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if token is None:
        raise _no_autenticado()

    try:
        payload: dict[str, Any] = decodificar_token(token)
        usuario_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise _no_autenticado() from None

    usuario = await UsuarioRepository(session).get_by_id(usuario_id)
    if usuario is None or not usuario.activo:
        raise _no_autenticado()

    request.state.user = usuario
    request.state.token_roles = list(payload.get("roles", []))
    return usuario


def requiere_rol(*roles: str) -> Callable[..., Awaitable[Usuario]]:
    """Builds a dependency requiring at least one live role from the database.

    Crucial Rule (CONSIGNA_PARCIAL §2.5, design decision #7):
    - Roles are queried on every request, so a revocation takes effect on the
      very next call instead of waiting for the token to expire.
    - Missing session is 401; an authenticated user without any required role
      is 403.
    """
    roles_exigidos = frozenset(roles)

    async def _verificar_rol(
        request: Request,
        usuario: Usuario = Depends(get_usuario_actual),
        session: AsyncSession = Depends(get_session),
    ) -> Usuario:
        vigentes = await UsuarioRepository(session).get_roles_vigentes(usuario.id)
        if not roles_exigidos.intersection(vigentes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ACCESO_DENEGADO,
            )
        request.state.roles_vigentes = vigentes
        return usuario

    return _verificar_rol


async def verificar_no_debe_cambiar_password(
    usuario: Usuario = Depends(get_usuario_actual),
) -> None:
    """Dependency verifying that the user is not required to change password.

    Crucial Rule (CONSIGNA_PARCIAL §2.5):
    - Resolves the session first: no cookie/token means HTTP 401.
    - If the authenticated user has debe_cambiar_password == True, raises
      HTTP 403 Forbidden.
    """
    if usuario.debe_cambiar_password is True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debe cambiar su contraseña antes de continuar",
        )
