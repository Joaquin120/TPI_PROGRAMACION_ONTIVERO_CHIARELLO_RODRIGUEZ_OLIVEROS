"""Authentication and user administration services.

Services receive a ``UnitOfWork`` (never a raw session) so the router keeps the
transaction boundary while repositories stay free of commits.
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.core.security import crear_token_acceso, verify_password
from parcial.app.core.unit_of_work import UnitOfWork
from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.usuarios.models import AsignacionRol, Usuario
from parcial.app.modules.usuarios.repository import (
    AsignacionRolRepository,
    EventoSeguridadRepository,
    IntentoAccesoRepository,
    UsuarioRepository,
    registrar_intento_acceso_aislado,
)

EMAIL_DUPLICADO = "El email ya está registrado"
CREDENCIALES_INVALIDAS = "Credenciales inválidas"
DEMASIADOS_INTENTOS = "Demasiados intentos fallidos, intente más tarde"
MAX_FALLOS_LOGIN = 5
VENTANA_RATE_LIMIT_SEGUNDOS = 60
ACCION_PASSWORD_CAMBIADO = "PASSWORD_CAMBIADO"
ACCION_USUARIO_CREADO = "USUARIO_CREADO"
ACCION_ROL_ASIGNADO = "ROL_ASIGNADO"
ACCION_ROL_REVOCADO = "ROL_REVOCADO"
USUARIO_INEXISTENTE = "Usuario no encontrado"
ASIGNACION_DUPLICADA = "El usuario ya tiene una asignación activa de ese rol"
ASIGNACION_NO_ENCONTRADA = "No se encontró una asignación activa del rol para el usuario"
AUTO_REVOCACION_PROHIBIDA = "No puede auto-revocarse el rol de administrador"
ULTIMO_ADMIN_PROHIBIDO = "No se puede revocar el último administrador del sistema"


async def registrar_cliente(
    uow: UnitOfWork,
    *,
    email: str,
    nombre: str,
    password_hash: str,
) -> tuple[Usuario, list[str]]:
    """Creates user, CLIENTE assignment and customer record in one transaction."""
    usuarios = UsuarioRepository(uow.session)
    if await usuarios.get_by_email(email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=EMAIL_DUPLICADO,
        )

    usuario = Usuario(email=email, nombre=nombre, password_hash=password_hash)
    try:
        await usuarios.add(usuario)
        uow.session.add(AsignacionRol(usuario_id=usuario.id, rol="CLIENTE"))
        uow.session.add(
            Cliente(nombre=nombre, email=email, usuario_id=usuario.id)
        )
        await uow.session.flush()
    except IntegrityError:
        # Covers the race where a concurrent request inserted the same email
        # or the same active role between the existence check and the flush.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=EMAIL_DUPLICADO,
        ) from None

    return usuario, ["CLIENTE"]


async def autenticar(
    uow: UnitOfWork,
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    fictitious_password_hash: str,
    email: str,
    password: str,
    ip: str,
) -> tuple[Usuario, list[str], str]:
    """Authenticates credentials following the mandatory evaluation order.

    Order matters (design decision #3): the rate limit is checked *before*
    bcrypt so a blocked caller cannot force CPU work; unknown emails are still
    verified against a fictitious hash so response timing does not reveal
    whether the account exists; the attempt is persisted in an isolated
    transaction so it survives the rollback raised by a failed login.
    """
    intentos = IntentoAccesoRepository(uow.session)
    fallos = await intentos.contar_fallos_recientes(
        email,
        ip,
        VENTANA_RATE_LIMIT_SEGUNDOS,
    )
    if fallos >= MAX_FALLOS_LOGIN:
        await registrar_intento_acceso_aislado(
            sessionmaker,
            email=email,
            ip=ip,
            exito=False,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=DEMASIADOS_INTENTOS,
            headers={"Retry-After": str(VENTANA_RATE_LIMIT_SEGUNDOS)},
        )

    usuarios = UsuarioRepository(uow.session)
    usuario = await usuarios.get_by_email(email)
    hash_a_verificar = (
        usuario.password_hash if usuario is not None else fictitious_password_hash
    )
    credenciales_validas = await verify_password(password, hash_a_verificar)
    exito = bool(
        usuario is not None
        and usuario.activo
        and credenciales_validas
    )
    await registrar_intento_acceso_aislado(
        sessionmaker,
        email=email,
        ip=ip,
        exito=exito,
    )
    if not exito:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=CREDENCIALES_INVALIDAS,
        )

    roles = await usuarios.get_roles_vigentes(usuario.id)
    token = crear_token_acceso(usuario.id, usuario.email, roles)
    return usuario, roles, token


async def cambiar_password(
    uow: UnitOfWork,
    *,
    usuario: Usuario,
    password_hash_nuevo: str,
) -> None:
    """Rotates the password, clears the pending flag and audits in the same UoW."""
    usuario.password_hash = password_hash_nuevo
    usuario.debe_cambiar_password = False
    await uow.session.flush()
    await EventoSeguridadRepository(uow.session).registrar(
        actor=usuario.email,
        accion=ACCION_PASSWORD_CAMBIADO,
    )


async def crear_personal(
    uow: UnitOfWork,
    *,
    email: str,
    nombre: str,
    password_hash: str,
    rol: str,
    otorgada_por: int,
    actor: str,
) -> tuple[Usuario, list[str]]:
    """Creates a staff account with a temporary password and audits the action."""
    usuarios = UsuarioRepository(uow.session)
    if await usuarios.get_by_email(email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=EMAIL_DUPLICADO,
        )

    usuario = Usuario(
        email=email,
        nombre=nombre,
        password_hash=password_hash,
        activo=True,
        debe_cambiar_password=True,
    )
    try:
        await usuarios.add(usuario)
        uow.session.add(
            AsignacionRol(
                usuario_id=usuario.id,
                rol=rol,
                otorgada_por=otorgada_por,
            )
        )
        await uow.session.flush()
        await EventoSeguridadRepository(uow.session).registrar(
            actor=actor,
            accion=ACCION_USUARIO_CREADO,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=EMAIL_DUPLICADO,
        ) from None

    return usuario, [rol]


async def _obtener_usuario(uow: UnitOfWork, usuario_id: int) -> Usuario:
    """Loads a user or raises HTTP 404, shared by the role endpoints."""
    usuario = await UsuarioRepository(uow.session).get_by_id(usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=USUARIO_INEXISTENTE,
        )
    return usuario


async def listar_asignaciones(
    uow: UnitOfWork,
    *,
    usuario_id: int,
    skip: int,
    limit: int,
) -> tuple[list[AsignacionRol], int]:
    """Lists a user's role assignments (history included) with their total."""
    await _obtener_usuario(uow, usuario_id)
    asignaciones = AsignacionRolRepository(uow.session)
    items = await asignaciones.listar_por_usuario(usuario_id, skip=skip, limit=limit)
    total = await asignaciones.contar_por_usuario(usuario_id)
    return list(items), total


async def asignar_rol(
    uow: UnitOfWork,
    *,
    usuario_id: int,
    rol: str,
    vence_en: datetime,
    otorgada_por: int,
    actor: str,
) -> AsignacionRol:
    """Grants a live role, rejecting duplicates and auditing in the same UoW."""
    await _obtener_usuario(uow, usuario_id)
    asignaciones = AsignacionRolRepository(uow.session)
    if await asignaciones.get_activa(usuario_id, rol) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ASIGNACION_DUPLICADA,
        )

    asignacion = AsignacionRol(
        usuario_id=usuario_id,
        rol=rol,
        vence_en=vence_en,
        otorgada_por=otorgada_por,
    )
    try:
        await asignaciones.add(asignacion)
    except IntegrityError:
        # Partial unique index on (usuario_id, rol) where revocada_en IS NULL.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ASIGNACION_DUPLICADA,
        ) from None

    await EventoSeguridadRepository(uow.session).registrar(
        actor=actor,
        accion=ACCION_ROL_ASIGNADO,
    )
    return asignacion


