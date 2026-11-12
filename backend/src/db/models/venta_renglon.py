from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class VentaRenglon(Base):
    __tablename__ = "ventas_renglones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venta_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ventas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    libro_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("libros.id"),
        nullable=False,
        index=True,
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    venta: Mapped["Venta"] = relationship("Venta", back_populates="renglones")
    libro: Mapped["Libro"] = relationship("Libro", lazy="selectin")
