# Tasks: C-07 Ventas - Historial, Detalle e Invariante de Precio Histórico

> Nota de estado inicial (Opción A): la base funcional de `C-07` y las migraciones ya se encuentran en el working tree sin commitear; durante `/opsx-apply` se verificará esa base, se aplicarán las correcciones pendientes de `app.js` y se completarán los tests faltantes.

## 1. Migraciones y Backend (Historial, Detalle y PATCH Libros)

- [x] 1.1 Verificar el encadenamiento Alembic (`backend/alembic.ini`, `backend/alembic/versions/002b_create_catalogo_libros.py` y `backend/alembic/versions/003_create_ventas.py`), ejecutando `python -m pytest -p no:cacheprovider tests/integration/test_migrations.py -v` sin errores.
- [x] 1.2 Verificar `LibroUpdate` en `backend/src/schemas/libro.py` y `PATCH /libros/{libro_id}` en `backend/src/api/v1/endpoints/libros.py` (`404`, `409` ISBN, `422`), validando con `python -m pytest -p no:cacheprovider tests/unit/test_libro_schemas.py -v`.
- [x] 1.3 Verificar `GET /ventas/` (`limit` `1..100`, `offset >= 0`, orden descendente) y `GET /ventas/{venta_id}` (`200`/`404`) en `backend/src/api/v1/endpoints/ventas.py`, y ampliar `backend/tests/integration/test_ventas_api.py` (incluyendo soporte de `Editorial`/`Genero` en `FakeVentasAsyncSession`) para cubrir `422` en parámetros de paginación de `GET /ventas/` y `PATCH /libros/{id}` sobre `editorial_id`, `genero_id`, `genero_id: null` y payload `{}`; verificar ejecutando `python -m pytest -p no:cacheprovider tests/integration/test_ventas_api.py -v`.

## 2. Frontend (Historial, Detalle Inmutable, Comprobante y Ajuste de Precio)

- [x] 2.1 Verificar `frontend/public/js/history.js` (`GET /api/ventas/` paginado y `GET /api/ventas/{id}` en solo lectura sin `localStorage`) y ampliar `frontend/public/js/history.test.js` para cubrir errores de red/`404`, click en `.historial-ver-detalle` de `crearFilaVentaHistorial` e `inicializarEventosHistorial`; verificar con `node --test frontend/public/js/history.test.js`.
- [x] 2.2 Verificar edición inline de cantidad y panel oficial `#venta-confirmada-detalle` en `frontend/public/js/sales.js`, agregando prueba explícita de `renderizarVentaConfirmada` en `frontend/public/js/sales.test.js`; verificar con `node --test frontend/public/js/sales.test.js`.
- [x] 2.3 Verificar listado `#tabla-libros` y formulario `#form-actualizar-precio-libro` en `frontend/public/js/books.js` y agregar pruebas unitarias en `frontend/public/js/books.test.js` para `renderizarTablaLibrosRegistrados` y `enviarActualizarPrecioLibro` (validación local, `PATCH /libros/{id}` exitoso, errores HTTP y bloqueo de botón); verificar con `node --test frontend/public/js/books.test.js`.
- [x] 2.4 Corregir la orquestación en `frontend/public/js/app.js` (manteniendo limpios `frontend/public/index.html` y `frontend/public/css/estilos.css` sin `localStorage` ni datos simulados) para: (a) cargar `#venta-libro`, `#libro-precio-editar-id` y `#tabla-libros` desde `/libros/` (`limit=100, offset=0` sin filtro `titulo`) de forma independiente al filtro/paginación de `#vista-catalogo`, y (b) reiniciar `estadoHistorial.offset = 0` tras confirmar una venta antes de recargar `#tabla-historial`; verificar mediante pruebas automatizadas en `node --test`.

## 3. Validación Integral de C-07

- [x] 3.1 Ejecutar las suites completas `python -m pytest -p no:cacheprovider tests -v` (en `backend/`) y `node --test frontend/public/js/*.test.js` con 0 fallos, y ejecutar `openspec validate "c-07-ventas-historial-detalle" --strict --json` verificando `passed: 1, failed: 0`.

## Workflow follow-up

- Sincronizar el delta spec de `sales-management` mediante `/opsx-sync` hacia `openspec/specs/sales-management/spec.md`.
- Archivar el change mediante `/opsx-archive c-07-ventas-historial-detalle`, marcar `[x]` únicamente `C-07` en `CHANGES.md` y crear el commit único exclusivo de `C-07`.
