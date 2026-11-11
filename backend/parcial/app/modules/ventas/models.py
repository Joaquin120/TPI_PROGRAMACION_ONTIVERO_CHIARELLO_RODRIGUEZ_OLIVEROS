from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from parcial.app.core.base import Base

if TYPE_CHECKING:
    from parcial.app.modules.clientes.models import Cliente
    from parcial.app.modules.libros.models import Libro, MovimientoStock
    from parcial.app.modules.usuarios.models import Usuario


class Venta(Base):
    """Sale transaction header."""

    __tablename__ = "venta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("cliente.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuario.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    cliente: Mapped["Cliente"] = relationship(
        "parcial.app.modules.clientes.models.Cliente",
        back_populates="ventas",
    )
    usuario: Mapped["Usuario"] = relationship(
        "parcial.app.modules.usuarios.models.Usuario",
    )
    detalles: Mapped[list["DetalleVenta"]] = relationship(
        "DetalleVenta",
        back_populates="venta",
        cascade="all, delete-orphan",
    )
    movimientos: Mapped[list["MovimientoStock"]] = relationship(
        "parcial.app.modules.libros.models.MovimientoStock",
        back_populates="venta",
    )


class DetalleVenta(Base):
    """Line item of a sale transaction."""

    __tablename__ = "detalle_venta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venta_id: Mapped[int] = mapped_column(Integer, ForeignKey("venta.id"), nullable=False)
    libro_id: Mapped[int] = mapped_column(Integer, ForeignKey("libro.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_detalle_venta_cantidad_positiva"),
    )

    # Relationships
    venta: Mapped["Venta"] = relationship("Venta", back_populates="detalles")
    libro: Mapped["Libro"] = relationship("parcial.app.modules.libros.models.Libro")
