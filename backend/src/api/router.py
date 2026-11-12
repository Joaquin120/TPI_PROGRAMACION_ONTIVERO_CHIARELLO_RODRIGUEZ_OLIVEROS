from fastapi import APIRouter

from src.api.v1.endpoints import autores, editoriales, generos, health, items, libros

api_router = APIRouter()

# Health routes
api_router.include_router(health.router)
api_router.include_router(health.router, prefix="/api/v1")

# Items routes
api_router.include_router(items.router, prefix="/items")
api_router.include_router(items.router, prefix="/api/v1/items")

# Libros routes
api_router.include_router(libros.router, prefix="/libros")
api_router.include_router(libros.router, prefix="/api/v1/libros")

# Editoriales routes
api_router.include_router(editoriales.router, prefix="/editoriales")
api_router.include_router(editoriales.router, prefix="/api/v1/editoriales")

# Generos routes
api_router.include_router(generos.router, prefix="/generos")
api_router.include_router(generos.router, prefix="/api/v1/generos")

# Autores routes
api_router.include_router(autores.router, prefix="/autores")
api_router.include_router(autores.router, prefix="/api/v1/autores")
