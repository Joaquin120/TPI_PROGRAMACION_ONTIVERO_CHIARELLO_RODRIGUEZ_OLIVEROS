import pytest
from sqlalchemy import Float, Integer, String
from sqlalchemy.sql.elements import TextClause

from src.db.base import Base
from src.db.models.base import AuditMixin, TimestampMixin
from src.db.models.item import Item


def test_item_instantiation_defaults() -> None:
    """Verifies that an Item can be instantiated with required fields and adopts default values."""
    item = Item(name="Test Item", price=19.99)
    assert item.name == "Test Item"
    assert item.price == 19.99
    assert item.is_active is True
    assert item.stock == 0
    assert item.description is None


def test_item_instantiation_explicit_values() -> None:
    """Verifies that an Item retains explicitly provided values."""
    item = Item(
        name="Custom Item",
        price=49.50,
        description="A sample custom item",
        stock=15,
        is_active=False,
    )
    assert item.name == "Custom Item"
    assert item.price == 49.50
    assert item.description == "A sample custom item"
    assert item.stock == 15
    assert item.is_active is False


def test_models_registered_in_base_metadata() -> None:
    """Verifies that the items table is registered in Base.metadata.tables."""
    assert "items" in Base.metadata.tables
    table = Base.metadata.tables["items"]
    assert table.name == "items"


def test_item_table_columns_and_constraints() -> None:
    """Verifies table schema, columns, data types, and nullability constraints on Item.__table__."""
    table = Item.__table__
    columns = {c.name: c for c in table.columns}

    # Primary key id
    assert "id" in columns
    id_col = columns["id"]
    assert id_col.primary_key is True
    assert id_col.autoincrement is True
    assert isinstance(id_col.type, Integer)

    # Name column
    assert "name" in columns
    name_col = columns["name"]
    assert isinstance(name_col.type, String)
    assert name_col.type.length == 100
    assert not name_col.nullable
    assert name_col.index is True

    # Description column
    assert "description" in columns
    desc_col = columns["description"]
    assert isinstance(desc_col.type, String)
    assert desc_col.type.length == 255
    assert desc_col.nullable is True

    # Price column
    assert "price" in columns
    price_col = columns["price"]
    assert isinstance(price_col.type, Float)
    assert not price_col.nullable

    # Stock column
    assert "stock" in columns
    stock_col = columns["stock"]
    assert isinstance(stock_col.type, Integer)
    assert not stock_col.nullable
    assert stock_col.default is not None
    assert stock_col.default.arg == 0
    assert isinstance(stock_col.server_default.arg, TextClause)
    assert str(stock_col.server_default.arg) == "0"

    # AuditMixin is_active column
    assert "is_active" in columns
    is_active_col = columns["is_active"]
    assert not is_active_col.nullable
    assert is_active_col.default is not None
    assert is_active_col.default.arg is True
    assert isinstance(is_active_col.server_default.arg, TextClause)
    assert str(is_active_col.server_default.arg) == "true"

    # TimestampMixin created_at column
    assert "created_at" in columns
    created_col = columns["created_at"]
    assert not created_col.nullable
    assert created_col.type.timezone is True
    assert created_col.server_default is not None

    # TimestampMixin updated_at column
    assert "updated_at" in columns
    updated_col = columns["updated_at"]
    assert not updated_col.nullable
    assert updated_col.type.timezone is True
    assert updated_col.server_default is not None
    assert updated_col.onupdate is not None


def test_item_table_naming_conventions() -> None:
    """Verifies that the unified naming conventions are applied to constraints and indexes."""
    table = Item.__table__
    assert table.primary_key.name == "pk_items"

    index_names = {idx.name for idx in table.indexes}
    assert "ix_items_name" in index_names


def test_class_hierarchy_and_mixins() -> None:
    """Verifies class inheritance structure for Item and mixins."""
    assert issubclass(Item, Base)
    assert issubclass(Item, AuditMixin)
    assert issubclass(Item, TimestampMixin)
    assert issubclass(AuditMixin, TimestampMixin)
