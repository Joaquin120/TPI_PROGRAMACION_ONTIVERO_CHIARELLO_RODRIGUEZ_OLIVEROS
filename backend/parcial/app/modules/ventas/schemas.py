"""Pydantic schemas for sales transactions with strict extra='forbid' validation."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from parcial.app.modules.clientes.schemas import ClienteResponse


class VentaItemRequest(BaseModel):
    """Line item payload for sales creation."""

    model_config = ConfigDict(extra="forbid")

    libro_id: int = Field(..., gt=0, description="Identificador único del libro")
    cantidad: int = Field(..., gt=0, description="Cantidad a vender (debe ser mayor a 0)")


class VentaCreateRequest(BaseModel):
    """Payload to record a new atomic sale transaction."""

    model_config = ConfigDict(extra="forbid")

    cliente_id: int = Field(..., gt=0, description="Identificador del cliente comprador")
    items: list[VentaItemRequest] = Field(
        ...,
        min_length=1,
        description="Lista de renglones de la venta (al menos 1)",
    )


class DetalleVentaResponse(BaseModel):
    """Response DTO for an individual sale line item."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    libro_id: int
    cantidad: int
    precio_unitario: Decimal


class VentaResponse(BaseModel):
    """Response DTO for sale header summary."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    cliente_id: int
    usuario_id: int
    fecha: datetime
    total: Decimal


class VentaDetailResponse(VentaResponse):
    """Response DTO for sale header with full line items and optional customer info."""

    detalles: list[DetalleVentaResponse] = []
    cliente: ClienteResponse | None = None
