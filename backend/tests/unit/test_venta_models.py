import pytest
from sqlalchemy import Float, ForeignKey, Integer, Numeric, String

from src.db.base import Base
from src.db.models.venta import Venta
from src.db.models.venta_renglon import VentaRenglon


def test_venta_model_table_definition() -> None:
    """Verifies table schema for 'ventas' (id PK, cliente_id FK, fecha, total)."""
    table = Venta.__table__
    assert table.name == "ventas"

    columns = {c.name: c for c in table.columns}
    assert "id" in columns
    assert columns["id"].primary_key is True
    assert isinstance(columns["id"].type, Integer)

    assert "cliente_id" in columns
    assert columns["cliente_id"].nullable is False
    assert isinstance(columns["cliente_id"].type, Integer)

    assert "fecha" in columns
    assert columns["fecha"].nullable is False

    assert "total" in columns
    assert columns["total"].nullable is False
    assert isinstance(columns["total"].type, (Numeric, Float))


def test_venta_renglon_model_table_definition() -> None:
    """Verifies table schema for 'ventas_renglones' (id PK, venta_id FK, libro_id FK, cantidad, precio_unitario, subtotal)."""
    table = VentaRenglon.__table__
    assert table.name == "ventas_renglones"

    columns = {c.name: c for c in table.columns}
    assert "id" in columns
    assert columns["id"].primary_key is True
    assert isinstance(columns["id"].type, Integer)

    assert "venta_id" in columns
    assert columns["venta_id"].nullable is False

    assert "libro_id" in columns
    assert columns["libro_id"].nullable is False

    assert "cantidad" in columns
    assert columns["cantidad"].nullable is False
    assert isinstance(columns["cantidad"].type, Integer)

    assert "precio_unitario" in columns
    assert columns["precio_unitario"].nullable is False

    assert "subtotal" in columns
    assert columns["subtotal"].nullable is False


def test_ventas_registered_in_base_metadata() -> None:
    """Verifies that 'ventas' and 'ventas_renglones' tables are registered in Base.metadata.tables."""
    assert "ventas" in Base.metadata.tables
    assert "ventas_renglones" in Base.metadata.tables
