"""parcial_schema

Revision ID: 003
Revises: 002
Create Date: 2026-11-04 00:00:00.000000

"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Tablas de usuarios y seguridad
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("debe_cambiar_password", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuario")),
    )
    op.create_index(op.f("ix_usuario_email"), "usuario", ["email"], unique=True)

    op.create_table(
        "asignacion_rol",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("desde", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("vence_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("otorgada_por", sa.Integer(), nullable=True),
        sa.CheckConstraint("rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')", name=op.f("ck_asignacion_rol_rol_valido")),
        sa.ForeignKeyConstraint(["otorgada_por"], ["usuario.id"], name=op.f("fk_asignacion_rol_otorgada_por_usuario")),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], name=op.f("fk_asignacion_rol_usuario_id_usuario")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asignacion_rol")),
    )
    op.create_index(
        "ix_asignacion_rol_usuario_rol_activa",
        "asignacion_rol",
        ["usuario_id", "rol"],
        unique=True,
        postgresql_where=sa.text("revocada_en IS NULL"),
    )

    op.create_table(
        "intento_acceso",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cuando", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("ip", sa.String(length=50), nullable=False),
        sa.Column("exito", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_intento_acceso")),
    )
    op.create_index("ix_intento_acceso_email_ip_cuando", "intento_acceso", ["email", "ip", "cuando"])

    op.create_table(
        "evento_seguridad",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cuando", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("accion", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evento_seguridad")),
    )

    # 2. Tablas de catálogo
    op.create_table(
        "autor",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("biografia", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_autor")),
    )

    op.create_table(
        "editorial",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_editorial")),
    )

    op.create_table(
        "genero",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_genero")),
    )

    op.create_table(
        "libro",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("isbn", sa.String(length=30), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("precio", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("stock", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("autor_id", sa.Integer(), nullable=False),
        sa.Column("editorial_id", sa.Integer(), nullable=False),
        sa.Column("genero_id", sa.Integer(), nullable=False),
        sa.Column("borrado_en", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["autor_id"], ["autor.id"], name=op.f("fk_libro_autor_id_autor")),
        sa.ForeignKeyConstraint(["editorial_id"], ["editorial.id"], name=op.f("fk_libro_editorial_id_editorial")),
        sa.ForeignKeyConstraint(["genero_id"], ["genero.id"], name=op.f("fk_libro_genero_id_genero")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_libro")),
    )
    op.create_index(
        "ix_libro_isbn_activo",
        "libro",
        ["isbn"],
        unique=True,
        postgresql_where=sa.text("borrado_en IS NULL"),
    )

    # 3. Tablas de clientes y ventas
    op.create_table(
        "cliente",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("telefono", sa.String(length=50), nullable=True),
        sa.Column("direccion", sa.String(length=200), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], name=op.f("fk_cliente_usuario_id_usuario")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cliente")),
    )
    op.create_index(op.f("ix_cliente_usuario_id"), "cliente", ["usuario_id"], unique=True)

    op.create_table(
        "venta",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["cliente.id"], name=op.f("fk_venta_cliente_id_cliente")),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], name=op.f("fk_venta_usuario_id_usuario")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_venta")),
    )

    op.create_table(
        "detalle_venta",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("venta_id", sa.Integer(), nullable=False),
        sa.Column("libro_id", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint("cantidad > 0", name=op.f("ck_detalle_venta_cantidad_positiva")),
        sa.ForeignKeyConstraint(["libro_id"], ["libro.id"], name=op.f("fk_detalle_venta_libro_id_libro")),
        sa.ForeignKeyConstraint(["venta_id"], ["venta.id"], name=op.f("fk_detalle_venta_venta_id_venta")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_detalle_venta")),
    )

    op.create_table(
        "movimiento_stock",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("libro_id", sa.Integer(), nullable=False),
        sa.Column("venta_id", sa.Integer(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(length=50), nullable=False),
        sa.Column("cuando", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("cantidad <> 0", name=op.f("ck_movimiento_stock_cantidad_no_cero")),
        sa.ForeignKeyConstraint(["libro_id"], ["libro.id"], name=op.f("fk_movimiento_stock_libro_id_libro")),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], name=op.f("fk_movimiento_stock_usuario_id_usuario")),
        sa.ForeignKeyConstraint(["venta_id"], ["venta.id"], name=op.f("fk_movimiento_stock_venta_id_venta")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_movimiento_stock")),
    )


def downgrade() -> None:
    op.drop_table("movimiento_stock")
    op.drop_table("detalle_venta")
    op.drop_table("venta")
    op.drop_index(op.f("ix_cliente_usuario_id"), table_name="cliente")
    op.drop_table("cliente")
    op.drop_index("ix_libro_isbn_activo", table_name="libro")
    op.drop_table("libro")
    op.drop_table("genero")
    op.drop_table("editorial")
    op.drop_table("autor")
    op.drop_table("evento_seguridad")
    op.drop_index("ix_intento_acceso_email_ip_cuando", table_name="intento_acceso")
    op.drop_table("intento_acceso")
    op.drop_index("ix_asignacion_rol_usuario_rol_activa", table_name="asignacion_rol")
    op.drop_table("asignacion_rol")
    op.drop_index(op.f("ix_usuario_email"), table_name="usuario")
    op.drop_table("usuario")
