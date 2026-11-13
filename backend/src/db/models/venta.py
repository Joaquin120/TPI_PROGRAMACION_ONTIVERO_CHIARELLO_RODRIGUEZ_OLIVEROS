from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    cliente: Mapped["Cliente"] = relationship("Cliente", lazy="selectin")
    renglones: Mapped[list["VentaRenglon"]] = relationship(
        "VentaRenglon",
        back_populates="venta",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
