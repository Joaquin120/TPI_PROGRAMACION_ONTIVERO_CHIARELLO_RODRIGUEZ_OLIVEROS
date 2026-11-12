# Tasks: C-05 Alta de Clientes

## 1. Modelo de Datos y Schemas (Backend)

- [x] 1.1 Definir el modelo SQLAlchemy `Cliente` en `backend/src/db/models/cliente.py` con campos `id` (PK), `nombre` (VARCHAR 128 NOT NULL) y `email` (VARCHAR 255 UNIQUE NOT NULL), registrándolo en `backend/src/db/models/__init__.py`.
- [x] 1.2 Definir los esquemas Pydantic `ClienteCreate` y `ClienteResponse` en `backend/src/schemas/cliente.py` con validación sintáctica de email (`EmailStr`) y exportarlos en `backend/src/schemas/__init__.py`.
- [x] 1.3 Crear y aplicar la migración Alembic para la tabla `clientes` y verificar la creación correcta de la tabla y restricciones mediante pruebas unitarias en `backend/tests/unit/test_models.py`.

## 2. Endpoints REST y Pruebas de API (Backend)

- [x] 2.1 Escribir suite de pruebas de integración TDD en `backend/tests/integration/test_clientes_api.py` verificando `POST /api/v1/clientes/` (201 Created), rechazo por email duplicado (409 Conflict, RN-CLI-01), errores de validación de contrato (422 Unprocessable Entity, RN-CLI-02), consulta `GET /api/v1/clientes/{id}` (200 OK y 404 Not Found) y listado `GET /api/v1/clientes/`.
- [x] 2.2 Implementar el router de clientes en `backend/src/api/v1/endpoints/clientes.py` con los endpoints `POST /`, `GET /{id}` y `GET /`, manejando `IntegrityError` y validaciones de negocio.
- [x] 2.3 Registrar las rutas de clientes en `backend/src/api/router.py` bajo los prefijos `/clientes` y `/api/v1/clientes`, y verificar que toda la suite de tests en `backend/tests/integration/test_clientes_api.py` pase en verde.

## 3. Módulo de Clientes e Interfaz Web (Frontend)

- [x] 3.1 Escribir suite de pruebas unitarias en `frontend/public/js/clients.test.js` cubriendo la validación sintáctica de email en cliente, el despacho a `api.post('/clientes/', ...)`, el reseteo de formulario ante 201 y la preservación intacta de campos ante 409 Conflict.
- [x] 3.2 Implementar el módulo `frontend/public/js/clients.js` con las funciones `validarEmail()`, `cargarClientes()`, `enviarAltaCliente()`, `consultarClientePorId()`, `renderizarTablaClientes()`, `sincronizarSelectorVentas()` e `inicializarEventosClientes()`.
- [x] 3.3 Conectar el módulo `clients.js` en `frontend/public/js/app.js` e `index.html`, vinculando el evento submit de `#form-alta-cliente`, la actualización reactiva del feedback en `#clientes-feedback` y el refresco del selector `#venta-cliente`.

## 4. Verificación Integral y Caso de Prueba G-03

- [x] 4.1 Ejecutar la suite completa de pruebas de frontend (`node --test frontend/public/js/*.test.js`) y de backend (`pytest backend/tests`), verificando que no existan regresiones.
- [x] 4.2 Validar de extremo a extremo los criterios del caso de prueba G-03: registro de cliente exitoso (201), rechazo ante email duplicado (409) con preservación del formulario, y consulta de cliente por ID.
