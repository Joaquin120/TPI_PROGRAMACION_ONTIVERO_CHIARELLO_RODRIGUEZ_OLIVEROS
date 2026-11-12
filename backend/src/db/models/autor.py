from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Autor(Base):
    __tablename__ = "autores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(128), nullable=False)
    biografia: Mapped[str | None] = mapped_column(Text, nullable=True)

    libros_asociados: Mapped[list["LibroAutor"]] = relationship("LibroAutor", back_populates="autor")

