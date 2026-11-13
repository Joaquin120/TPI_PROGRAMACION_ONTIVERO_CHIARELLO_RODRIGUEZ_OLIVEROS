# Proposal: C-07 Ventas - Historial, Detalle e Invariante de Precio Histórico

## Why

Tras implementar el borrador de venta en memoria y la confirmación transaccional (`POST /api/ventas/`) en `C-06`, el sistema aún no expone la consulta paginada del historial ni el detalle histórico inmutable de ventas (`US-008`), ni permite actualizar el precio de un libro vía `PATCH /api/libros/{id}` para verificar el invariante de precio histórico (`RN-VEN-05` / Caso `G-05`). Además, `frontend/public/index.html` y `frontend/public/js/app.js` conservaban lógica heredada con `localStorage`, y la cadena de migraciones Alembic necesitaba `002b_create_catalogo_libros.py` y el ajuste de `alembic.ini` para poder crear las tablas referenciadas por `003_create_ventas.py` en PostgreSQL.

## What Changes

- **Backend**:
  - Agregar endpoints `GET /ventas/` (paginado con `limit` `1..100` por defecto `20`, `offset >= 0`, ordenado descendente por `id`) y `GET /ventas/{venta_id}` (`200` / `404`) en `backend/src/api/v1/endpoints/ventas.py`.
  - Agregar esquema `LibroUpdate` en `backend/src/schemas/libro.py` y endpoint parcial `PATCH /libros/{libro_id}` en `backend/src/api/v1/endpoints/libros.py` (con validaciones `404`, `409` por ISBN duplicado y `422`) garantizando que no se alteren los importes congelados en `ventas_renglones`.
  - Incorporar la migración `backend/alembic/versions/002b_create_catalogo_libros.py`, encadenar `003_create_ventas.py` sobre `002b` y corregir `version_locations` en `backend/alembic.ini`.
- **Frontend**:
  - Crear `frontend/public/js/history.js` para consultar `GET /api/ventas/` (paginación con `limit` y `offset`) y `GET /api/ventas/{id}`, renderizando el detalle histórico inmutable sin `localStorage` ni controles de edición o eliminación.
  - Actualizar `frontend/public/js/sales.js` (edición de cantidad en borrador y panel oficial `#venta-confirmada-detalle` tras `201 Created`) y `frontend/public/js/books.js` (listado de libros registrados y formulario `#form-actualizar-precio-libro` contra `PATCH /api/libros/{id}`).
  - Limpiar `frontend/public/index.html`, `frontend/public/css/estilos.css` y `frontend/public/js/app.js` eliminando datos simulados y `localStorage`, asegurando además que:
    - los selectores de libros en Ventas (`#venta-libro`) y Actualizar precio (`#libro-precio-editar-id`) no queden recortados ni filtrados por la búsqueda/paginación visual de `#vista-catalogo`;
    - al confirmar una venta, el historial reinicie `offset = 0` antes de recargarse.
- **Pruebas automatizadas**:
  - Ampliar tests de backend (`test_ventas_api.py`, `test_libro_schemas.py`, `test_migrations.py`) y frontend (`history.test.js`, `sales.test.js`, `books.test.js`) cubriendo `US-008` y `G-05`.

## Capabilities

### New Capabilities
<!-- Sin nuevas capabilities: el alcance amplía las reglas de sales-management. -->

### Modified Capabilities
- `sales-management`: agregar requisitos de consulta paginada de historial (`GET /api/ventas/`), consulta de detalle histórico inmutable (`GET /api/ventas/{id}`), visualización del comprobante oficial tras confirmación (`#venta-confirmada-detalle`), ajuste de precio de catálogo (`PATCH /api/libros/{id}`) e invariante de precio histórico (`RN-VEN-05` / Caso `G-05`), además del desacoplamiento de selectores y refresco del historial en página 1.

## Impact

- **Backend**: `backend/src/api/v1/endpoints/ventas.py`, `backend/src/api/v1/endpoints/libros.py`, `backend/src/schemas/libro.py`, `backend/src/schemas/__init__.py`, `backend/alembic.ini`, `backend/alembic/versions/002b_create_catalogo_libros.py`, `backend/alembic/versions/003_create_ventas.py`.
- **Frontend**: `frontend/public/index.html`, `frontend/public/css/estilos.css`, `frontend/public/js/app.js`, `frontend/public/js/books.js`, `frontend/public/js/sales.js`, `frontend/public/js/history.js`.
- **Tests**: `backend/tests/integration/test_migrations.py`, `backend/tests/integration/test_ventas_api.py`, `backend/tests/unit/test_libro_schemas.py`, `frontend/public/js/history.test.js`, `frontend/public/js/sales.test.js`, `frontend/public/js/books.test.js`.
- **Compatibilidad**: Sin cambios **BREAKING** en contratos existentes.
