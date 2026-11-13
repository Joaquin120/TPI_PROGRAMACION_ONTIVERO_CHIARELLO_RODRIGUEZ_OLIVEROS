from decimal import Decimal
import pytest
from pydantic import ValidationError

from src.schemas.libro import (
    AutorResponse,
    EditorialResponse,
    GeneroResponse,
    LibroAutorCreate,
    LibroAutorDetailResponse,
    LibroCreate,
    LibroDetailResponse,
    LibroResponse,
    LibroUpdate,
)


def test_libro_autor_create_valid():
    autor = LibroAutorCreate(autor_id=1, rol="autor", orden=1)
    assert autor.autor_id == 1
    assert autor.rol == "autor"
    assert autor.orden == 1


def test_libro_autor_create_rol_invalido():
    with pytest.raises(ValidationError):
        LibroAutorCreate(autor_id=1, rol="director", orden=1)


def test_libro_create_valid():
    libro_in = LibroCreate(
        titulo="Manual de Python",
        isbn="978-987-1234-56-7",
        precio=Decimal("2500.00"),
        stock=15,
        editorial_id=1,
        genero_id=2,
        autores=[
            LibroAutorCreate(autor_id=1, rol="autor", orden=1),
            LibroAutorCreate(autor_id=2, rol="coautor", orden=2),
        ],
    )
    assert libro_in.titulo == "Manual de Python"
    assert len(libro_in.autores) == 2


def test_libro_create_sin_autores():
    with pytest.raises(ValidationError):
        LibroCreate(
            titulo="Sin autores",
            isbn="978-000-0000-00-0",
            precio=Decimal("1000.00"),
            stock=1,
            editorial_id=1,
            autores=[],
        )


def test_libro_create_precio_cero():
    with pytest.raises(ValidationError):
        LibroCreate(
            titulo="Gratis",
            isbn="978-000-0000-00-1",
            precio=Decimal("0.00"),
            stock=1,
            editorial_id=1,
            autores=[LibroAutorCreate(autor_id=1)],
        )


def test_libro_create_stock_negativo():
    with pytest.raises(ValidationError):
        LibroCreate(
            titulo="Negativo",
            isbn="978-000-0000-00-2",
            precio=Decimal("500.00"),
            stock=-5,
            editorial_id=1,
            autores=[LibroAutorCreate(autor_id=1)],
        )


def test_libro_update_partial_valid():
    libro_upd = LibroUpdate(precio=Decimal("2999.99"))
    assert libro_upd.precio == Decimal("2999.99")
    assert "precio" in libro_upd.model_fields_set
    assert "titulo" not in libro_upd.model_fields_set


def test_libro_update_invalid_precio_o_stock():
    with pytest.raises(ValidationError):
        LibroUpdate(precio=Decimal("0"))

    with pytest.raises(ValidationError):
        LibroUpdate(stock=-1)
