import pytest
from sqlalchemy import Integer, String

from src.db.base import Base
from src.db.models.cliente import Cliente


def test_cliente_model_instantiation() -> None:
    """Verifies that a Cliente model can be instantiated with nombre and email."""
    cliente = Cliente(nombre="Juan Pérez", email="juan.perez@example.com")
    assert cliente.nombre == "Juan Pérez"
    assert cliente.email == "juan.perez@example.com"


def test_cliente_model_table_definition() -> None:
    """Verifies that Cliente table schema has id PK, nombre VARCHAR(128) and email VARCHAR(255) UNIQUE."""
    table = Cliente.__table__
    assert table.name == "clientes"

    columns = {c.name: c for c in table.columns}
    assert "id" in columns
    assert columns["id"].primary_key is True
    assert isinstance(columns["id"].type, Integer)

    assert "nombre" in columns
    assert isinstance(columns["nombre"].type, String)
    assert columns["nombre"].type.length == 128
    assert not columns["nombre"].nullable

    assert "email" in columns
    assert isinstance(columns["email"].type, String)
    assert columns["email"].type.length == 255
    assert not columns["email"].nullable
    assert columns["email"].unique is True


def test_cliente_registered_in_base_metadata() -> None:
    """Verifies that 'clientes' table is registered in Base.metadata.tables."""
    assert "clientes" in Base.metadata.tables
