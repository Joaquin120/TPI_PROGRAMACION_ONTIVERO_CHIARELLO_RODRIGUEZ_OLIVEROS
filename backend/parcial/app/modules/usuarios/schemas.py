"""Strict request/response contracts for authentication and user administration.

Crucial Rule (CONSIGNA_PARCIAL §2):
- Every input model forbids unexpected fields (``extra="forbid"``), so FastAPI
  answers HTTP 422 instead of silently ignoring caller mistakes.
- Passwords are limited by UTF-8 byte length, not character count, because
  bcrypt rejects payloads above 72 bytes. Validating here keeps that failure a
  deterministic 422 instead of a 500 raised from the hashing layer.
"""

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

from parcial.app.core.security import MAX_PASSWORD_BYTES

RolAsignable = Literal["ADMIN", "VENDEDOR", "CLIENTE"]
RolPersonal = Literal["ADMIN", "VENDEDOR"]


def _validar_longitud_password(valor: str) -> str:
    """Rejects passwords whose UTF-8 encoding exceeds bcrypt's 72-byte limit."""
    if len(valor.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"La contraseña no puede superar los {MAX_PASSWORD_BYTES} bytes en UTF-8"
        )
    return valor


PasswordPlano = Annotated[
    str,
    Field(min_length=1),
    AfterValidator(_validar_longitud_password),
]
EmailStr = Annotated[str, Field(min_length=3, max_length=255)]
NombreStr = Annotated[str, Field(min_length=1, max_length=100)]


class StrictModel(BaseModel):
    """Base model rejecting undeclared fields."""

    model_config = ConfigDict(extra="forbid")


class RegistroRequest(StrictModel):
    """Public self-registration payload (always assigns the CLIENTE role)."""

    email: EmailStr
    nombre: NombreStr
    password: PasswordPlano


class LoginRequest(StrictModel):
    """Credential payload for session creation."""

    email: EmailStr
    password: PasswordPlano


class CambiarPasswordRequest(StrictModel):
    """Password rotation payload for the authenticated user."""

    password_actual: PasswordPlano
    password_nueva: PasswordPlano


class UsuarioCreateRequest(StrictModel):
    """Staff creation payload restricted to administrative roles."""

    email: EmailStr
    nombre: NombreStr
    password: PasswordPlano
    rol: RolPersonal


class RolAsignacionRequest(StrictModel):
    """Role assignment payload requiring an aware, future expiration date."""

    rol: RolAsignable
    vence_en: datetime

    @field_validator("vence_en")
    @classmethod
    def validar_vigencia(cls, valor: datetime) -> datetime:
        if valor.tzinfo is None or valor.tzinfo.utcoffset(valor) is None:
            raise ValueError("vence_en debe incluir información de zona horaria")
        if valor <= datetime.now(timezone.utc):
            raise ValueError("vence_en debe ser una fecha futura")
        return valor


class UsuarioResponse(StrictModel):
    """Public user projection: never exposes ``password_hash``."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    email: str
    nombre: str
    activo: bool
    debe_cambiar_password: bool


class UsuarioConRolesResponse(UsuarioResponse):
    """Public user projection with the informational role names."""

    roles: list[str]


class AsignacionRolResponse(StrictModel):
    """Role assignment projection."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    usuario_id: int
    rol: str
    desde: datetime
    vence_en: datetime | None
    revocada_en: datetime | None
    otorgada_por: int | None


class EventoSeguridadResponse(StrictModel):
    """Security audit event projection."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    cuando: datetime
    actor: str
    accion: str


class AuthYoResponse(StrictModel):
    """Authenticated identity, live roles from the database, and token roles."""

    usuario: UsuarioResponse
    roles_vigentes: list[str]
    roles_token: list[str]
