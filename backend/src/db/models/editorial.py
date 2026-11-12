from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Editorial(Base):
    __tablename__ = "editoriales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    libros: Mapped[list["Libro"]] = relationship("Libro", back_populates="editorial")

