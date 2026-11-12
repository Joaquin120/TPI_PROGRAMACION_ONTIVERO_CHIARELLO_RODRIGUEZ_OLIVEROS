from fastapi import APIRouter

from src.api.v1.endpoints import health, items, libros

api_router = APIRouter()

# Root level health routes: /health, /health/live, /health/ready
api_router.include_router(health.router)

# Versioned API routes: /api/v1/health, /api/v1/health/live, /api/v1/health/ready
api_router.include_router(health.router, prefix="/api/v1")

# Item routes mounted at root (/items) and versioned (/api/v1/items)
api_router.include_router(items.router, prefix="/items")
api_router.include_router(items.router, prefix="/api/v1/items")

# Libros routes mounted at root (/libros) and versioned (/api/v1/libros)
api_router.include_router(libros.router, prefix="/libros")
api_router.include_router(libros.router, prefix="/api/v1/libros")
