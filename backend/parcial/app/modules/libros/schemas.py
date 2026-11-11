"""Strict schemas for catalog entities and stock management."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

IsbnStr = Annotated[str, Field(min_length=1, max_length=30)]
TituloStr = Annotated[str, Field(min_length=1, max_length=200)]


class StrictModel(BaseModel):
    """Base model rejecting undeclared fields."""

    model_config = ConfigDict(extra="forbid")


class AutorResponse(StrictModel):
    """Author response contract."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str
    biografia: str | None = None


class EditorialResponse(StrictModel):
    """Publisher response contract."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str


class GeneroResponse(StrictModel):
    """Genre response contract."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str


class LibroCreateRequest(StrictModel):
    """Payload for administrative book registration."""

    isbn: IsbnStr
    titulo: TituloStr
    precio: Decimal = Field(..., gt=Decimal("0"))
    stock_inicial: int = Field(default=0, ge=0)
    autor_id: int
    editorial_id: int
    genero_id: int


class LibroUpdateRequest(StrictModel):
    """Payload for partial book metadata update. Direct mutation of stock is strictly forbidden."""

    titulo: TituloStr | None = None
    precio: Decimal | None = Field(default=None, gt=Decimal("0"))
    autor_id: int | None = None
    editorial_id: int | None = None
    genero_id: int | None = None


class LibroResponse(StrictModel):
    """Public book catalog projection."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    autor_id: int
    editorial_id: int
    genero_id: int
    borrado_en: datetime | None = None


class LibroDetailResponse(LibroResponse):
    """Detailed book projection including related entities."""

    autor: AutorResponse
    editorial: EditorialResponse
    genero: GeneroResponse


class ReponerStockRequest(StrictModel):
    """Payload for administrative stock replenishment."""

    cantidad: int = Field(..., gt=0, description="Cantidad a incrementar en stock")


class MovimientoStockResponse(StrictModel):
    """Historical stock movement ledger projection."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    libro_id: int
    venta_id: int | None = None
    usuario_id: int
    cantidad: int
    motivo: str
    cuando: datetime


