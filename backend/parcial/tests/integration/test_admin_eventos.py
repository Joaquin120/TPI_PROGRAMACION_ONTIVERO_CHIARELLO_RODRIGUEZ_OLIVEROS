import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.app.modules.usuarios.models import EventoSeguridad
from parcial.tests.integration.helpers import crear_admin, login, registrar


async def test_listado_eventos_sin_sesion_responde_401(app_client: AsyncClient) -> None:
    respuesta = await app_client.get("/eventos")
    assert respuesta.status_code == 401


async def test_listado_eventos_usuario_no_admin_responde_403(
    app_client: AsyncClient,
) -> None:
    await registrar(app_client, "cliente@example.com")
    await login(app_client, "cliente@example.com")
    respuesta = await app_client.get("/eventos")
    assert respuesta.status_code == 403


async def test_listado_eventos_devuelve_envoltorio_paginado_y_default_20(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)

    async with db_sessionmaker() as session:
        for i in range(25):
            session.add(
                EventoSeguridad(
                    actor="sistema@example.com",
                    accion=f"ACCION_{i}",
                )
            )
        await session.commit()

    respuesta = await app_client.get("/eventos")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"items", "total", "page", "size", "pages"}
    assert cuerpo["total"] >= 25
    assert cuerpo["page"] == 1
    assert cuerpo["size"] == 20
    assert cuerpo["pages"] >= 2
    assert len(cuerpo["items"]) == 20

    primer_evento = cuerpo["items"][0]
    assert "id" in primer_evento
    assert "cuando" in primer_evento
    assert "actor" in primer_evento
    assert "accion" in primer_evento
    assert "password_hash" not in respuesta.text


async def test_listado_eventos_pagina_inexistente_responde_422(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await crear_admin(app_client, db_sessionmaker)

    respuesta = await app_client.get("/eventos", params={"page": 999, "size": 20})

    assert respuesta.status_code == 422
