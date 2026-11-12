from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class EditorialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class GeneroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class AutorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    biografia: str | None = None


class LibroAutorDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    autor_id: int
    nombre: str
    rol: str
    orden: int


class LibroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    isbn: str
    precio: Decimal = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    editorial: str | None = None
    genero: str | None = None


class LibroDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    isbn: str
    precio: Decimal = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    editorial_id: int
    editorial: str | None = None
    genero_id: int | None = None
    genero: str | None = None
    autores: list[LibroAutorDetailResponse] = Field(default_factory=list)


class LibroListResponse(BaseModel):
    items: list[LibroResponse]
    total: int
    limit: int
    offset: int

