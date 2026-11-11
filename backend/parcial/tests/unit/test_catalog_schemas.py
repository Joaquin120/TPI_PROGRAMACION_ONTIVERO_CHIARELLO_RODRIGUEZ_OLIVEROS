from decimal import Decimal
import pytest
from pydantic import ValidationError

from parcial.app.modules.libros.schemas import (
    AutorResponse,
    EditorialResponse,
    GeneroResponse,
    LibroCreateRequest,
    LibroDetailResponse,
    LibroResponse,
    LibroUpdateRequest,
    MovimientoStockResponse,
    ReponerStockRequest,
)


def test_autor_response_accepts_valid_data() -> None:
    autor = AutorResponse(id=1, nombre="Jorge Luis Borges", biografia="Escritor argentino")
    assert autor.id == 1
    assert autor.nombre == "Jorge Luis Borges"
    assert autor.biografia == "Escritor argentino"


def test_autor_response_optional_biografia() -> None:
    autor = AutorResponse(id=1, nombre="Julio Cortázar")
    assert autor.biografia is None


def test_autor_response_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        AutorResponse(id=1, nombre="Borges", extra_field="invalid")


def test_editorial_response_accepts_valid_data() -> None:
    ed = EditorialResponse(id=1, nombre="Sur")
    assert ed.id == 1
    assert ed.nombre == "Sur"


def test_editorial_response_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        EditorialResponse(id=1, nombre="Sur", extra_field="invalid")


def test_genero_response_accepts_valid_data() -> None:
    gen = GeneroResponse(id=1, nombre="Ficción")
    assert gen.id == 1
    assert gen.nombre == "Ficción"


def test_genero_response_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        GeneroResponse(id=1, nombre="Ficción", extra_field="invalid")


def test_catalog_schemas_from_attributes() -> None:
    class DummyAutor:
        id = 10
        nombre = "Cortazar"
        biografia = None

    class DummyEditorial:
        id = 20
        nombre = "Alfaguara"

    class DummyGenero:
        id = 30
        nombre = "Novela"

    autor = AutorResponse.model_validate(DummyAutor())
    editorial = EditorialResponse.model_validate(DummyEditorial())
    genero = GeneroResponse.model_validate(DummyGenero())

    assert autor.id == 10 and autor.nombre == "Cortazar" and autor.biografia is None
    assert editorial.id == 20 and editorial.nombre == "Alfaguara"
    assert genero.id == 30 and genero.nombre == "Novela"


def test_libro_create_request_valid() -> None:
    req = LibroCreateRequest(
        isbn="978-987-1138-01-2",
        titulo="Ficciones",
        precio=Decimal("1500.50"),
        stock_inicial=10,
        autor_id=1,
        editorial_id=2,
        genero_id=3,
    )
    assert req.isbn == "978-987-1138-01-2"
    assert req.precio == Decimal("1500.50")
    assert req.stock_inicial == 10


def test_libro_create_request_rejects_negative_stock() -> None:
    with pytest.raises(ValidationError):
        LibroCreateRequest(
            isbn="978-987-1138-01-2",
            titulo="Ficciones",
            precio=Decimal("1500.50"),
            stock_inicial=-1,
            autor_id=1,
            editorial_id=2,
            genero_id=3,
        )


def test_libro_create_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        LibroCreateRequest(
            isbn="978-987-1138-01-2",
            titulo="Ficciones",
            precio=Decimal("1500.50"),
            stock_inicial=5,
            autor_id=1,
            editorial_id=2,
            genero_id=3,
            descuento=10,
        )


def test_libro_update_request_accepts_valid_fields() -> None:
    req = LibroUpdateRequest(
        titulo="Ficciones - Edición Especial",
        precio=Decimal("2000.00"),
    )
    assert req.titulo == "Ficciones - Edición Especial"
    assert req.precio == Decimal("2000.00")


def test_libro_update_request_strictly_rejects_stock() -> None:
    with pytest.raises(ValidationError):
        LibroUpdateRequest(stock=50)


def test_libro_detail_response_includes_relations() -> None:
    detail = LibroDetailResponse(
        id=1,
        isbn="978-987-1138-01-2",
        titulo="Ficciones",
        precio=Decimal("1500.50"),
        stock=10,
        autor_id=1,
        editorial_id=2,
        genero_id=3,
        borrado_en=None,
        autor=AutorResponse(id=1, nombre="Borges"),
        editorial=EditorialResponse(id=2, nombre="Sur"),
        genero=GeneroResponse(id=3, nombre="Cuentos"),
    )
    assert detail.autor.nombre == "Borges"
    assert detail.editorial.nombre == "Sur"
    assert detail.genero.nombre == "Cuentos"


def test_libro_response_from_orm_object() -> None:
    class DummyLibro:
        id = 99
        isbn = "1234567890"
        titulo = "El Aleph"
        precio = Decimal("1200.00")
        stock = 25
        autor_id = 1
        editorial_id = 2
        genero_id = 3
        borrado_en = None

    res = LibroResponse.model_validate(DummyLibro())
    assert res.id == 99
    assert res.titulo == "El Aleph"
    assert res.stock == 25


def test_reponer_stock_request_valid() -> None:
    req = ReponerStockRequest(cantidad=15)
    assert req.cantidad == 15


def test_reponer_stock_request_rejects_zero_or_negative() -> None:
    with pytest.raises(ValidationError):
        ReponerStockRequest(cantidad=0)

    with pytest.raises(ValidationError):
        ReponerStockRequest(cantidad=-5)


def test_reponer_stock_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ReponerStockRequest(cantidad=10, motivo="Reposicion")


def test_movimiento_stock_response_from_orm() -> None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    class DummyMovimiento:
        id = 1
        libro_id = 42
        venta_id = None
        usuario_id = 7
        cantidad = 20
        motivo = "Reposicion"
        cuando = now

    res = MovimientoStockResponse.model_validate(DummyMovimiento())
    assert res.id == 1
    assert res.libro_id == 42
    assert res.cantidad == 20
    assert res.motivo == "Reposicion"
    assert res.cuando == now




