"""Password hashing and JWT helpers for the Parcial backend.

Crucial Rule (CONSIGNA_PARCIAL §2):
- bcrypt work MUST run off the event loop because it is CPU-bound and would
  otherwise block every coroutine served by the process.
- Concurrency is bounded by an ``asyncio.Semaphore`` sized from
  ``Settings.BCRYPT_MAX_CONCURRENCY`` so parallel requests cannot exhaust the
  CPU or saturate the thread pool used by ``asyncio.to_thread``.
- Passwords MUST be rejected when their UTF-8 encoding exceeds bcrypt's 72-byte
  limit, both before hashing (DTO validation) and during verification (defence
  in depth), so an oversized input can never surface as an HTTP 500.
"""

import asyncio
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from parcial.app.core.config import get_settings

MAX_PASSWORD_BYTES = 72
ACCESS_TOKEN_COOKIE = "access_token"

_bcrypt_semaphore: asyncio.Semaphore | None = None


def get_bcrypt_semaphore() -> asyncio.Semaphore:
    """Returns the process-wide semaphore bounding concurrent bcrypt work."""
    global _bcrypt_semaphore
    if _bcrypt_semaphore is None:
        _bcrypt_semaphore = asyncio.Semaphore(get_settings().BCRYPT_MAX_CONCURRENCY)
    return _bcrypt_semaphore


def reset_bcrypt_semaphore() -> None:
    """Drops the cached semaphore so the next call rebuilds it from settings."""
    global _bcrypt_semaphore
    _bcrypt_semaphore = None


async def hash_password(password: str) -> str:
    """Hashes a plaintext password with bcrypt without blocking the event loop."""
    settings = get_settings()
    password_bytes = password.encode("utf-8")
    salt = await asyncio.to_thread(bcrypt.gensalt, rounds=settings.BCRYPT_ROUNDS)

    async with get_bcrypt_semaphore():
        hashed = await asyncio.to_thread(bcrypt.hashpw, password_bytes, salt)

    return hashed.decode("utf-8")


async def verify_password(password: str, password_hash: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash.

    Returns ``False`` instead of raising for inputs bcrypt cannot process
    (oversized UTF-8 payloads or malformed hashes), keeping failures mapped to
    401/422 responses rather than 500.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_PASSWORD_BYTES:
        return False

    async with get_bcrypt_semaphore():
        try:
            return await asyncio.to_thread(
                bcrypt.checkpw,
                password_bytes,
                password_hash.encode("utf-8"),
            )
        except ValueError:
            return False


def crear_token_acceso(
    usuario_id: int,
    email: str,
    roles: Sequence[str] = (),
) -> str:
    """Builds a signed JWT carrying the user identity and informational roles."""
    settings = get_settings()
    ahora = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(usuario_id),
        "email": email,
        "roles": list(roles),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> dict[str, Any]:
    """Decodes and validates a JWT, raising ``jwt.InvalidTokenError`` on failure."""
    settings = get_settings()
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
