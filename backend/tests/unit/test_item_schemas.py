from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from src.db.models.item import Item
from src.schemas.item import (
    ItemBase,
    ItemCreate,
    ItemListResponse,
    ItemResponse,
    ItemUpdate,
)


def test_item_base_valid() -> None:
    """Verifies ItemBase instantiates with valid parameters."""
    item = ItemBase(name="Keyboard", description="Mechanical", price=99.99, stock=10)
    assert item.name == "Keyboard"
    assert item.description == "Mechanical"
    assert item.price == 99.99
    assert item.stock == 10


def test_item_create_defaults() -> None:
    """Verifies ItemCreate adopts expected defaults for optional fields."""
    item = ItemCreate(name="Mouse", price=29.50)
    assert item.name == "Mouse"
    assert item.price == 29.50
    assert item.description is None
    assert item.stock == 0
    assert item.is_active is True


def test_item_create_negative_price_raises_validation_error() -> None:
    """Verifies that negative price raises ValidationError."""
    with pytest.raises(ValidationError):
        ItemCreate(name="Monitor", price=-10.0)


def test_item_create_negative_stock_raises_validation_error() -> None:
    """Verifies that negative stock raises ValidationError."""
    with pytest.raises(ValidationError):
        ItemCreate(name="Monitor", price=150.0, stock=-1)


def test_item_create_empty_name_raises_validation_error() -> None:
    """Verifies that empty string for name raises ValidationError."""
    with pytest.raises(ValidationError):
        ItemCreate(name="", price=10.0)


def test_item_create_name_max_length_validation_error() -> None:
    """Verifies that names longer than 100 characters raise ValidationError."""
    with pytest.raises(ValidationError):
        ItemCreate(name="A" * 101, price=10.0)


def test_item_create_description_max_length_validation_error() -> None:
    """Verifies that descriptions longer than 255 characters raise ValidationError."""
    with pytest.raises(ValidationError):
        ItemCreate(name="Valid Name", price=10.0, description="D" * 256)


def test_item_update_optional_and_validation() -> None:
    """Verifies ItemUpdate fields are optional and validated when present."""
    # All fields omitted is valid
    update_empty = ItemUpdate()
    assert update_empty.model_dump(exclude_unset=True) == {}

    # Valid partial
    update_partial = ItemUpdate(price=45.0, is_active=False)
    dumped = update_partial.model_dump(exclude_unset=True)
    assert dumped == {"price": 45.0, "is_active": False}

    # Invalid negative price in update
    with pytest.raises(ValidationError):
        ItemUpdate(price=-5.0)

    # Invalid negative stock in update
    with pytest.raises(ValidationError):
        ItemUpdate(stock=-2)

    # Invalid empty name in update
    with pytest.raises(ValidationError):
        ItemUpdate(name="")


def test_item_response_from_attributes() -> None:
    """Verifies ItemResponse serializes correctly from an Item domain model instance."""
    now = datetime.now(timezone.utc)
    db_item = Item(
        name="Laptop Pro",
        description="High performance",
        price=1499.99,
        stock=5,
        is_active=True,
    )
    db_item.id = 42
    db_item.created_at = now
    db_item.updated_at = now

    response = ItemResponse.model_validate(db_item)
    assert response.id == 42
    assert response.name == "Laptop Pro"
    assert response.description == "High performance"
    assert response.price == 1499.99
    assert response.stock == 5
    assert response.is_active is True
    assert response.created_at == now
    assert response.updated_at == now


def test_item_list_response_serialization() -> None:
    """Verifies ItemListResponse correctly aggregates items with pagination metadata."""
    now = datetime.now(timezone.utc)
    item_resp = ItemResponse(
        id=1,
        name="Cable",
        description="USB-C",
        price=9.99,
        stock=100,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    list_response = ItemListResponse(
        items=[item_resp],
        total=1,
        skip=0,
        limit=10,
    )
    assert len(list_response.items) == 1
    assert list_response.total == 1
    assert list_response.skip == 0
    assert list_response.limit == 10
