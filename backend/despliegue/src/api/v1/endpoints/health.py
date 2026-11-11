import asyncio
import logging
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.core.config import get_settings
from src.db.session import engine
from src.schemas.health import HealthStatusResponse, ReadinessResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
@router.get(
    "/health/live",
    response_model=HealthStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe (live alias)",
)
async def get_health_live() -> HealthStatusResponse:
    """Returns 200 OK immediately to verify the process is alive without external deps."""
    settings = get_settings()
    return HealthStatusResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": ReadinessResponse},
        503: {"model": ReadinessResponse},
    },
    summary="Readiness probe",
)
async def get_health_ready() -> JSONResponse | ReadinessResponse:
    """Actively checks database connectivity with a timeout; returns 503 if unavailable."""
    settings = get_settings()
    try:
        async with engine.connect() as conn:
            await asyncio.wait_for(
                conn.execute(text("SELECT 1")),
                timeout=settings.DB_TIMEOUT,
            )
        return ReadinessResponse(status="ready", database="connected")
    except Exception as exc:
        logger.warning("Readiness probe check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ReadinessResponse(
                status="unhealthy",
                database="disconnected",
            ).model_dump(),
        )
