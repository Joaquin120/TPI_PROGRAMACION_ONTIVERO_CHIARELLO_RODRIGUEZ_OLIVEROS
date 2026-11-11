import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from parcial.app.core.paginacion import (
    PaginatedResponse,
    PaginationParams,
    calcular_total_paginas,
    crear_respuesta_paginada,
)


def test_calcular_total_paginas() -> None:
    """Verifies page calculation including empty collection case."""
    assert calcular_total_paginas(0, 20) == 1
    assert calcular_total_paginas(10, 20) == 1
    assert calcular_total_paginas(20, 20) == 1
    assert calcular_total_paginas(21, 20) == 2
    assert calcular_total_paginas(50, 20) == 3


def test_crear_respuesta_paginada_standard() -> None:
    """Verifies normal paginated response creation."""
    items = ["item1", "item2"]
    resp = crear_respuesta_paginada(items, total=50, page=1, size=20)
    assert resp.items == items
    assert resp.total == 50
    assert resp.page == 1
    assert resp.size == 20
    assert resp.pages == 3


def test_crear_respuesta_paginada_total_zero() -> None:
    """Verifies edge case where total == 0 returns 1 empty page."""
    resp = crear_respuesta_paginada([], total=0, page=1, size=20)
    assert resp.items == []
    assert resp.total == 0
    assert resp.page == 1
    assert resp.size == 20
    assert resp.pages == 1


def test_crear_respuesta_paginada_page_exceeded_raises_422() -> None:
    """Verifies requesting page > pages raises HTTP 422 with exact message."""
    with pytest.raises(HTTPException) as exc_info:
        crear_respuesta_paginada(["item"], total=50, page=4, size=20)

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "La página 4 no existe: hay 3"


def test_crear_respuesta_paginada_page_exceeded_with_zero_total() -> None:
    """Verifies requesting page > 1 when total == 0 raises HTTP 422."""
    with pytest.raises(HTTPException) as exc_info:
        crear_respuesta_paginada([], total=0, page=2, size=20)

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "La página 2 no existe: hay 1"


def test_pagination_params_defaults() -> None:
    """Verifies default values for PaginationParams."""
    params = PaginationParams()
    assert params.page == 1
    assert params.size == 20
    assert params.skip == 0

    custom = PaginationParams(page=3, size=15)
    assert custom.page == 3
    assert custom.size == 15
    assert custom.skip == 30


def test_paginated_response_extra_forbid() -> None:
    """Verifies extra attributes are strictly forbidden in PaginatedResponse."""
    with pytest.raises(ValidationError):
        PaginatedResponse(
            items=[],
            total=0,
            page=1,
            size=20,
            pages=1,
            extra_field="rejected",
        )
