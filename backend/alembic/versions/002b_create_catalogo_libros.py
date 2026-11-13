"""create_catalogo_libros

Revision ID: 002b
Revises: 002
Create Date: 2026-11-13 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002b"
down_revision: str | Sequence[str] | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: create editoriales, generos, autores, libros and libros_autores tables."""
    op.create_table(
        "editoriales",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_editoriales")),
        sa.UniqueConstraint("nombre", name=op.f("uq_editoriales_nombre")),
    )

    op.create_table(
        "generos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generos")),
        sa.UniqueConstraint("nombre", name=op.f("uq_generos_nombre")),
    )

    op.create_table(
        "autores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=128), nullable=False),
        sa.Column("biografia", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_autores")),
    )

    op.create_table(
        "libros",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("isbn", sa.String(length=32), nullable=False),
        sa.Column("precio", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("stock", sa.Integer(), server_default="0", nullable=False),
        sa.Column("editorial_id", sa.Integer(), nullable=False),
        sa.Column("genero_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("precio > 0", name="ck_libros_precio_positivo"),
        sa.CheckConstraint("stock >= 0", name="ck_libros_stock_no_negativo"),
        sa.ForeignKeyConstraint(
            ["editorial_id"],
            ["editoriales.id"],
            name=op.f("fk_libros_editorial_id_editoriales"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["genero_id"],
            ["generos.id"],
            name=op.f("fk_libros_genero_id_generos"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_libros")),
    )
    op.create_index(op.f("ix_libros_titulo"), "libros", ["titulo"], unique=False)
    op.create_index(op.f("ix_libros_isbn"), "libros", ["isbn"], unique=True)

    op.create_table(
        "libros_autores",
        sa.Column("libro_id", sa.Integer(), nullable=False),
        sa.Column("autor_id", sa.Integer(), nullable=False),
        sa.Column("rol", sa.String(length=32), server_default="autor", nullable=False),
        sa.Column("orden", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint(
            "rol IN ('autor', 'coautor', 'traductor', 'ilustrador')",
            name="ck_libros_autores_rol",
        ),
        sa.ForeignKeyConstraint(
            ["autor_id"],
            ["autores.id"],
            name=op.f("fk_libros_autores_autor_id_autores"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["libro_id"],
            ["libros.id"],
            name=op.f("fk_libros_autores_libro_id_libros"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("libro_id", "autor_id", name=op.f("pk_libros_autores")),
    )


def downgrade() -> None:
    """Downgrade schema: drop libros_autores, libros, autores, generos and editoriales tables."""
    op.drop_table("libros_autores")
    op.drop_index(op.f("ix_libros_isbn"), table_name="libros")
    op.drop_index(op.f("ix_libros_titulo"), table_name="libros")
    op.drop_table("libros")
    op.drop_table("autores")
    op.drop_table("generos")
    op.drop_table("editoriales")
