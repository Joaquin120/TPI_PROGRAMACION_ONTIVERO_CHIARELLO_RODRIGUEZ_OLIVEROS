from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class VentaRenglonCreate(BaseModel):
    libro_id: int = Field(..., gt=0, description="Identificador único del libro en catálogo")
    cantidad: int = Field(..., ge=1, description="Cantidad de ejemplares (entero mayor o igual a 1)")


class VentaCreate(BaseModel):
    cliente_id: int = Field(..., gt=0, description="Identificador del cliente comprador")
    renglones: list[VentaRenglonCreate] = Field(
        ...,
        min_length=1,
        description="Lista de renglones que componen la venta (al menos 1)",
    )

    @field_validator("renglones")
    @classmethod
    def validate_unique_libros(cls, v: list[VentaRenglonCreate]) -> list[VentaRenglonCreate]:
        libro_ids = [r.libro_id for r in v]
        if len(libro_ids) != len(set(libro_ids)):
            raise ValueError("No se permite incluir el mismo libro en más de un renglón de la venta (RN-VEN-04)")
        return v


class VentaRenglonResponse(BaseModel):
    id: int
    libro_id: int
    titulo: str | None = None
    cantidad: int
    precio_unitario: float
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class VentaResponse(BaseModel):
    id: int
    cliente_id: int
    cliente_nombre: str | None = None
    fecha: datetime
    total: float
    renglones: list[VentaRenglonResponse]

    model_config = ConfigDict(from_attributes=True)
