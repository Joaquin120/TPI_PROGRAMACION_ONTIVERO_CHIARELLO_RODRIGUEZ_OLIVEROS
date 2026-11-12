"""create_ventas

Revision ID: 003
Revises: 002
Create Date: 2026-11-12 20:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | Sequence[str] | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: create ventas and ventas_renglones tables."""
    op.create_table(
        "ventas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"], name=op.f("fk_ventas_cliente_id_clientes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ventas")),
    )
    op.create_index(op.f("ix_ventas_cliente_id"), "ventas", ["cliente_id"], unique=False)

    op.create_table(
        "ventas_renglones",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("venta_id", sa.Integer(), nullable=False),
        sa.Column("libro_id", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.CheckConstraint("cantidad > 0", name=op.f("ck_ventas_renglones_cantidad_positiva")),
        sa.ForeignKeyConstraint(["libro_id"], ["libros.id"], name=op.f("fk_ventas_renglones_libro_id_libros")),
        sa.ForeignKeyConstraint(["venta_id"], ["ventas.id"], name=op.f("fk_ventas_renglones_venta_id_ventas"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ventas_renglones")),
    )
    op.create_index(op.f("ix_ventas_renglones_venta_id"), "ventas_renglones", ["venta_id"], unique=False)
    op.create_index(op.f("ix_ventas_renglones_libro_id"), "ventas_renglones", ["libro_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema: drop ventas_renglones and ventas tables."""
    op.drop_index(op.f("ix_ventas_renglones_libro_id"), table_name="ventas_renglones")
    op.drop_index(op.f("ix_ventas_renglones_venta_id"), table_name="ventas_renglones")
    op.drop_table("ventas_renglones")

    op.drop_index(op.f("ix_ventas_cliente_id"), table_name="ventas")
    op.drop_table("ventas")
