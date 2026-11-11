from decimal import Decimal
import pytest
from sqlalchemy import CheckConstraint, Index

from parcial.app.modules.clientes.models import Cliente
from parcial.app.modules.libros.models import (
    Autor,
    Editorial,
    Genero,
    Libro,
    MovimientoStock,
)
from parcial.app.modules.usuarios.models import (
    AsignacionRol,
    EventoSeguridad,
    IntentoAcceso,
    Usuario,
)
from parcial.app.modules.ventas.models import DetalleVenta, Venta


def test_models_table_names() -> None:
    """Verifies that all entity tables are mapped with their exact specified names."""
    assert Usuario.__tablename__ == "usuario"
    assert AsignacionRol.__tablename__ == "asignacion_rol"
    assert IntentoAcceso.__tablename__ == "intento_acceso"
    assert EventoSeguridad.__tablename__ == "evento_seguridad"
    assert Autor.__tablename__ == "autor"
    assert Editorial.__tablename__ == "editorial"
    assert Genero.__tablename__ == "genero"
    assert Libro.__tablename__ == "libro"
    assert MovimientoStock.__tablename__ == "movimiento_stock"
    assert Cliente.__tablename__ == "cliente"
    assert Venta.__tablename__ == "venta"
    assert DetalleVenta.__tablename__ == "detalle_venta"


def test_usuario_model_attributes_and_defaults() -> None:
    """Verifies Usuario model attributes, unique email index, and security defaults."""
    user = Usuario(
        id=1,
        email="admin@example.com",
        nombre="Administrador",
        password_hash="hashed_secret",
    )
    assert user.email == "admin@example.com"
    assert user.nombre == "Administrador"
    assert user.activo is True
    assert user.debe_cambiar_password is False

    table = Usuario.__table__
    assert table.c.email.unique is True or any(
        idx.unique and "email" in [c.name for c in idx.columns]
        for idx in table.indexes
    )


def test_asignacion_rol_check_and_partial_index() -> None:
    """Verifies AsignacionRol check constraint on role names and partial unique index."""
    table = AsignacionRol.__table__

    # Check constraint
    checks = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    role_check = next((c for c in checks if "ADMIN" in str(c.sqltext)), None)
    assert role_check is not None
    assert "VENDEDOR" in str(role_check.sqltext)
    assert "CLIENTE" in str(role_check.sqltext)

    # Partial index
    partial_idx = next(
        (idx for idx in table.indexes if idx.name == "ix_asignacion_rol_usuario_rol_activa"),
        None,
    )
    assert partial_idx is not None
    assert partial_idx.unique is True
    assert partial_idx.dialect_options["postgresql"]["where"] is not None
    assert "revocada_en IS NULL" in str(partial_idx.dialect_options["postgresql"]["where"])


def test_intento_acceso_compound_index() -> None:
    """Verifies IntentoAcceso compound index (email, ip, cuando) for rate limiting."""
    table = IntentoAcceso.__table__
    idx = next(
        (i for i in table.indexes if i.name == "ix_intento_acceso_email_ip_cuando"),
        None,
    )
    assert idx is not None
    col_names = [c.name for c in idx.columns]
    assert col_names == ["email", "ip", "cuando"]


def test_libro_isbn_partial_unique_index() -> None:
    """Verifies Libro partial unique index on isbn excluding soft-deleted books."""
    table = Libro.__table__
    isbn_idx = next(
        (i for i in table.indexes if i.name == "ix_libro_isbn_activo"),
        None,
    )
    assert isbn_idx is not None
    assert isbn_idx.unique is True
    assert isbn_idx.dialect_options["postgresql"]["where"] is not None
    assert "borrado_en IS NULL" in str(isbn_idx.dialect_options["postgresql"]["where"])


def test_movimiento_stock_check_constraint() -> None:
    """Verifies MovimientoStock check constraint ensuring quantity is non-zero."""
    table = MovimientoStock.__table__
    checks = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    qty_check = next((c for c in checks if "cantidad <> 0" in str(c.sqltext)), None)
    assert qty_check is not None


def test_cliente_usuario_one_to_one_relationship() -> None:
    """Verifies Cliente optional 1-to-1 foreign key to Usuario."""
    table = Cliente.__table__
    assert table.c.usuario_id.nullable is True
    assert table.c.usuario_id.unique is True or any(
        idx.unique and "usuario_id" in [c.name for c in idx.columns]
        for idx in table.indexes
    )

    # Relationship verification
    cliente = Cliente(id=1, nombre="Lucia", email="lucia@example.com")
    assert cliente.usuario is None


def test_detalle_venta_check_constraint() -> None:
    """Verifies DetalleVenta check constraint ensuring quantity is strictly positive."""
    table = DetalleVenta.__table__
    checks = [c for c in table.constraints if isinstance(c, CheckConstraint)]
    qty_check = next((c for c in checks if "cantidad > 0" in str(c.sqltext)), None)
    assert qty_check is not None
