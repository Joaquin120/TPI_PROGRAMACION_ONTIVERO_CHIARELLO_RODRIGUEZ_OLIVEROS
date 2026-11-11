from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from parcial.app.core.security import ACCESS_TOKEN_COOKIE, crear_token_acceso, hash_password
from parcial.app.modules.libros.models import Autor, Editorial, Genero, Libro, MovimientoStock
from parcial.app.modules.usuarios.models import AsignacionRol, Usuario


async def _crear_admin(db_session: AsyncSession) -> tuple[Usuario, str]:
    pw_hash = await hash_password("secreto-123")
    user = Usuario(email="invariant_admin@example.com", nombre="Admin", password_hash=pw_hash)
    db_session.add(user)
    await db_session.flush()

    asignacion = AsignacionRol(usuario_id=user.id, rol="ADMIN")
    db_session.add(asignacion)
    await db_session.commit()

    token = crear_token_acceso(usuario_id=user.id, email=user.email, roles=["ADMIN"])
    return user, token


async def _calcular_suma_movimientos(db_session: AsyncSession, libro_id: int) -> int:
    stmt = (
        select(func.coalesce(func.sum(MovimientoStock.cantidad), 0))
        .where(MovimientoStock.libro_id == libro_id)
    )
    result = await db_session.execute(stmt)
    return int(result.scalar_one() or 0)


async def test_invariante_balance_stock_libro_y_movimientos(
    app_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    admin, token = await _crear_admin(db_session)
    autor = Autor(nombre="Arthur Conan Doyle")
    ed = Editorial(nombre="George Newnes")
    gen = Genero(nombre="Policial")
    db_session.add_all([autor, ed, gen])
    await db_session.commit()
    autor_id = autor.id
    ed_id = ed.id
    gen_id = gen.id

    app_client.cookies.set(ACCESS_TOKEN_COOKIE, token)

    # 1. Crear libro con stock inicial de 10
    res_crear = await app_client.post(
        "/libros",
        json={
            "isbn": "978-0-14-043770-0",
            "titulo": "Estudio en escarlata",
            "precio": "2200.00",
            "stock_inicial": 10,
            "autor_id": autor_id,
            "editorial_id": ed_id,
            "genero_id": gen_id,
        },
    )
    assert res_crear.status_code == 201
    libro_id = res_crear.json()["id"]

    # Invariante tras creación
    suma_1 = await _calcular_suma_movimientos(db_session, libro_id)
    libro_db_1 = await db_session.get(Libro, libro_id)
    assert libro_db_1 is not None
    assert libro_db_1.stock == 10
    assert suma_1 == 10
    assert libro_db_1.stock == suma_1

    # 2. Primera reposición: +25 unidades
    res_repo_1 = await app_client.post(
        f"/libros/{libro_id}/reponer",
        json={"cantidad": 25},
    )
    assert res_repo_1.status_code == 200

    suma_2 = await _calcular_suma_movimientos(db_session, libro_id)
    await db_session.refresh(libro_db_1)
    assert libro_db_1.stock == 35
    assert suma_2 == 35
    assert libro_db_1.stock == suma_2

    # 3. Segunda reposición: +5 unidades
    res_repo_2 = await app_client.post(
        f"/libros/{libro_id}/reponer",
        json={"cantidad": 5},
    )
    assert res_repo_2.status_code == 200

    suma_3 = await _calcular_suma_movimientos(db_session, libro_id)
    await db_session.refresh(libro_db_1)
    assert libro_db_1.stock == 40
    assert suma_3 == 40
    assert libro_db_1.stock == suma_3

    # 4. Intento fallido de alterar stock por PATCH
    res_patch = await app_client.patch(
        f"/libros/{libro_id}",
        json={"stock": 999},
    )
    assert res_patch.status_code == 422

    # Invariante se mantiene intacta tras el 422
    suma_4 = await _calcular_suma_movimientos(db_session, libro_id)
    await db_session.refresh(libro_db_1)
    assert libro_db_1.stock == 40
    assert suma_4 == 40
    assert libro_db_1.stock == suma_4

    # 5. Intento fallido de reposición con cantidad negativa
    res_neg = await app_client.post(
        f"/libros/{libro_id}/reponer",
        json={"cantidad": -10},
    )
    assert res_neg.status_code == 422

    suma_5 = await _calcular_suma_movimientos(db_session, libro_id)
    await db_session.refresh(libro_db_1)
    assert libro_db_1.stock == 40
    assert suma_5 == 40
    assert libro_db_1.stock == suma_5

    # 6. Histórico auditado refleja exactamente los 3 movimientos realizados
    res_historial = await app_client.get(f"/libros/{libro_id}/movimientos")
    assert res_historial.status_code == 200
    items = res_historial.json()["items"]
    assert len(items) == 3
    cantidades = [m["cantidad"] for m in items]
    assert cantidades == [10, 25, 5]
    assert sum(cantidades) == 40

