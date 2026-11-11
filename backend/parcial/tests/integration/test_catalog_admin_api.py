from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.security import ACCESS_TOKEN_COOKIE, crear_token_acceso, hash_password
from parcial.app.modules.libros.models import Autor, Editorial, Genero, Libro
from parcial.app.modules.usuarios.models import AsignacionRol, Usuario


async def _crear_usuario_con_rol(
    db_session: AsyncSession,
    email: str,
    rol: str,
) -> Usuario:
    pw_hash = await hash_password("secreto-123")
    user = Usuario(email=email, nombre="Usuario Test", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()

    asignacion = AsignacionRol(usuario_id=user.id, rol=rol)
    db_session.add(asignacion)
    await db_session.commit()
    return user


async def test_admin_book_endpoints_security_matrix_and_crud(
    app_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    admin = await _crear_usuario_con_rol(db_session, "admin_books@example.com", "ADMIN")
    cliente = await _crear_usuario_con_rol(db_session, "cliente_books@example.com", "CLIENTE")

    autor = Autor(nombre="Cortázar")
    ed = Editorial(nombre="Sudamericana")
    gen = Genero(nombre="Cuentos")
    db_session.add_all([autor, ed, gen])
    await db_session.commit()
    autor_id = autor.id
    ed_id = ed.id
    gen_id = gen.id

    token_admin = crear_token_acceso(
        usuario_id=admin.id,
        email=admin.email,
        roles=["ADMIN"],
    )
    token_cliente = crear_token_acceso(
        usuario_id=cliente.id,
        email=cliente.email,
        roles=["CLIENTE"],
    )

    payload_create = {
        "isbn": "978-950-07-0050-0",
        "titulo": "Rayuela",
        "precio": "3200.00",
        "stock_inicial": 8,
        "autor_id": autor_id,
        "editorial_id": ed_id,
        "genero_id": gen_id,
    }

    # 1. Anonymous -> 401
    res_anon = await app_client.post("/libros", json=payload_create)
    assert res_anon.status_code == 401

    # 2. Cliente -> 403
    app_client.cookies.set(ACCESS_TOKEN_COOKIE, token_cliente)
    res_cli = await app_client.post("/libros", json=payload_create)
    assert res_cli.status_code == 403

    # 3. Admin -> 201 Created
    app_client.cookies.set(ACCESS_TOKEN_COOKIE, token_admin)
    res_ok = await app_client.post("/libros", json=payload_create)
    assert res_ok.status_code == 201
    book_id = res_ok.json()["id"]
    assert res_ok.json()["stock"] == 8

    # 4. Extra fields in create -> 422
    payload_extra = dict(payload_create)
    payload_extra["isbn"] = "978-950-07-0051-1"
    payload_extra["descuento"] = 10
    res_extra = await app_client.post("/libros", json=payload_extra)
    assert res_extra.status_code == 422

    # 5. Duplicate ISBN -> 409
    res_dup = await app_client.post("/libros", json=payload_create)
    assert res_dup.status_code == 409

    # 6. PATCH /libros/{id} with forbidden stock -> 422
    res_patch_stock = await app_client.patch(f"/libros/{book_id}", json={"stock": 99})
    assert res_patch_stock.status_code == 422

    # 7. PATCH /libros/{id} valid metadata -> 200
    res_patch = await app_client.patch(
        f"/libros/{book_id}",
        json={"titulo": "Rayuela - Edición Aniversario", "precio": "3800.00"},
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["titulo"] == "Rayuela - Edición Aniversario"
    assert res_patch.json()["stock"] == 8  # stock preserved

    # 8. DELETE /libros/{id} by non-admin -> 403
    app_client.cookies.set(ACCESS_TOKEN_COOKIE, token_cliente)
    res_del_cli = await app_client.delete(f"/libros/{book_id}")
    assert res_del_cli.status_code == 403

    # 9. DELETE /libros/{id} by admin -> 204
    app_client.cookies.set(ACCESS_TOKEN_COOKIE, token_admin)
    res_del = await app_client.delete(f"/libros/{book_id}")
    assert res_del.status_code == 204

    # 10. Re-deleting -> 404
    res_del_404 = await app_client.delete(f"/libros/{book_id}")
    assert res_del_404.status_code == 404

    # 11. PATCH on deleted book -> 404
    res_patch_del = await app_client.patch(f"/libros/{book_id}", json={"titulo": "Otro"})
    assert res_patch_del.status_code == 404


async def test_admin_stock_endpoints_security_and_conflict(
    app_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    admin = await _crear_usuario_con_rol(db_session, "stock_api_admin@example.com", "ADMIN")
    vendedor = await _crear_usuario_con_rol(db_session, "stock_api_vendedor@example.com", "VENDEDOR")

    autor = Autor(nombre="García Márquez")
    ed = Editorial(nombre="Sudamericana")
    gen = Genero(nombre="Novela")
    db_session.add_all([autor, ed, gen])
    await db_session.commit()

    token_admin = crear_token_acceso(usuario_id=admin.id, email=admin.email, roles=["ADMIN"])
    token_vendedor = crear_token_acceso(usuario_id=vendedor.id, email=vendedor.email, roles=["VENDEDOR"])

    app_client.cookies.set(ACCESS_TOKEN_COOKIE, token_admin)
    res_libro = await app_client.post(
        "/libros",
        json={
            "isbn": "978-950-07-3333-3",
            "titulo": "Crónica de una muerte anunciada",
            "precio": "2800.00",
            "stock_inicial": 5,
            "autor_id": autor.id,
            "editorial_id": ed.id,
            "genero_id": gen.id,
        },
    )
    assert res_libro.status_code == 201
    libro_id = res_libro.json()["id"]

    # 1. Anonymous restock -> 401
    app_client.cookies.clear()
    res_anon = await app_client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 10})
    assert res_anon.status_code == 401

    # 2. Vendedor restock -> 403
    app_client.cookies.set(ACCESS_TOKEN_COOKIE, token_vendedor)
    res_vend = await app_client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 10})
    assert res_vend.status_code == 403

    # 3. Non-positive quantity -> 422
    app_client.cookies.set(ACCESS_TOKEN_COOKIE, token_admin)
    res_neg = await app_client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 0})
    assert res_neg.status_code == 422

    # 4. Extra fields -> 422
    res_extra = await app_client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 5, "extra": "x"})
    assert res_extra.status_code == 422

    # 5. Successful restock -> 200
    res_restock = await app_client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 15})
    assert res_restock.status_code == 200
    assert res_restock.json()["stock"] == 20

    # 6. GET /libros/{id}/movimientos -> 200
    res_movs = await app_client.get(f"/libros/{libro_id}/movimientos")
    assert res_movs.status_code == 200
    data_movs = res_movs.json()
    assert data_movs["total"] == 2
    assert data_movs["items"][0]["motivo"] == "Stock inicial"
    assert data_movs["items"][1]["motivo"] == "Reposicion"
    assert data_movs["items"][1]["cantidad"] == 15

    # 7. Soft delete book -> restock returns 409 Conflict
    res_del = await app_client.delete(f"/libros/{libro_id}")
    assert res_del.status_code == 204

    res_conflict = await app_client.post(f"/libros/{libro_id}/reponer", json={"cantidad": 5})
    assert res_conflict.status_code == 409

