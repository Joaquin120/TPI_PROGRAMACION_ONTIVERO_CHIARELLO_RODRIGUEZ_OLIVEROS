import pytest
from pydantic import ValidationError

from src.schemas.cliente import ClienteCreate, ClienteResponse


def test_cliente_create_valid() -> None:
    """Verifies valid payload passes ClienteCreate schema."""
    data = {"nombre": "Ana Beltrán", "email": "ana.beltran@example.com"}
    schema = ClienteCreate(**data)
    assert schema.nombre == "Ana Beltrán"
    assert schema.email == "ana.beltran@example.com"


def test_cliente_create_invalid_email() -> None:
    """Verifies invalid email format raises ValidationError (RN-CLI-02)."""
    with pytest.raises(ValidationError):
        ClienteCreate(nombre="Ana Beltrán", email="not-an-email")


def test_cliente_create_empty_nombre() -> None:
    """Verifies empty nombre raises ValidationError (RN-CLI-02)."""
    with pytest.raises(ValidationError):
        ClienteCreate(nombre="   ", email="ana.beltran@example.com")


def test_cliente_response_serialization() -> None:
    """Verifies ClienteResponse serialization with id, nombre and email."""
    data = {"id": 1, "nombre": "Carlos Duarte", "email": "carlos.duarte@example.com"}
    schema = ClienteResponse(**data)
    assert schema.id == 1
    assert schema.nombre == "Carlos Duarte"
    assert schema.email == "carlos.duarte@example.com"
