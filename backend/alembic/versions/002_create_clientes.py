"""create_clientes

Revision ID: 002
Revises: 001
Create Date: 2026-11-12 19:15:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | Sequence[str] | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: create clientes table."""
    op.create_table(
        "clientes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clientes")),
    )
    op.create_index(op.f("ix_clientes_email"), "clientes", ["email"], unique=True)


def downgrade() -> None:
    """Downgrade schema: drop clientes table."""
    op.drop_index(op.f("ix_clientes_email"), table_name="clientes")
    op.drop_table("clientes")
