from decimal import Decimal
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Libro(Base):
    __tablename__ = "libros"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_libros_precio_positivo"),
        CheckConstraint("stock >= 0", name="ck_libros_stock_no_negativo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    isbn: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    editorial_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("editoriales.id", ondelete="RESTRICT"),
        nullable=False,
    )
    genero_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("generos.id", ondelete="SET NULL"),
        nullable=True,
    )

    editorial: Mapped["Editorial"] = relationship("Editorial", back_populates="libros")
    genero: Mapped["Genero | None"] = relationship("Genero", back_populates="libros")
    autores_asociados: Mapped[list["LibroAutor"]] = relationship(
        "LibroAutor",
        back_populates="libro",
        cascade="all, delete-orphan",
        order_by="LibroAutor.orden",
    )

