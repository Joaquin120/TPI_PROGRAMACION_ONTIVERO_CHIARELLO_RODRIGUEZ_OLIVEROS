"""Pydantic schemas for the customers module with strict extra='forbid' validation."""

from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

EmailStr = Annotated[str, Field(min_length=3, max_length=255)]
NombreStr = Annotated[str, Field(min_length=1, max_length=100)]


class ClienteBase(BaseModel):
    """Base schema for customer entities."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: NombreStr
    email: EmailStr
    telefono: str | None = Field(default=None, max_length=50)
    direccion: str | None = Field(default=None, max_length=200)


class ClienteCreateRequest(ClienteBase):
    """Request DTO to create a new customer."""

    pass


class ClienteUpdateRequest(BaseModel):
    """Request DTO for partial customer update (PATCH)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: NombreStr | None = None
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=50)
    direccion: str | None = Field(default=None, max_length=200)


class ClienteResponse(BaseModel):
    """Response DTO representing a customer record."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str
    email: str
    telefono: str | None = None
    direccion: str | None = None
    usuario_id: int | None = None
