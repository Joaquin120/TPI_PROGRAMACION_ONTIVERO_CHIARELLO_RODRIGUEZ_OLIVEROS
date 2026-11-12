from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class LibroAutor(Base):
    __tablename__ = "libros_autores"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('autor', 'coautor', 'traductor', 'ilustrador')",
            name="ck_libros_autores_rol",
        ),
    )

    libro_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("libros.id", ondelete="CASCADE"),
        primary_key=True,
    )
    autor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("autores.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    rol: Mapped[str] = mapped_column(String(32), nullable=False, default="autor")
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    libro: Mapped["Libro"] = relationship("Libro", back_populates="autores_asociados")
    autor: Mapped["Autor"] = relationship("Autor", back_populates="libros_asociados")

