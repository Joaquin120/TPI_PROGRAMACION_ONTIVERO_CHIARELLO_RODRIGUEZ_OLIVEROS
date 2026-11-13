# Design: C-07 Ventas - Historial, Detalle e Invariante de Precio Histórico

## Context

Ver `proposal.md` para la motivación y alcance (`US-008`, `RN-VEN-05` y Caso `G-05`).
El backend ya cuenta con `POST /ventas/` y las tablas `ventas` y `ventas_renglones` (`precio_unitario` y `subtotal` congelados) en `003_create_ventas.py`. El frontend ya dispone de los módulos `api.js`, `catalog.js`, `books.js`, `clients.js` y `sales.js`, aunque `index.html` y `app.js` aún requieren completar la orquestación sin `localStorage` ni datos simulados y corregir la cadena de migraciones previas (`002b`) para poder ejecutar `alembic upgrade head` en PostgreSQL.

## Goals / Non-Goals

**Goals:**
- Exponer `GET /ventas/` (paginación `limit`/`offset`, orden `Venta.id.desc()`) y `GET /ventas/{venta_id}` (`404` si no existe) en `backend/src/api/v1/endpoints/ventas.py`.
- Exponer `PATCH /libros/{libro_id}` con esquema `LibroUpdate` validando `404`, `409` (ISBN único) y `422` (campos o claves foráneas inválidas), manteniendo intactos los registros en `ventas_renglones`.
- Incorporar `002b_create_catalogo_libros.py`, encadenar `003_create_ventas.py` sobre `002b` y fijar `version_locations` en `backend/alembic.ini` para evitar colisiones con `parcial/migrations`.
- Crear `frontend/public/js/history.js` para historial paginado y detalle histórico inmutable (sin `localStorage` ni controles de edición/borrado), extender `sales.js` y `books.js`, y consolidar `app.js` / `index.html`.
- Garantizar mediante `app.js` que la recarga de selectores (`#venta-libro`, `#libro-precio-editar-id`) no dependa del filtro/paginación de `#vista-catalogo`, y que al confirmar una venta el historial reinicie `offset = 0`.
- Asegurar cobertura unitaria y de integración en `pytest` y `node --test`.

**Non-Goals:**
- No alterar el cálculo ni el contrato de `POST /ventas/` ni agregar descuento automático de `stock` (fuera del alcance definido de `C-06`/`C-07`).
- No modificar el formato de respuesta en lista plana JSON de `GET /ventas/` ni de `GET /libros/`.
- No incluir documentación de despliegue Easypanel, `seed.py` ni evidencias públicas `G-01`..`G-07` (reservado para `C-09`).

## Decisions

### 1. Endpoints de Historial (`GET /ventas/` y `GET /ventas/{venta_id}`)
- **Decisión**: Reutilizar un helper `_build_venta_response` en `ventas.py` y cargar relaciones `Venta.cliente` y `Venta.renglones -> VentaRenglon.libro` con `selectinload`, ordenando `GET /ventas/` por `Venta.id.desc()`.
- **Alternativas consideradas**:
  - *Devolver objeto envoltorio `{ items, total }`*: Descartado para mantener simetría con `GET /libros/` y evitar cambios innecesarios de contrato respecto a la consigna.

### 2. Actualización Parcial de Libros (`PATCH /libros/{libro_id}`)
- **Decisión**: Definir `LibroUpdate` en `backend/src/schemas/libro.py` con todos sus campos opcionales y usar `model_fields_set` en `update_libro` para distinguir campos omitidos de campos enviados explícitamente (por ejemplo `genero_id: null` para quitar el género), validando `409` ante ISBN duplicado en otro libro y `422` ante `editorial_id`/`genero_id` inexistentes.
- **Alternativas consideradas**:
  - *Exponer únicamente `PATCH /libros/{id}/precio`*: Descartado porque la consigna y `G-05` especifican `PATCH /api/libros/{id}`.

### 3. Encadenamiento de Migraciones Alembic (`002b`)
- **Decisión**: Insertar `002b_create_catalogo_libros.py` (`down_revision = "002"`) antes de `003_create_ventas.py` (`down_revision = "002b"`) y limitar `version_locations` en `backend/alembic.ini` a `%(here)s/alembic/versions`.
- **Alternativas consideradas**:
  - *Reescribir `001` o `002`*: Descartado para preservar intacto el historial ya archivado de migraciones previas.

### 4. Desacoplamiento de Selectores y Refresco Post-Venta en Frontend (`app.js`)
- **Decisión**: Separar la carga del listado de catálogo visible (`cargarCatalogoApi`, sujeto a búsqueda y paginación de `#vista-catalogo`) de la sincronización de selectores operativos (`#venta-libro`, `#libro-precio-editar-id`, `#tabla-libros`) mediante una consulta independiente `/libros/` con límite amplio (`limit=100, offset=0` sin filtro `titulo`), y reiniciar `estadoHistorial.offset = 0` en el callback `onExito` de confirmación de venta antes de recargar el historial.
- **Alternativas consideradas**:
  - *Reutilizar el array filtrado `estadoCatalogo.libros` para llenar `#venta-libro` y `#libro-precio-editar-id`*: Descartado porque una búsqueda sin coincidencias o el cambio de página en el catálogo deja vacíos o incompletos los selectores de Ventas y de ajuste de precio.

## Risks / Trade-offs

- **[Catálogo mayor a 100 libros en selectores sin buscador dedicado]** → **Mitigación**: Usar `limit=100, offset=0` cubre holgadamente el volumen del TPI y evita dependencias con el filtro del catálogo; si a futuro crece el catálogo, `GET /api/libros/` ya soporta paginación incremental.
- **[Pruebas de integración de ventas sobre sesión en memoria (`FakeVentasAsyncSession`)]** → **Mitigación**: Complementar la cobertura de `FakeVentasAsyncSession` soportando `Editorial`/`Genero` o consultas en memoria y validar la cadena de migraciones reales mediante `test_migrations.py` sobre SQLite, dejando la verificación con PostgreSQL real para el arranque contenedorizado.

## Migration Plan

1. Ejecutar `alembic upgrade head` para aplicar `001 -> 002 -> 002b -> 003` limpiamente.
2. Verificar suites de backend (`pytest`) y frontend (`node --test`).
3. Validar `openspec validate c-07-ventas-historial-detalle --strict --json`.
