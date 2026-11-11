import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging
import bcrypt
from fastapi import APIRouter, Depends, FastAPI, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from parcial.app.core.config import get_settings
from parcial.app.core.database import async_session_factory, engine
from parcial.app.core.dependencies import verificar_no_debe_cambiar_password
from parcial.app.modules.clientes.router import clientes_router
from parcial.app.modules.libros.router import (
    catalogo_admin_router,
    catalogo_open_router,
)
from parcial.app.modules.usuarios.admin_router import admin_router, eventos_router
from parcial.app.modules.usuarios.router import auth_router
from parcial.app.modules.ventas.router import mis_ventas_router, ventas_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """ASGI Lifespan manager for the Parcial application.

    Crucial Architectural Rules (CONSIGNA_PARCIAL §2.3, AGENTS.md):
    - Precomputes app.state.fictitious_password_hash with bcrypt to mitigate timing attacks.
    - Stores engine and sessionmaker in app.state.
    - Cleanly disposes the connection pool on shutdown.
    """
    settings = get_settings()

    # Store engine and session factory on app state
    app.state.engine = engine
    app.state.sessionmaker = async_session_factory

    # Precalculate fictitious password hash with bcrypt off the event loop
    fictitious_pw = b"timing-attack-mitigation-fictitious-password"
    salt = await asyncio.to_thread(bcrypt.gensalt, rounds=settings.BCRYPT_ROUNDS)
    app.state.fictitious_password_hash = (
        await asyncio.to_thread(bcrypt.hashpw, fictitious_pw, salt)
    ).decode("utf-8")
    logger.info("Fictitious password hash precomputed in application state.")

    try:
        yield
    finally:
        # Shutdown: cleanly dispose of connection pool
        await engine.dispose()
        logger.info("Database engine disposed on shutdown.")


# Initialize FastAPI app
app = FastAPI(
    title="Parcial Librería Backend",
    description="Backend asíncrono con FastAPI y PostgreSQL (Parcial Capítulos 1 a 6)",
    version="0.1.0",
    lifespan=lifespan,
)

# --- 1. Grupo Abierto ---
# /health/*, /auth/registro, /auth/login, /auth/logout, /auth/yo, /auth/cambiar-password, catálogo público
open_router = APIRouter(tags=["Grupo Abierto"])


@open_router.get("/health", status_code=status.HTTP_200_OK)
@open_router.get("/health/live", status_code=status.HTTP_200_OK)
async def health_live() -> dict[str, str]:
    """Liveness probe: verifies process is running without checking external dependencies."""
    return {"status": "healthy"}


@open_router.get("/health/ready", status_code=status.HTTP_200_OK, response_model=None)
async def health_ready() -> Response:
    """Readiness probe: actively verifies database connectivity with a 2-second timeout."""
    settings = get_settings()
    try:
        async with engine.connect() as conn:
            await asyncio.wait_for(
                conn.execute(text("SELECT 1")),
                timeout=settings.DB_TIMEOUT,
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready", "database": "connected"},
        )
    except Exception as exc:
        logger.warning("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected"},
        )


# --- 2. Grupo Protegido ---
# Custodiado centralizadamente por debe_cambiar_password == false (HTTP 403 Forbidden si es true)
protected_router = APIRouter(
    dependencies=[Depends(verificar_no_debe_cambiar_password)],
    tags=["Grupo Protegido"],
)


@protected_router.get("/protected/ping", status_code=status.HTTP_200_OK)
async def protected_ping() -> dict[str, str]:
    """Sample protected endpoint to verify route group security enforcement."""
    return {"status": "ok"}


protected_router.include_router(admin_router)
protected_router.include_router(eventos_router)
protected_router.include_router(catalogo_admin_router)
protected_router.include_router(clientes_router)
protected_router.include_router(ventas_router)
protected_router.include_router(mis_ventas_router)


# Mount routers on application
open_router.include_router(auth_router)
open_router.include_router(catalogo_open_router)
app.include_router(open_router)
app.include_router(protected_router)
