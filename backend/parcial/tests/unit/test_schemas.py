from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from parcial.app.modules.usuarios.schemas import (
    AsignacionRolResponse,
    AuthYoResponse,
    CambiarPasswordRequest,
    EventoSeguridadResponse,
    LoginRequest,
    RegistroRequest,
    RolAsignacionRequest,
    UsuarioConRolesResponse,
    UsuarioCreateRequest,
    UsuarioResponse,
)

CUARENTA_Y_DOS = "a" * 42


def test_registro_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        RegistroRequest(
            email="ana@example.com",
            nombre="Ana",
            password="secreto-seguro",
            campo_inesperado="x",
        )


def test_registro_accepts_password_of_exactly_72_bytes() -> None:
    payload = RegistroRequest(
        email="ana@example.com",
        nombre="Ana",
        password="a" * 72,
    )

    assert payload.password == "a" * 72


def test_registro_rejects_password_of_73_bytes() -> None:
    with pytest.raises(ValidationError):
        RegistroRequest(
            email="ana@example.com",
            nombre="Ana",
            password="a" * 73,
        )


def test_password_limit_is_measured_in_utf8_bytes_not_characters() -> None:
    # "á" encodes as two UTF-8 bytes: 36 chars == 72 bytes, 37 chars == 74 bytes.
    assert RegistroRequest(
        email="ana@example.com",
        nombre="Ana",
        password="á" * 36,
    ).password == "á" * 36

    with pytest.raises(ValidationError):
        RegistroRequest(
            email="ana@example.com",
            nombre="Ana",
            password="á" * 37,
        )


def test_login_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(
            email="ana@example.com",
            password="secreto-seguro",
            role="ADMIN",
        )


def test_cambiar_password_rejects_oversized_new_password() -> None:
    with pytest.raises(ValidationError):
        CambiarPasswordRequest(
            password_actual="secreto-seguro",
            password_nueva="a" * 73,
        )


def test_cambiar_password_rejects_oversized_current_password() -> None:
    with pytest.raises(ValidationError):
        CambiarPasswordRequest(
            password_actual="a" * 73,
            password_nueva="secreto-seguro",
        )


def test_usuario_create_accepts_staff_roles() -> None:
    for rol in ("ADMIN", "VENDEDOR"):
        payload = UsuarioCreateRequest(
            email=f"{rol.lower()}@example.com",
            nombre="Personal",
            password=CUARENTA_Y_DOS,
            rol=rol,
        )
        assert payload.rol == rol


def test_usuario_create_rejects_cliente_role_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        UsuarioCreateRequest(
            email="cliente@example.com",
            nombre="Cliente",
            password=CUARENTA_Y_DOS,
            rol="CLIENTE",
        )

    with pytest.raises(ValidationError):
        UsuarioCreateRequest(
            email="admin@example.com",
            nombre="Admin",
            password=CUARENTA_Y_DOS,
            rol="ADMIN",
            activo=True,
        )


def test_rol_asignacion_rejects_naive_vence_en() -> None:
    with pytest.raises(ValidationError):
        RolAsignacionRequest(
            rol="VENDEDOR",
            vence_en=datetime(2030, 1, 1, 12, 0, 0),
        )


def test_rol_asignacion_rejects_past_vence_en() -> None:
    with pytest.raises(ValidationError):
        RolAsignacionRequest(
            rol="VENDEDOR",
            vence_en=datetime.now(timezone.utc) - timedelta(minutes=1),
        )


def test_rol_asignacion_accepts_future_aware_vence_en() -> None:
    futuro = datetime.now(timezone.utc) + timedelta(days=30)

    payload = RolAsignacionRequest(rol="VENDEDOR", vence_en=futuro)

    assert payload.vence_en == futuro


def test_response_models_never_declare_password_hash() -> None:
    for model in (
        UsuarioResponse,
        UsuarioConRolesResponse,
        AsignacionRolResponse,
        EventoSeguridadResponse,
        AuthYoResponse,
    ):
        assert "password_hash" not in model.model_fields


def test_usuario_con_roles_serializes_without_password_hash() -> None:
    payload = UsuarioConRolesResponse(
        id=1,
        email="ana@example.com",
        nombre="Ana",
        activo=True,
        debe_cambiar_password=False,
        roles=["CLIENTE"],
    )

    assert "password_hash" not in payload.model_dump()


async def test_http_layer_maps_contract_errors_to_422_never_500() -> None:
    app = FastAPI()

    @app.post("/registro")
    async def registro(payload: RegistroRequest) -> dict[str, str]:
        return {"email": payload.email}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        extra_field = await client.post(
            "/registro",
            json={
                "email": "ana@example.com",
                "nombre": "Ana",
                "password": "secreto-seguro",
                "inesperado": "x",
            },
        )
        oversize = await client.post(
            "/registro",
            json={
                "email": "ana@example.com",
                "nombre": "Ana",
                "password": "a" * 73,
            },
        )
        valid = await client.post(
            "/registro",
            json={
                "email": "ana@example.com",
                "nombre": "Ana",
                "password": "a" * 72,
            },
        )

    assert extra_field.status_code == 422
    assert oversize.status_code == 422
    assert valid.status_code == 200
