import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from src.core.config import get_settings
from src.db.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """ASGI Lifespan manager handling atomic startup validation and clean shutdown."""
    settings = get_settings()

    # Startup: execute SELECT 1 ping to verify database connectivity
    try:
        async with engine.connect() as conn:
            await asyncio.wait_for(
                conn.execute(text("SELECT 1")),
                timeout=settings.DB_TIMEOUT,
            )
        logger.info("Database connectivity check succeeded.")
    except Exception as exc:
        logger.critical("Database connectivity check failed during startup: %s", exc)
        raise

    try:
        yield
    finally:
        # Shutdown: cleanly dispose connection pool
        await engine.dispose()
        logger.info("Database connection pool disposed.")
