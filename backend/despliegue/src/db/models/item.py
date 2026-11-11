from sqlalchemy import Float, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.db.models.base import AuditMixin


class Item(Base, AuditMixin):
    """Domain model representing a saleable or inventory item."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("stock", 0)
        kwargs.setdefault("description", None)
        super().__init__(**kwargs)
