from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from parcial.app.core.base import Base

if TYPE_CHECKING:
    from parcial.app.modules.usuarios.models import Usuario
    from parcial.app.modules.ventas.models import Venta


class Autor(Base):
    """Author entity for book cataloging."""

    __tablename__ = "autor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    biografia: Mapped[str | None] = mapped_column(String(500), nullable=True)

    libros: Mapped[list["Libro"]] = relationship("Libro", back_populates="autor")


class Editorial(Base):
    """Publisher entity for book cataloging."""

    __tablename__ = "editorial"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    libros: Mapped[list["Libro"]] = relationship("Libro", back_populates="editorial")


class Genero(Base):
    """Genre category entity for book cataloging."""

    __tablename__ = "genero"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)

    libros: Mapped[list["Libro"]] = relationship("Libro", back_populates="genero")


class Libro(Base):
    """Book entity with soft deletion and conditional ISBN uniqueness."""

    __tablename__ = "libro"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    isbn: Mapped[str] = mapped_column(String(30), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"), nullable=False)
    autor_id: Mapped[int] = mapped_column(Integer, ForeignKey("autor.id"), nullable=False)
    editorial_id: Mapped[int] = mapped_column(Integer, ForeignKey("editorial.id"), nullable=False)
    genero_id: Mapped[int] = mapped_column(Integer, ForeignKey("genero.id"), nullable=False)
    borrado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_libro_isbn_activo",
            "isbn",
            unique=True,
            postgresql_where=text("borrado_en IS NULL"),
        ),
    )

    # Relationships
    autor: Mapped["Autor"] = relationship("Autor", back_populates="libros")
    editorial: Mapped["Editorial"] = relationship("Editorial", back_populates="libros")
    genero: Mapped["Genero"] = relationship("Genero", back_populates="libros")
    movimientos: Mapped[list["MovimientoStock"]] = relationship(
        "MovimientoStock",
        back_populates="libro",
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("stock", 0)
        kwargs.setdefault("borrado_en", None)
        super().__init__(**kwargs)


class MovimientoStock(Base):
    """Append-only ledger of physical stock changes."""

    __tablename__ = "movimiento_stock"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    libro_id: Mapped[int] = mapped_column(Integer, ForeignKey("libro.id"), nullable=False)
    venta_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("venta.id"), nullable=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuario.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str] = mapped_column(String(50), nullable=False)
    cuando: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("cantidad <> 0", name="ck_movimiento_stock_cantidad_no_cero"),
    )

    # Relationships
    libro: Mapped["Libro"] = relationship("Libro", back_populates="movimientos")
    usuario: Mapped["Usuario"] = relationship("parcial.app.modules.usuarios.models.Usuario")
    venta: Mapped["Venta | None"] = relationship(
        "parcial.app.modules.ventas.models.Venta",
        back_populates="movimientos",
    )
