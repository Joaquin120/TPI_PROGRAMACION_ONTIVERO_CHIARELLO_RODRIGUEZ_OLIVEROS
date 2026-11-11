from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from parcial.app.core.base import Base

if TYPE_CHECKING:
    from parcial.app.modules.usuarios.models import Usuario
    from parcial.app.modules.ventas.models import Venta


class Cliente(Base):
    """Customer entity with optional 1-to-1 relationship to a user account."""

    __tablename__ = "cliente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    usuario_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("usuario.id"),
        unique=True,
        index=True,
        nullable=True,
    )

    # Relationships
    usuario: Mapped["Usuario | None"] = relationship(
        "parcial.app.modules.usuarios.models.Usuario",
        back_populates="cliente",
    )
    ventas: Mapped[list["Venta"]] = relationship(
        "parcial.app.modules.ventas.models.Venta",
        back_populates="cliente",
    )
