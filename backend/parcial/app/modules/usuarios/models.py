from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from parcial.app.core.base import Base

if TYPE_CHECKING:
    from parcial.app.modules.clientes.models import Cliente


class Usuario(Base):
    """User account entity with dynamic role management and password expiration flags."""

    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    debe_cambiar_password: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )

    # Relationships
    roles: Mapped[list["AsignacionRol"]] = relationship(
        "AsignacionRol",
        back_populates="usuario",
        foreign_keys="[AsignacionRol.usuario_id]",
        cascade="all, delete-orphan",
    )
    cliente: Mapped["Cliente | None"] = relationship(
        "Cliente",
        back_populates="usuario",
        uselist=False,
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("activo", True)
        kwargs.setdefault("debe_cambiar_password", False)
        super().__init__(**kwargs)


class AsignacionRol(Base):
    """Dynamic role assignment with validity windows and conditional uniqueness."""

    __tablename__ = "asignacion_rol"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuario.id"), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    desde: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    vence_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    otorgada_por: Mapped[int | None] = mapped_column(Integer, ForeignKey("usuario.id"), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')",
            name="ck_asignacion_rol_rol_valido",
        ),
        Index(
            "ix_asignacion_rol_usuario_rol_activa",
            "usuario_id",
            "rol",
            unique=True,
            postgresql_where=text("revocada_en IS NULL"),
        ),
    )

    # Relationships
    usuario: Mapped["Usuario"] = relationship(
        "Usuario",
        foreign_keys=[usuario_id],
        back_populates="roles",
    )
    otorgador: Mapped["Usuario | None"] = relationship(
        "Usuario",
        foreign_keys=[otorgada_por],
    )


class IntentoAcceso(Base):
    """Audit log for login attempts with compound index for 60-second rate limiting."""

    __tablename__ = "intento_acceso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cuando: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    ip: Mapped[str] = mapped_column(String(50), nullable=False)
    exito: Mapped[bool] = mapped_column(Boolean, nullable=False)

    __table_args__ = (
        Index("ix_intento_acceso_email_ip_cuando", "email", "ip", "cuando"),
    )


class EventoSeguridad(Base):
    """Audit log for critical security events."""

    __tablename__ = "evento_seguridad"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cuando: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    accion: Mapped[str] = mapped_column(String(255), nullable=False)
