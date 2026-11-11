"""Response assemblers shared by the authentication and administration routers."""

from parcial.app.modules.usuarios.models import Usuario
from parcial.app.modules.usuarios.schemas import UsuarioConRolesResponse


def usuario_con_roles(
    usuario: Usuario,
    roles: list[str],
) -> UsuarioConRolesResponse:
    """Projects a user entity without ever exposing ``password_hash``."""
    return UsuarioConRolesResponse(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        activo=usuario.activo,
        debe_cambiar_password=usuario.debe_cambiar_password,
        roles=roles,
    )
