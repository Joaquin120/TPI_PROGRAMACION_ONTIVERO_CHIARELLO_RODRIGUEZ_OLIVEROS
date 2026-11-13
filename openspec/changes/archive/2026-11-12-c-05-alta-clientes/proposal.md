# Proposal: C-05 Alta de Clientes

## Why

Actualmente la sección de clientes en la interfaz del frontend opera con datos estáticos simulados del Primer Parcial y no interactúa con la API REST ni con la base de datos PostgreSQL. Asimismo, el backend no expone aún los endpoints ni el modelo de datos persistente para la entidad `clientes`. Es indispensable implementar el flujo integral de gestión y alta de clientes (Ejercicio 2B / US-005) para registrar compradores con `nombre` y `email` único (`POST /api/clientes/`), consultar clientes por su identificador (`GET /api/clientes/{id}`) y listar clientes existentes (`GET /api/clientes/`), garantizando el tratamiento resiliente de errores `409 Conflict` por email duplicado y validación de contrato `422`, preparando los cimientos requeridos para el posterior registro transaccional de ventas (C-06).

## What Changes

- **Modelo y Persistencia de Clientes en Backend**:
  - Definición del modelo SQLAlchemy `Cliente` en `backend/src/db/models/cliente.py` sobre la tabla `clientes` (`id` PK, `nombre` VARCHAR(128) NOT NULL, `email` VARCHAR(255) UNIQUE NOT NULL).
  - Inclusión de `Cliente` en `backend/src/db/models/__init__.py` y generación/aplicación de migración Alembic (o sincronización de schema) para la tabla `clientes`.
  - Definición de schemas Pydantic en `backend/src/schemas/cliente.py` (`ClienteCreate`, `ClienteResponse`) con validación de sintaxis de email (`EmailStr`) y normalización.
- **Endpoints de Clientes en Backend**:
  - `POST /api/v1/clientes/`: Registro atómico de cliente. Validación de unicidad de `email` (RN-CLI-01); retorna HTTP `201 Created` con el cliente persistido o HTTP `409 Conflict` si el correo ya está registrado, y `422 Unprocessable Entity` ante violaciones de contrato (RN-CLI-02).
  - `GET /api/v1/clientes/{id}`: Consulta individual por ID; retorna HTTP `200 OK` con datos del cliente o HTTP `404 Not Found` si no existe.
  - `GET /api/v1/clientes/`: Listado de clientes para poblar la vista y los selectores de ventas.
  - Registro de rutas en `backend/src/api/router.py` con prefijos `/clientes` y `/api/v1/clientes`.
- **Módulo de Clientes en Frontend (`frontend/public/js/clients.js`)**:
  - Implementación modular en ES6+ Modules para la gestión de clientes, integrando el cliente HTTP centralizado (`api.js`).
  - Validación sintáctica en cliente de formato de email y completitud de campos antes del despacho de red (RN-CLI-02).
  - Conexión del formulario `#form-alta-cliente` en `#vista-clientes`: captura de `submit`, feedback de carga (*loading*) y despacho de `POST /api/clientes/`.
  - Tratamiento amigable de respuestas:
    - `201 Created`: Despliegue de mensaje de éxito en `#clientes-feedback`, reseteo del formulario, actualización de la tabla `#tabla-clientes` y sincronización con el selector `#venta-cliente`.
    - `409 Conflict`: Visualización clara del mensaje de advertencia («El correo electrónico ya se encuentra registrado») en `#clientes-feedback`, PRESERVANDO intactos los valores en los inputs para permitir su corrección (RN-CLI-01).
    - `422 Unprocessable Entity`: Notificación de error de validación sin pérdida de datos en los campos.
  - Carga y renderizado reactivo del listado de clientes en `#tabla-clientes`, gestionando el estado vacío (`#clientes-listado-vacio`).
  - Función de consulta y verificación de cliente por identificador `GET /api/clientes/{id}`.
- **Integración con la UI Principal (`frontend/public/js/app.js` e `index.html`)**:
  - Inicialización del módulo de clientes al navegar a `#vista-clientes` o al cargar la aplicación.
  - Actualización reactiva de las listas desplegables de clientes en la vista de ventas.

## Capabilities

### New Capabilities
- `client-management`: Gestión integral de clientes en backend y frontend: modelo de datos con email único, endpoints REST (`POST /api/clientes/`, `GET /api/clientes/{id}`, `GET /api/clientes/`), formulario con validación sintáctica, preservación de datos ante conflicto 409 y consulta de cliente por ID (US-005, RN-CLI-01, RN-CLI-02).

### Modified Capabilities
<!-- Ninguna especificación existente cambia sus requerimientos de contrato -->

## Impact

- **Backend**:
  - Nuevos archivos: `backend/src/db/models/cliente.py`, `backend/src/schemas/cliente.py`, `backend/src/api/v1/endpoints/clientes.py`.
  - Archivos modificados: `backend/src/db/models/__init__.py`, `backend/src/schemas/__init__.py`, `backend/src/api/router.py`, migraciones Alembic.
  - Tests automáticos: tests unitarios y de integración para endpoints de clientes (`backend/tests/integration/test_clientes_api.py`).
- **Frontend**:
  - Nuevo módulo: `frontend/public/js/clients.js` y sus tests asociados `frontend/public/js/clients.test.js`.
  - Archivos modificados: `frontend/public/index.html` (ajustes de accesibilidad/IDs si aplica) y `frontend/public/js/app.js` (importación e inicialización).
- **APIs**:
  - Nuevos contratos: `POST /api/clientes/`, `GET /api/clientes/{id}`, `GET /api/clientes/`.
- **Casos de Prueba**:
  - Cumplimiento y verificación del caso de prueba **G-03** (alta exitosa 201, rechazo 409 por email repetido y consulta por ID).
