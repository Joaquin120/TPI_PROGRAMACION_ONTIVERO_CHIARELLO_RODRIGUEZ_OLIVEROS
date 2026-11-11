from datetime import datetime

from sqlalchemy import Boolean, DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class TimestampMixin:
    """Mixin that provides timezone-aware created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AuditMixin(TimestampMixin):
    """Mixin that extends TimestampMixin with an active status flag."""

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
