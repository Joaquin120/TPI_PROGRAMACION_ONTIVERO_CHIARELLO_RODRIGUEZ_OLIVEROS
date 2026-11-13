import pytest
from pydantic import ValidationError

from src.schemas.venta import (
    VentaCreate,
    VentaRenglonCreate,
    VentaResponse,
    VentaRenglonResponse,
)


def test_venta_renglon_create_valid() -> None:
    """Verifies valid renglon create payload."""
    renglon = VentaRenglonCreate(libro_id=1, cantidad=3)
    assert renglon.libro_id == 1
    assert renglon.cantidad == 3


def test_venta_renglon_create_invalid_cantidad() -> None:
    """Verifies cantidad must be >= 1 (RN-VEN-03)."""
    with pytest.raises(ValidationError):
        VentaRenglonCreate(libro_id=1, cantidad=0)

    with pytest.raises(ValidationError):
        VentaRenglonCreate(libro_id=1, cantidad=-5)


def test_venta_create_valid() -> None:
    """Verifies valid venta create payload."""
    venta = VentaCreate(
        cliente_id=1,
        renglones=[
            VentaRenglonCreate(libro_id=1, cantidad=2),
            VentaRenglonCreate(libro_id=2, cantidad=1),
        ],
    )
    assert venta.cliente_id == 1
    assert len(venta.renglones) == 2


def test_venta_create_empty_renglones_rejected() -> None:
    """Verifies empty renglones list is rejected (RN-VEN-02)."""
    with pytest.raises(ValidationError):
        VentaCreate(cliente_id=1, renglones=[])


def test_venta_create_duplicate_libro_rejected() -> None:
    """Verifies duplicate libro_id in renglones is rejected (RN-VEN-04)."""
    with pytest.raises(ValidationError):
        VentaCreate(
            cliente_id=1,
            renglones=[
                VentaRenglonCreate(libro_id=1, cantidad=2),
                VentaRenglonCreate(libro_id=1, cantidad=3),
            ],
        )
