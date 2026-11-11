from fastapi import FastAPI

from src.api.router import api_router
from src.core.config import get_settings
from src.core.lifespan import lifespan

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.include_router(api_router)
