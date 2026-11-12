import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class ClienteBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=128, description="Nombre completo del cliente")
    email: str = Field(..., max_length=255, description="Correo electrónico único del cliente")

    @field_validator("nombre")
    @classmethod
    def validate_nombre_not_blank(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("El nombre del cliente no puede estar vacío")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("El formato del correo electrónico no es válido")
        return clean


class ClienteCreate(ClienteBase):
    pass


class ClienteResponse(ClienteBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
