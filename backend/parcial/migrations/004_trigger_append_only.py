"""trigger_append_only

Revision ID: 004
Revises: 003
Create Date: 2026-11-04 00:00:00.000000

"""
from collections.abc import Sequence
from alembic import op


revision: str = "004"
down_revision: str | Sequence[str] | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Función PL/pgSQL que rechaza UPDATE y DELETE
    op.execute("""
    CREATE OR REPLACE FUNCTION rechazar_mutacion_movimiento_stock()
    RETURNS TRIGGER AS $$
    BEGIN
        RAISE EXCEPTION 'Operación no permitida: movimiento_stock es una tabla de solo agregado (inmutable)';
    END;
    $$ LANGUAGE plpgsql;
    """)

    # 2. Trigger BEFORE UPDATE OR DELETE sobre movimiento_stock
    op.execute("""
    CREATE TRIGGER trg_movimiento_stock_solo_agregado
    BEFORE UPDATE OR DELETE ON movimiento_stock
    FOR EACH ROW
    EXECUTE FUNCTION rechazar_mutacion_movimiento_stock();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_movimiento_stock_solo_agregado ON movimiento_stock;")
    op.execute("DROP FUNCTION IF EXISTS rechazar_mutacion_movimiento_stock();")