async def revocar_rol(
    uow: UnitOfWork,
    *,
    usuario_id: int,
    rol: str,
    actor_id: int,
    actor_email: str,
) -> None:
    """Revokes a user's active role assignment.

    Guards:
    1. Actor cannot revoke their own ADMIN role (HTTP 409).
    2. Must have an active assignment (HTTP 404).
    3. Revoking ADMIN locks all active ADMIN assignments with SELECT ... FOR UPDATE;
       if leaving zero active administrators, rejects with HTTP 409.
    4. Records EventoSeguridad(actor=actor_email, accion="ROL_REVOCADO") within the same UoW.
    """
    if rol == "ADMIN" and usuario_id == actor_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=AUTO_REVOCACION_PROHIBIDA,
        )

    asignaciones = AsignacionRolRepository(uow.session)
    asignacion = await asignaciones.get_activa_for_update(usuario_id, rol)
    if asignacion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ASIGNACION_NO_ENCONTRADA,
        )

    if rol == "ADMIN":
        admins_activos = await asignaciones.listar_admins_activos_for_update()
        admins_restantes = [a for a in admins_activos if a.usuario_id != usuario_id]
        if not admins_restantes:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ULTIMO_ADMIN_PROHIBIDO,
            )

    asignacion.revocada_en = datetime.now(timezone.utc)
    await uow.session.flush()
    await EventoSeguridadRepository(uow.session).registrar(
        actor=actor_email,
        accion=ACCION_ROL_REVOCADO,
    )

