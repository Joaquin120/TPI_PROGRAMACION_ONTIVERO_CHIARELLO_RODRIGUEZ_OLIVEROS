import pytest
from pydantic import ValidationError

from parcial.app.modules.clientes.schemas import (
    ClienteCreateRequest,
    ClienteResponse,
    ClienteUpdateRequest,
)


def test_cliente_create_request_accepts_valid_data() -> None:
    req = ClienteCreateRequest(
        nombre="Lucía Fernández",
        email="lucia@example.com",
        telefono="11223344",
        direccion="Av. Siempre Viva 123",
    )
    assert req.nombre == "Lucía Fernández"
    assert req.email == "lucia@example.com"
    assert req.telefono == "11223344"
    assert req.direccion == "Av. Siempre Viva 123"


def test_cliente_create_request_defaults_optional_fields() -> None:
    req = ClienteCreateRequest(
        nombre="Tomás Ríos",
        email="tomas@example.com",
    )
    assert req.telefono is None
    assert req.direccion is None


def test_cliente_create_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ClienteCreateRequest(
            nombre="Ana",
            email="ana@example.com",
            unauthorized_field="malicious",
        )


def test_cliente_create_request_rejects_empty_nombre() -> None:
    with pytest.raises(ValidationError):
        ClienteCreateRequest(
            nombre="",
            email="ana@example.com",
        )


def test_cliente_update_request_partial() -> None:
    req = ClienteUpdateRequest(telefono="99887766")
    dump = req.model_dump(exclude_unset=True)
    assert dump == {"telefono": "99887766"}


def test_cliente_update_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ClienteUpdateRequest(nombre="Nuevo", hacker="attack")


def test_cliente_response_from_attributes() -> None:
    class DummyCliente:
        id = 1
        nombre = "Lucía"
        email = "lucia@example.com"
        telefono = "1234"
        direccion = "Calle 1"
        usuario_id = 42

    res = ClienteResponse.model_validate(DummyCliente())
    assert res.id == 1
    assert res.nombre == "Lucía"
    assert res.usuario_id == 42
