from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.modules.libros.models import Autor, Editorial, Genero, Libro


async def test_catalogo_public_endpoints(
    app_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    autor = Autor(nombre="Jorge Luis Borges", biografia="Escritor")
    ed = Editorial(nombre="Emecé Editores")
    gen = Genero(nombre="Ficción")
    db_session.add_all([autor, ed, gen])
    await db_session.commit()

    libro = Libro(
        isbn="978-950-04-0010-0",
        titulo="Ficciones",
        precio=Decimal("2500.00"),
        stock=10,
        autor_id=autor.id,
        editorial_id=ed.id,
        genero_id=gen.id,
    )
    db_session.add(libro)
    await db_session.commit()

    # GET /libros without authentication
    res = await app_client.get("/libros")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["size"] == 20
    assert data["pages"] == 1
    assert data["items"][0]["titulo"] == "Ficciones"
    assert data["items"][0]["autor"]["nombre"] == "Jorge Luis Borges"

    # GET /libros/{id}
    res_detail = await app_client.get(f"/libros/{libro.id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["isbn"] == "978-950-04-0010-0"

    # GET /libros/{id} 404
    res_404 = await app_client.get("/libros/999999")
    assert res_404.status_code == 404

    # GET /autores
    res_autores = await app_client.get("/autores")
    assert res_autores.status_code == 200
    assert any(a["nombre"] == "Jorge Luis Borges" for a in res_autores.json())

    # GET /autores/{id}/libros
    res_autor_libros = await app_client.get(f"/autores/{autor.id}/libros")
    assert res_autor_libros.status_code == 200
    assert res_autor_libros.json()["total"] == 1

    # GET /editoriales
    res_ed = await app_client.get("/editoriales")
    assert res_ed.status_code == 200
    assert any(e["nombre"] == "Emecé Editores" for e in res_ed.json())

    # GET /editoriales/{id}/libros
    res_ed_libros = await app_client.get(f"/editoriales/{ed.id}/libros")
    assert res_ed_libros.status_code == 200
    assert res_ed_libros.json()["total"] == 1

    # GET /generos
    res_gen = await app_client.get("/generos")
    assert res_gen.status_code == 200
    assert any(g["nombre"] == "Ficción" for g in res_gen.json())

    # GET /generos/{id}/libros
    res_gen_libros = await app_client.get(f"/generos/{gen.id}/libros")
    assert res_gen_libros.status_code == 200
    assert res_gen_libros.json()["total"] == 1

    # Pagination 422 when page > pages
    res_p422 = await app_client.get("/libros?page=99&size=10")
    assert res_p422.status_code == 422


async def test_openapi_docs_and_route_segregation(app_client: AsyncClient) -> None:
    from parcial.app.main import app, open_router, protected_router

    res = await app_client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    paths = schema["paths"]

    assert "/libros" in paths
    assert "/libros/{id}" in paths
    assert "/libros/{id}/reponer" in paths
    assert "/libros/{id}/movimientos" in paths
    assert "/autores" in paths
    assert "/editoriales" in paths
    assert "/generos" in paths

