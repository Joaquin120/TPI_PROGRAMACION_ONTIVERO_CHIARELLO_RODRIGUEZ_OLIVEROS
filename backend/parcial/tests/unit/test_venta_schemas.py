from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError

from parcial.app.modules.ventas.schemas import (
    DetalleVentaResponse,
    VentaCreateRequest,
    VentaDetailResponse,
    VentaItemRequest,
    VentaResponse,
)


def test_venta_item_request_accepts_valid() -> None:
    item = VentaItemRequest(libro_id=1, cantidad=2)
    assert item.libro_id == 1
    assert item.cantidad == 2


def test_venta_item_request_rejects_negative_or_zero_quantity() -> None:
    with pytest.raises(ValidationError):
        VentaItemRequest(libro_id=1, cantidad=0)
    with pytest.raises(ValidationError):
        VentaItemRequest(libro_id=1, cantidad=-5)


def test_venta_item_request_rejects_zero_or_negative_libro_id() -> None:
    with pytest.raises(ValidationError):
        VentaItemRequest(libro_id=0, cantidad=1)
    with pytest.raises(ValidationError):
        VentaItemRequest(libro_id=-1, cantidad=1)


def test_venta_item_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        VentaItemRequest(libro_id=1, cantidad=2, extra="forbidden")


def test_venta_create_request_accepts_valid() -> None:
    req = VentaCreateRequest(
        cliente_id=5,
        items=[
            VentaItemRequest(libro_id=1, cantidad=2),
            VentaItemRequest(libro_id=2, cantidad=1),
        ],
    )
    assert req.cliente_id == 5
    assert len(req.items) == 2


def test_venta_create_request_rejects_invalid_cliente_id() -> None:
    with pytest.raises(ValidationError):
        VentaCreateRequest(cliente_id=0, items=[VentaItemRequest(libro_id=1, cantidad=1)])


def test_venta_create_request_requires_at_least_one_item() -> None:
    with pytest.raises(ValidationError):
        VentaCreateRequest(cliente_id=5, items=[])


def test_venta_create_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        VentaCreateRequest(cliente_id=5, items=[VentaItemRequest(libro_id=1, cantidad=1)], hack="yes")


def test_venta_response_from_attributes() -> None:
    ahora = datetime.now(timezone.utc)

    class DummyVenta:
        id = 100
        cliente_id = 5
        usuario_id = 2
        fecha = ahora
        total = Decimal("45000.00")

    res = VentaResponse.model_validate(DummyVenta())
    assert res.id == 100
    assert res.cliente_id == 5
    assert res.total == Decimal("45000.00")


def test_venta_detail_response_with_items() -> None:
    ahora = datetime.now(timezone.utc)

    class DummyDetalle:
        id = 1
        libro_id = 3
        cantidad = 2
        precio_unitario = Decimal("15000.00")

    class DummyVentaConDetalles:
        id = 100
        cliente_id = 5
        usuario_id = 2
        fecha = ahora
        total = Decimal("30000.00")
        detalles = [DummyDetalle()]
        cliente = None

    res = VentaDetailResponse.model_validate(DummyVentaConDetalles())
    assert res.id == 100
    assert len(res.detalles) == 1
    assert res.detalles[0].cantidad == 2
