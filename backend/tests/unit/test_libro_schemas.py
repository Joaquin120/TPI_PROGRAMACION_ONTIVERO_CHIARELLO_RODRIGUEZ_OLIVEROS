from decimal import Decimal
import pytest
from pydantic import ValidationError

from src.schemas.libro import (
    AutorResponse,
    EditorialResponse,
    GeneroResponse,
    LibroAutorDetailResponse,
    LibroDetailResponse,
    LibroResponse,
)


def test_editorial_response_valid():
    editorial = EditorialResponse(id=1, nombre="Editorial Sudamericana")
    assert editorial.id == 1
    assert editorial.nombre == "Editorial Sudamericana"


def test_genero_response_valid():
    genero = GeneroResponse(id=1, nombre="Fábula")
    assert genero.id == 1
    assert genero.nombre == "Fábula"


def test_libro_response_valid():
    libro = LibroResponse(
        id=1,
        titulo="El principito",
        isbn="978-84-376-0494-7",
        precio=Decimal("1500.00"),
        stock=10,
        editorial="Editorial Sudamericana",
        genero="Fábula",
    )
    assert libro.id == 1
    assert libro.titulo == "El principito"
    assert libro.precio == Decimal("1500.00")
    assert libro.genero == "Fábula"


def test_libro_response_genero_none():
    libro = LibroResponse(
        id=2,
        titulo="Cuentos de terror",
        isbn="978-987-1111-22-3",
        precio=Decimal("2000.00"),
        stock=5,
        editorial="Ediciones Horizon",
        genero=None,
    )
    assert libro.genero is None


def test_libro_response_precio_invalido():
    with pytest.raises(ValidationError):
        LibroResponse(
            id=3,
            titulo="Invalido",
            isbn="123",
            precio=Decimal("0.00"),
            stock=1,
            editorial="UTN",
        )


def test_libro_detail_response_con_autores():
    detalle = LibroDetailResponse(
        id=1,
        titulo="El principito",
        isbn="978-84-376-0494-7",
        precio=Decimal("1500.00"),
        stock=10,
        editorial_id=1,
        editorial="Editorial Sudamericana",
        genero_id=1,
        genero="Fábula",
        autores=[
            LibroAutorDetailResponse(
                autor_id=1,
                nombre="Antoine de Saint-Exupéry",
                rol="autor",
                orden=1,
            )
        ],
    )
    assert len(detalle.autores) == 1
    assert detalle.autores[0].nombre == "Antoine de Saint-Exupéry"
    assert detalle.autores[0].rol == "autor"

