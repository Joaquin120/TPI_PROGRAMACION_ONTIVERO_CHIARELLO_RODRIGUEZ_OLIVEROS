from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from parcial.app.modules.usuarios import router as usuarios_router

PASSWORD = "secreto-seguro"
EMAIL = "ana@example.com"


async def _registrar_y_loguear(client: AsyncClient) -> None:
    registro = await client.post(
        "/auth/registro",
        json={"email": EMAIL, "nombre": "Ana", "password": PASSWORD},
    )
    assert registro.status_code == 201
    login = await client.post(
        "/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert login.status_code == 200


async def test_login_setea_cookie_httponly_samesite_y_max_age(
    app_client: AsyncClient,
) -> None:
    await _registrar_y_loguear(app_client)

    respuesta = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )

    assert respuesta.status_code == 200
    cabecera = respuesta.headers["set-cookie"].lower()
    assert "access_token=" in cabecera
    assert "httponly" in cabecera
    assert "samesite=lax" in cabecera
    assert "max-age=3600" in cabecera
    assert "path=/" in cabecera
    assert "secure" not in cabecera

    cuerpo = respuesta.json()
    assert "access_token" not in cuerpo
    assert "token" not in cuerpo


async def test_cookie_secure_es_configurable(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        usuarios_router,
        "get_settings",
        lambda: SimpleNamespace(
            COOKIE_SECURE=True,
            ACCESS_TOKEN_EXPIRE_MINUTES=60,
        ),
    )
    await _registrar_y_loguear(app_client)

    respuesta = await app_client.post(
        "/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )

    assert respuesta.status_code == 200
    assert "secure" in respuesta.headers["set-cookie"].lower()


async def test_logout_elimina_la_cookie_y_responde_204(
    app_client: AsyncClient,
) -> None:
    await _registrar_y_loguear(app_client)

    respuesta = await app_client.post("/auth/logout")

    assert respuesta.status_code == 204
    cabecera = respuesta.headers["set-cookie"].lower()
    assert "access_token=" in cabecera
    assert "max-age=0" in cabecera


async def test_authorization_bearer_es_rechazado(
    app_client: AsyncClient,
) -> None:
    respuesta = await app_client.get(
        "/auth/yo",
        headers={"Authorization": "Bearer token-en-cabecera"},
    )

    assert respuesta.status_code == 401


async def test_cookie_presente_con_bearer_adicional_es_rechazada(
    app_client: AsyncClient,
) -> None:
    await _registrar_y_loguear(app_client)

    respuesta = await app_client.get(
        "/auth/yo",
        headers={"Authorization": "Bearer token-extra"},
    )

    assert respuesta.status_code == 401


async def test_sin_cookie_responde_401(
    app_client: AsyncClient,
) -> None:
    respuesta = await app_client.get("/auth/yo")

    assert respuesta.status_code == 401
