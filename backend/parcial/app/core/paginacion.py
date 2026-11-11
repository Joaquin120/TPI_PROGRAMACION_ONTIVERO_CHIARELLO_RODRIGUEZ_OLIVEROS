import math
from typing import Annotated, Generic, TypeVar
from fastapi import HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard uniform pagination envelope."""

    model_config = ConfigDict(extra="forbid")

    items: list[T]
    total: int = Field(..., ge=0, description="Total de registros coincidentes")
    page: int = Field(..., ge=1, description="Número de página actual")
    size: int = Field(..., ge=1, le=100, description="Cantidad de registros por página")
    pages: int = Field(..., ge=1, description="Total de páginas calculadas")


def calcular_total_paginas(total: int, size: int) -> int:
    """Calculates total pages. Returns 1 if total is 0."""
    if total <= 0:
        return 1
    return math.ceil(total / size)


def crear_respuesta_paginada(
    items: list[T],
    total: int,
    page: int,
    size: int,
) -> PaginatedResponse[T]:
    """Builds a PaginatedResponse and enforces boundary validation (HTTP 422)."""
    pages = calcular_total_paginas(total, size)
    if page > pages:
        raise HTTPException(
            status_code=422,
            detail=f"La página {page} no existe: hay {pages}",
        )
    return PaginatedResponse[T](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


# Alias for compatibility across modules
armar_paginacion = crear_respuesta_paginada


class PaginationParams:
    """FastAPI dependency container for pagination query parameters."""

    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Número de página")] = 1,
        size: Annotated[int, Query(ge=1, le=100, description="Registros por página")] = 20,
    ) -> None:
        self.page = page
        self.size = size

    @property
    def skip(self) -> int:
        """Calculates SQL offset."""
        return (self.page - 1) * self.size
