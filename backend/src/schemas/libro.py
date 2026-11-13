from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class LibroAutorCreate(BaseModel):
    autor_id: int
    rol: str = Field(default="autor")
    orden: int = Field(default=1, ge=1)

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, v: str) -> str:
        roles_validos = {"autor", "coautor", "traductor", "ilustrador"}
        if v.lower() not in roles_validos:
            raise ValueError(f"Rol '{v}' no válido. Debe ser uno de: {', '.join(sorted(roles_validos))}")
        return v.lower()


class LibroCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=255)
    isbn: str = Field(..., min_length=1, max_length=32)
    precio: Decimal = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    editorial_id: int
    genero_id: int | None = None
    autores: list[LibroAutorCreate] = Field(..., min_length=1)


class LibroUpdate(BaseModel):
    """Schema for partial updates to an existing book (used by PATCH /libros/{id})."""

    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    isbn: str | None = Field(default=None, min_length=1, max_length=32)
    precio: Decimal | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    editorial_id: int | None = None
    genero_id: int | None = None


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
