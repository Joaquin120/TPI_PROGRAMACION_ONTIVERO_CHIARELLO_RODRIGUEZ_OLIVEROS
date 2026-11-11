from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.security import ACCESS_TOKEN_COOKIE, crear_token_acceso, hash_password
from parcial.app.modules.libros.models import Autor, Editorial, Genero, Libro
from parcial.app.modules.usuarios.models import AsignacionRol, Usuario


async def _crear_admin(db_session: AsyncSession) -> tuple[Usuario, str]:
    pw_hash = await hash_password("secreto-123")
    user = Usuario(email="softdelete_admin@example.com", nombre="Admin", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()

    asignacion = AsignacionRol(usuario_id=user.id, rol="ADMIN")
    db_session.add(asignacion)
    await db_session.commit()

    token = crear_token_acceso(usuario_id=user.id, email=user.email, roles=["ADMIN"])
    return user, token


async def test_soft_delete_lifecycle_and_isbn_reuse_in_db(
    app_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    admin, token = await _crear_admin(db_session)
    autor = Autor(nombre="Julio Verne")
    ed = Editorial(nombre="Hetzel")
    gen = Genero(nombre="Aventura")
    db_session.add_all([autor, ed, gen])
    await db_session.commit()
    autor_id = autor.id
    ed_id = ed.id
    gen_id = gen.id

    app_client.cookies.set(ACCESS_TOKEN_COOKIE, token)

    isbn_compartido = "978-84-206-0000-1"
    payload_a = {
        "isbn": isbn_compartido,
        "titulo": "Veinte mil leguas de viaje submarino (1ra Edición)",
        "precio": "3000.00",
        "stock_inicial": 7,
        "autor_id": autor_id,
        "editorial_id": ed_id,
        "genero_id": gen_id,
    }

    # 1. Crear Libro A
    res_a = await app_client.post("/libros", json=payload_a)
    assert res_a.status_code == 201
    libro_a_id = res_a.json()["id"]

    # 2. Intento de crear Libro B con el mismo ISBN mientras A está activo -> 409
    res_dup = await app_client.post("/libros", json=payload_a)
    assert res_dup.status_code == 409

    # 3. Eliminar Libro A (Baja lógica) -> 204
    res_del = await app_client.delete(f"/libros/{libro_a_id}")
    assert res_del.status_code == 204

    # 4. Libro A ya no es visible en catálogo público
    res_get_a = await app_client.get(f"/libros/{libro_a_id}")
    assert res_get_a.status_code == 404

    res_list = await app_client.get("/libros")
    assert not any(item["id"] == libro_a_id for item in res_list.json()["items"])

    # 5. Crear Libro C con el MISMO ISBN -> Debe permitirse sin conflicto en PostgreSQL
    payload_c = {
        "isbn": isbn_compartido,
        "titulo": "Veinte mil leguas de viaje submarino (Nueva Traducción)",
        "precio": "4500.00",
        "stock_inicial": 10,
        "autor_id": autor_id,
        "editorial_id": ed_id,
        "genero_id": gen_id,
    }
    res_c = await app_client.post("/libros", json=payload_c)
    assert res_c.status_code == 201
    libro_c_id = res_c.json()["id"]
    assert libro_c_id != libro_a_id

    # 6. Re-eliminar Libro A devuelve 404
    res_re_del = await app_client.delete(f"/libros/{libro_a_id}")
    assert res_re_del.status_code == 404

    # 7. Verificación física en PostgreSQL: ambos registros existen en tabla libro
    stmt = select(Libro).where(Libro.isbn == isbn_compartido).order_by(Libro.id.asc())
    result = await db_session.execute(stmt)
    libros_en_db = result.scalars().all()

    assert len(libros_en_db) == 2
    assert libros_en_db[0].id == libro_a_id
    assert libros_en_db[0].borrado_en is not None  # Borrado lógicamente
    assert libros_en_db[1].id == libro_c_id
    assert libros_en_db[1].borrado_en is None      # Activo

