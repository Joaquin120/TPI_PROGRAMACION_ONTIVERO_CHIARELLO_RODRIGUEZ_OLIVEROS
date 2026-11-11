import threading
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import pytest

from parcial.app.core import security
from parcial.app.core.config import get_settings


@pytest.fixture(autouse=True)
def reset_security_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensures every test starts with a fresh settings cache and semaphore."""
    monkeypatch.setenv("BCRYPT_ROUNDS", "4")
    get_settings.cache_clear()
    security.reset_bcrypt_semaphore()
    yield
    security.reset_bcrypt_semaphore()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_hash_and_verify_password_round_trip() -> None:
    password = "secreto-seguro"
    password_hash = await security.hash_password(password)

    assert password_hash.startswith("$2")
    assert await security.verify_password(password, password_hash) is True
    assert await security.verify_password("otra-clave", password_hash) is False


@pytest.mark.asyncio
async def test_hash_runs_off_the_event_loop_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    observed_threads: list[str] = []
    original_hashpw = bcrypt.hashpw

    def spy_hashpw(password: bytes, salt: bytes) -> bytes:
        observed_threads.append(threading.current_thread().name)
        return original_hashpw(password, salt)

    monkeypatch.setattr(security.bcrypt, "hashpw", spy_hashpw)

    await security.hash_password("secreto-seguro")

    assert observed_threads
    assert observed_threads[0] != threading.current_thread().name


@pytest.mark.asyncio
async def test_semaphore_uses_configured_concurrency_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BCRYPT_MAX_CONCURRENCY", "2")
    get_settings.cache_clear()
    security.reset_bcrypt_semaphore()

    semaphore = security.get_bcrypt_semaphore()

    assert semaphore._value == 2


def test_jwt_round_trip_includes_subject_email_and_roles() -> None:
    token = security.crear_token_acceso(
        usuario_id=7,
        email="ana@example.com",
        roles=["CLIENTE", "VENDEDOR"],
    )

    payload = security.decodificar_token(token)

    assert payload["sub"] == "7"
    assert payload["email"] == "ana@example.com"
    assert payload["roles"] == ["CLIENTE", "VENDEDOR"]
    assert "exp" in payload
    assert "iat" in payload


def test_invalid_token_is_rejected() -> None:
    with pytest.raises(jwt.InvalidTokenError):
        security.decodificar_token("esto-no-es-un-jwt")


def test_expired_token_is_rejected() -> None:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {
            "sub": "1",
            "email": "ana@example.com",
            "roles": ["CLIENTE"],
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=5),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        security.decodificar_token(expired_token)


@pytest.mark.asyncio
async def test_verify_password_rejects_over_72_bytes_without_raising() -> None:
    password_hash = await security.hash_password("secreto-seguro")

    assert await security.verify_password("á" * 37, password_hash) is False
