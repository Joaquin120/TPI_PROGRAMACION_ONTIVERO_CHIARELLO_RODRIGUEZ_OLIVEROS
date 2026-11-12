# Proposal: C-03 Catalog View and Search

## Why

Actualmente el frontend conserva la lógica preliminar del Primer Parcial basada en datos simulados y tablas estáticas, sin consumir la API REST del backend. Es necesario implementar la vista interactiva del Catálogo (Ejercicio 1 / US-001, US-002, US-003) conectada a través del cliente HTTP centralizado (`api.js`) para permitir la consulta, paginación, búsqueda por título y visualización de autores de los libros persistidos en el sistema.

## What Changes

- **Integración de Catálogo en UI (`frontend/public/index.html` y `app.js`)**: Conectar la vista de catálogo para consultar dinámicamente `GET /api/libros/?limit=20&offset=0` al montar la aplicación.
- **Renderizado Dinámico de Libros**: Mostrar título, ISBN, precio formateado en moneda local, nombre de la editorial y género. Si el género es nulo, renderizar explícitamente «Sin clasificar» (RN-LIB-06).
- **Paginación Dinámica**: Controles interactivos de paginación («Anterior» y «Siguiente»), selector configurable de tamaño de página (`limit` entre 1 y 100, default 20) y cálculo reactivo del desplazamiento (`offset`).
- **Búsqueda por Título**: Campo de búsqueda que consulta `GET /api/libros/?titulo={texto}&offset=0` con filtrado insensible a mayúsculas (`ILIKE`) y reinicio forzado a `offset = 0` ante cualquier cambio de filtro (RN-LIB-07).
- **Gestión de 4 Estados Visuales**: Indicadores explícitos y diferenciados en la interfaz para:
  1. Estado de carga (*loading spinner* / mensaje mientras la promesa está pendiente).
  2. Catálogo vacío (cuando el inventario no tiene registros).
  3. Búsqueda sin coincidencias («No se encontraron libros»).
  4. Error de conexión o falla de red (mensaje descriptivo ante errores HTTP o caída de servicio).
- **Detalle Modal y Consulta de Autores**: Inspección detallada al seleccionar un libro que dispara `GET /api/libros/{id}` para mostrar la lista completa de autores asociados, su orden y su rol de autoría (`autor`, `coautor`, `traductor`, `ilustrador`).
- **Endpoint Backend para Libros (soporte de contrato)**: Garantizar que el backend exponga `GET /api/v1/libros/` (con filtros `titulo`, `limit`, `offset`) y `GET /api/v1/libros/{id}` acorde a las especificaciones y seed data del modelo de datos.

## Capabilities

### New Capabilities
- `frontend-catalog-view`: Interfaz y lógica cliente para visualización, búsqueda insensible a mayúsculas, paginación dinámica, manejo de estados visuales y consulta detallada de autores para libros del catálogo.

### Modified Capabilities
<!-- Ninguna especificación existente cambia sus requerimientos de contrato -->

## Impact

- **Frontend**: `frontend/public/index.html`, `frontend/public/js/app.js`, estilos CSS para los estados de carga, paginación y modal de detalle.
- **Backend**: Verificación / adición de routers `libros` en `backend/src/api/v1/endpoints/libros.py` y schemas de respuesta asociados si no estaban expuestos.
- **APIs**: Consumo estricto con prefijo `/api/` y trailing slash: `GET /api/libros/?limit={limit}&offset={offset}&titulo={titulo}` y `GET /api/libros/{id}`.
- **Tests**: Pruebas unitarias/funcionales de renderizado, búsqueda, paginación y validación del caso de prueba G-01.

