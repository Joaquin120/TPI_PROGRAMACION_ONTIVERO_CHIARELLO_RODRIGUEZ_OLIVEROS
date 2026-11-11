from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from parcial.tests.integration.helpers import (
    PASSWORD_TEMPORAL,
    asignar_rol,
    crear_admin,
    login,
    obtener_id,
    registrar,
)


def _futuro(dias: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()


ADMIN_ENDPOINTS = [
    ("POST", "/usuarios", {
        "email": "personal_matrix@example.com",
        "nombre": "Personal Matrix",
        "password": PASSWORD_TEMPORAL,
        "rol": "VENDEDOR",
    }),
    ("GET", "/usuarios/1/roles", None),
    ("POST", "/usuarios/1/roles", {"rol": "VENDEDOR", "vence_en": _futuro()}),
    ("DELETE", "/usuarios/1/roles/VENDEDOR", None),
    ("GET", "/eventos", None),
]


@pytest.mark.parametrize("metodo,path,body", ADMIN_ENDPOINTS)
async def test_endpoint_admin_sin_sesion_responde_401(
    app_client: AsyncClient,
    metodo: str,
    path: str,
    body: dict | None,
) -> None:
    res = await app_client.request(metodo, path, json=body)
    assert res.status_code == 401, f"{metodo} {path} esperado 401, recibido {res.status_code}"


@pytest.mark.parametrize("metodo,path,body", ADMIN_ENDPOINTS)
async def test_endpoint_admin_con_rol_cliente_responde_403(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    metodo: str,
    path: str,
    body: dict | None,
) -> None:
    email = "cliente_matrix@example.com"
    await registrar(app_client, email)
    await login(app_client, email)

    res = await app_client.request(metodo, path, json=body)
    assert res.status_code == 403, f"{metodo} {path} esperado 403, recibido {res.status_code}"


@pytest.mark.parametrize("metodo,path,body", ADMIN_ENDPOINTS)
async def test_endpoint_admin_con_rol_vendedor_responde_403(
    app_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    metodo: str,
    path: str,
    body: dict | None,
) -> None:
    email = "vendedor_matrix@example.com"
    await registrar(app_client, email)
    await asignar_rol(db_sessionmaker, email, "VENDEDOR")
    await login(app_client, email)

    res = await app_client.request(metodo, path, json=body)
    assert res.status_code == 403, f"{metodo} {path} esperado 403, recibido {res.status_code}"

