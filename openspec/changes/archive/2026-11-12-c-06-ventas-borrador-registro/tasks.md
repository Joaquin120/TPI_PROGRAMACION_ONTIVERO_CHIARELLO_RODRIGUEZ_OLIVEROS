# Tasks: C-06 Ventas - Borrador y Registro

## 1. Modelos de Datos y Migraciones para Ventas (Backend)

- [x] 1.1 Definir los modelos SQLAlchemy `Venta` en `backend/src/db/models/venta.py` y `VentaRenglon` en `backend/src/db/models/venta_renglon.py` con relaciones foráneas a `clientes` y `libros`, registrándolos en `backend/src/db/models/__init__.py`.
- [x] 1.2 Definir los esquemas Pydantic `VentaCreate`, `VentaRenglonCreate`, `VentaResponse` y `VentaRenglonResponse` en `backend/src/schemas/venta.py` con validación de cantidad positiva y no duplicación de libros, exportándolos en `backend/src/schemas/__init__.py`.
- [x] 1.3 Crear la migración Alembic `003_create_ventas.py` para las tablas `ventas` y `ventas_renglones`, y verificar la creación y constraints con pruebas unitarias en `backend/tests/unit/test_venta_models.py` y `backend/tests/unit/test_venta_schemas.py`.

## 2. Endpoint Transaccional de Ventas (Backend API)

- [x] 2.1 Escribir suite de pruebas de integración TDD en `backend/tests/integration/test_ventas_api.py` verificando registro exitoso `POST /api/v1/ventas/` (201 Created) con congelamiento de precios unitarios (RN-VEN-05), rechazo por cliente o libro inexistente (409 Conflict, RN-VEN-01), y rechazo por libro duplicado o cantidades inválidas (422 Unprocessable Entity, RN-VEN-02, RN-VEN-04).
- [x] 2.2 Implementar el router de ventas en `backend/src/api/v1/endpoints/ventas.py` con el endpoint `POST /`, realizando verificación de existencia, cálculo oficial de subtotales y total, y persistencia atómica en una única transacción de base de datos.
- [x] 2.3 Registrar las rutas de ventas en `backend/src/api/router.py` bajo los prefijos `/ventas` y `/api/v1/ventas`, y verificar que la suite de integración en `test_ventas_api.py` pase en verde.

## 3. Módulo Frontend de Composición de Ventas (Frontend)

- [x] 3.1 Escribir suite de pruebas unitarias en `frontend/public/js/sales.test.js` testeando la composición del borrador en memoria, cálculo de subtotales, bloqueo de libro repetido (RN-VEN-04), eliminación de renglones, y despacho con deshabilitación de botón confirmación (RN-VEN-07).
- [x] 3.2 Implementar el módulo `frontend/public/js/sales.js` con las funciones `agregarRenglonVenta()`, `eliminarRenglonVenta()`, `calcularTotalVenta()`, `renderizarTablaRenglones()`, `enviarConfirmacionVenta()` e `inicializarEventosVentas()`.
- [x] 3.3 Conectar el módulo `sales.js` en `frontend/public/js/app.js` e `index.html`, vinculando los eventos de `#venta-agregar`, `#venta-confirmar`, eliminación de renglones y preservación del borrador ante respuestas de error 409/422 (RN-VEN-08).

## 4. Verificación Integral y Casos de Prueba G-04 y G-06

- [x] 4.1 Ejecutar la suite completa de pruebas de frontend (`node --test frontend/public/js/*.test.js`) y de backend (`pytest backend/tests`), verificando que no existan regresiones en el sistema.
- [x] 4.2 Validar de extremo a extremo los criterios de los casos de prueba G-04 (registro exitoso de venta con 2 renglones e importes oficiales devueltos) y G-06 (rechazos 409 por cliente inexistente, 422 por libro duplicado y preservación del borrador en pantalla).
