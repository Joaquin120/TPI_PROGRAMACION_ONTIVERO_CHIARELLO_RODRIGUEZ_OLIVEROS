# Proposal: C-06 Ventas - Borrador y Registro

## Why

Actualmente la vista de ventas en la interfaz web opera mediante una maqueta estática del Primer Parcial con datos ficticios y simulación local en memoria del navegador (`localStorage`), sin consumir la API REST ni persistir transacciones atómicas en PostgreSQL. Asimismo, el backend carece de los modelos relacionales `Venta` y `VentaRenglon` y del endpoint transaccional `POST /api/ventas/`. Es indispensable implementar el flujo de composición en memoria del borrador de venta y su confirmación transaccional (Ejercicio 3A / US-006, US-007) para registrar ventas asociadas a un cliente con múltiples renglones de libros, congelando los precios unitarios de catálogo, validando la unicidad de libros por renglón (RN-VEN-04), garantizando la prevención de doble submit (RN-VEN-07) y preservando intacto el borrador ante respuestas `409 Conflict` o `422 Unprocessable Entity` (RN-VEN-08 / Casos de prueba G-04 y G-06).

## What Changes

- **Modelos y Persistencia Transaccional en Backend**:
  - Definición del modelo SQLAlchemy `Venta` en `backend/src/db/models/venta.py` (`id` PK, `cliente_id` FK a `clientes.id`, `fecha` TIMESTAMP WITH TIME ZONE DEFAULT `now()`, `total` NUMERIC(12, 2) NOT NULL) y relación uno-a-muchos con `VentaRenglon`.
  - Definición del modelo SQLAlchemy `VentaRenglon` en `backend/src/db/models/venta_renglon.py` (`id` PK, `venta_id` FK a `ventas.id` ondelete CASCADE, `libro_id` FK a `libros.id`, `cantidad` INT NOT NULL > 0, `precio_unitario` NUMERIC(10, 2) NOT NULL, `subtotal` NUMERIC(12, 2) NOT NULL).
  - Inclusión de modelos en `backend/src/db/models/__init__.py` y creación de la migración Alembic `003_create_ventas.py`.
  - Definición de schemas Pydantic en `backend/src/schemas/venta.py`:
    - `VentaRenglonCreate`: `{ libro_id: int, cantidad: int }` (`cantidad >= 1`).
    - `VentaCreate`: `{ cliente_id: int, renglones: list[VentaRenglonCreate] }` (al menos 1 renglón).
    - `VentaRenglonResponse`: `{ id: int, libro_id: int, titulo: str | None, cantidad: int, precio_unitario: float, subtotal: float }`.
    - `VentaResponse`: `{ id: int, cliente_id: int, cliente_nombre: str | None, fecha: datetime, total: float, renglones: list[VentaRenglonResponse] }`.
- **Endpoint Transaccional `POST /api/v1/ventas/`**:
  - Validación de existencia del `cliente_id` (retorna HTTP `409 Conflict` si no existe, RN-VEN-01).
  - Validación de unicidad de `libro_id` entre renglones (retorna HTTP `422 Unprocessable Entity` si hay duplicados, RN-VEN-04).
  - Validación de existencia de cada `libro_id` (retorna HTTP `409 Conflict` si algún libro no existe en catálogo, RN-VEN-01).
  - Congelamiento inmutable de precios unitarios: lectura del precio actual de cada libro desde `libros.precio`, cálculo atómico de `subtotal = cantidad * precio_unitario` y `total = sum(subtotales)` (RN-VEN-05, RN-VEN-06).
  - Persistencia atómica de encabezado `ventas` y líneas `ventas_renglones` en una única transacción de base de datos (`commit` o `rollback`).
  - Registro de rutas en `backend/src/api/router.py` bajo los prefijos `/ventas` y `/api/v1/ventas`.
- **Módulo Frontend de Ventas (`frontend/public/js/sales.js`)**:
  - Gestión del estado en memoria del borrador de venta: `borradorVenta = { cliente_id: null, renglones: [] }` (sin persistencia prematura en backend ni uso de `localStorage`).
  - Selección de cliente con validación visual y sincronización reactiva desde `GET /api/clientes/`.
  - Selector dinámico de libros poblado desde `GET /api/libros/`.
  - Agregado interactivo de renglones: verificación en cliente impidiendo duplicar el mismo libro en múltiples renglones (RN-VEN-04) y exigiendo `cantidad >= 1` (RN-VEN-03).
  - Edición reactiva del borrador: modificación de cantidades y eliminación de renglones con recálculo local informativo de subtotales y total provisorio.
  - Renderizado de la tabla `#tabla-renglones` y gestión del aviso `#renglones-listado-vacio`.
  - Despacho de la venta con prevención de dobles clics: deshabilitación inmediata del botón `#venta-confirmar` durante el vuelo de la promesa de red (RN-VEN-07).
  - Manejo amigable de respuestas:
    - `201 Created`: Despliegue de confirmación con importes oficiales devueltos por el backend, reseteo del borrador en memoria y limpieza de la tabla de renglones.
    - `409 Conflict` o `422 Unprocessable Entity`: Despliegue del mensaje de error del servidor en `#venta-feedback` y PRESERVACIÓN ESTRICTA del borrador en pantalla para que el operador pueda corregir cantidades o reemplazar ítems sin perder su trabajo (RN-VEN-08).
- **Integración en la UI (`frontend/public/js/app.js`)**:
  - Conexión del ciclo de vida de la vista de ventas con `sales.js`, integrando eventos de agregado, eliminación y confirmación.

## Capabilities

### New Capabilities
- `sales-management`: Gestión integral del dominio de ventas en backend y frontend: modelos relacionales inmutables `ventas` y `ventas_renglones`, endpoint atómico `POST /api/ventas/` con congelamiento de precios de catálogo, composición en memoria de borradores con validación de unicidad de renglones y cantidades positivas, prevención de doble confirmación y preservación resiliente del borrador ante errores (US-006, US-007, RN-VEN-01 a RN-VEN-08).

### Modified Capabilities
<!-- Ninguna especificación existente cambia sus requerimientos de contrato -->

## Impact

- **Backend**:
  - Nuevos modelos: `backend/src/db/models/venta.py`, `backend/src/db/models/venta_renglon.py`.
  - Nuevos schemas: `backend/src/schemas/venta.py`.
  - Nuevo endpoint: `backend/src/api/v1/endpoints/ventas.py`.
  - Nueva migración: `backend/alembic/versions/003_create_ventas.py`.
  - Modificados: `backend/src/db/models/__init__.py`, `backend/src/schemas/__init__.py`, `backend/src/api/router.py`.
  - Pruebas automáticas: `backend/tests/integration/test_ventas_api.py`, `backend/tests/unit/test_venta_models.py`, `backend/tests/unit/test_venta_schemas.py`.
- **Frontend**:
  - Nuevo módulo: `frontend/public/js/sales.js`.
  - Pruebas unitarias: `frontend/public/js/sales.test.js`.
  - Modificado: `frontend/public/js/app.js` (desacople de persistencia local estática y enlace con `sales.js`).
- **APIs**:
  - Contrato: `POST /api/ventas/` (y `/api/v1/ventas/`).
- **Casos de Prueba**:
  - Cumplimiento y verificación de **G-04** (registro exitoso de venta con 2 renglones) y **G-06** (rechazos 409/422 y preservación del borrador en memoria).
