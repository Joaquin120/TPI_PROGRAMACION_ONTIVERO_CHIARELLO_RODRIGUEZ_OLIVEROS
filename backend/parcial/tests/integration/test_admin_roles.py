from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.modules.usuarios.models import AsignacionRol
from parcial.tests.integration.helpers import (
    crear_admin,
    obtener_id,
    registrar,
)

OBJETIVO = "objetivo@example.com"


def _futuro(dias: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()


async def _preparar(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> int:
    """Logs in as ADMIN and registers a target user with its CLIENTE role."""
    await crear_admin(app_client, db_sessionmaker)
    await registrar(app_client, OBJETIVO)
    return await obtener_id(db_sessionmaker, OBJETIVO)


async def test_listado_de_roles_devuelve_el_envoltorio_paginado(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    objetivo_id = await _preparar(app_client, db_sessionmaker)

    respuesta = await app_client.get(f"/usuarios/{objetivo_id}/roles")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"items", "total", "page", "size", "pages"}
    assert cuerpo["total"] == 1
    assert cuerpo["page"] == 1
    assert cuerpo["size"] == 20
    assert cuerpo["pages"] == 1
    asignacion = cuerpo["items"][0]
    assert asignacion["usuario_id"] == objetivo_id
    assert asignacion["rol"] == "CLIENTE"
    assert asignacion["revocada_en"] is None
    assert "password_hash" not in respuesta.text


async def test_listado_de_roles_pagina_y_rechaza_pagina_inexistente(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    objetivo_id = await _preparar(app_client, db_sessionmaker)

    primera = await app_client.get(
        f"/usuarios/{objetivo_id}/roles",
        params={"page": 1, "size": 1},
    )
    inexistente = await app_client.get(
        f"/usuarios/{objetivo_id}/roles",
        params={"page": 99, "size": 1},
    )

    assert primera.status_code == 200
    assert primera.json()["size"] == 1
    assert len(primera.json()["items"]) == 1
    assert inexistente.status_code == 422


async def test_listado_de_roles_de_usuario_inexistente_responde_404(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)

    respuesta = await app_client.get("/usuarios/9999/roles")

    assert respuesta.status_code == 404


async def test_asignacion_de_rol_persiste_y_responde_201(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    objetivo_id = await _preparar(app_client, db_sessionmaker)

    respuesta = await app_client.post(
        f"/usuarios/{objetivo_id}/roles",
        json={"rol": "VENDEDOR", "vence_en": _futuro()},
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["usuario_id"] == objetivo_id
    assert cuerpo["rol"] == "VENDEDOR"
    assert cuerpo["revocada_en"] is None
    assert cuerpo["otorgada_por"] is not None
    assert "password_hash" not in respuesta.text

    async with db_sessionmaker() as session:
        asignaciones = (
            await session.execute(
                select(AsignacionRol).where(
                    AsignacionRol.usuario_id == objetivo_id,
                    AsignacionRol.rol == "VENDEDOR",
                )
            )
        ).scalars().all()

    assert len(asignaciones) == 1
    assert asignaciones[0].revocada_en is None


async def test_asignacion_a_usuario_inexistente_responde_404(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)

    respuesta = await app_client.post(
        "/usuarios/9999/roles",
        json={"rol": "VENDEDOR", "vence_en": _futuro()},
    )

    assert respuesta.status_code == 404


@pytest.mark.parametrize(
    "vence_en",
    [
        (datetime.now() + timedelta(days=30)).isoformat(),  # naive (no tzinfo)
        (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),  # past
    ],
)
async def test_vence_en_naive_o_pasado_responde_422(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    vence_en: str,
) -> None:
    objetivo_id = await _preparar(app_client, db_sessionmaker)

    respuesta = await app_client.post(
        f"/usuarios/{objetivo_id}/roles",
        json={"rol": "VENDEDOR", "vence_en": vence_en},
    )

    assert respuesta.status_code == 422

    async with db_sessionmaker() as session:
        total = (
            await session.execute(
                select(AsignacionRol).where(
                    AsignacionRol.usuario_id == objetivo_id,
                    AsignacionRol.rol == "VENDEDOR",
                )
            )
        ).scalars().all()

    assert total == []


async def test_asignacion_activa_duplicada_responde_409(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    objetivo_id = await _preparar(app_client, db_sessionmaker)

    # ``registrar`` already granted a live CLIENTE assignment.
    duplicada = await app_client.post(
        f"/usuarios/{objetivo_id}/roles",
        json={"rol": "CLIENTE", "vence_en": _futuro()},
    )

    primera = await app_client.post(
        f"/usuarios/{objetivo_id}/roles",
        json={"rol": "VENDEDOR", "vence_en": _futuro()},
    )
    repetida = await app_client.post(
        f"/usuarios/{objetivo_id}/roles",
        json={"rol": "VENDEDOR", "vence_en": _futuro()},
    )

    assert duplicada.status_code == 409
    assert primera.status_code == 201
    assert repetida.status_code == 409

    async with db_sessionmaker() as session:
        asignaciones = (
            await session.execute(
                select(AsignacionRol).where(
                    AsignacionRol.usuario_id == objetivo_id,
                    AsignacionRol.rol == "VENDEDOR",
                )
            )
        ).scalars().all()

    assert len(asignaciones) == 1


async def test_reasignar_rol_revocado_es_permitido_y_queda_en_el_historial(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    objetivo_id = await _preparar(app_client, db_sessionmaker)

    primera = await app_client.post(
        f"/usuarios/{objetivo_id}/roles",
        json={"rol": "VENDEDOR", "vence_en": _futuro()},
    )
    assert primera.status_code == 201

    # Revocation frees the conditional unique index for a new assignment.
    async with db_sessionmaker() as session:
        asignacion = (
            await session.execute(
                select(AsignacionRol).where(
                    AsignacionRol.usuario_id == objetivo_id,
                    AsignacionRol.rol == "VENDEDOR",
                )
            )
        ).scalar_one()
        asignacion.revocada_en = datetime.now(timezone.utc)
        await session.commit()

    segunda = await app_client.post(
        f"/usuarios/{objetivo_id}/roles",
        json={"rol": "VENDEDOR", "vence_en": _futuro()},
    )
    listado = await app_client.get(f"/usuarios/{objetivo_id}/roles")

    assert segunda.status_code == 201
    historial = [
        item for item in listado.json()["items"] if item["rol"] == "VENDEDOR"
    ]
    assert len(historial) == 2
    assert sum(1 for item in historial if item["revocada_en"] is None) == 1
