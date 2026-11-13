# Design: C-05 Alta de Clientes

## Context

Ver `proposal.md` para la justificación del cambio y el alcance de negocio (US-005, RN-CLI-01, RN-CLI-02 y caso de prueba G-03).
El proyecto cuenta con un backend FastAPI estructurado modularmente en `backend/src/api/v1/endpoints/`, modelos SQLAlchemy 2.0 asíncronos y migraciones Alembic. En el frontend, la arquitectura utiliza JavaScript ES6+ nativo sin dependencias externas, con un cliente HTTP centralizado (`frontend/public/js/api.js`) y módulos desacoplados para catálogo (`catalog.js`) y libros (`books.js`).

## Goals / Non-Goals

**Goals:**
- Implementar el modelo `Cliente` y su migración correspondiente en PostgreSQL (`id` PK, `nombre` VARCHAR(128), `email` VARCHAR(255) UNIQUE).
- Exponer los endpoints REST:
  - `POST /api/v1/clientes/`: alta de cliente retornando `201 Created` o `409 Conflict` ante email repetido.
  - `GET /api/v1/clientes/{id}`: consulta individual por identificador (retorna `200 OK` o `404 Not Found`).
  - `GET /api/v1/clientes/`: listado general de clientes registrados.
- Crear el módulo frontend `frontend/public/js/clients.js` desacoplado y testeable.
- Manejar la interacción en `#form-alta-cliente`, asegurando la validación sintáctica previa al envío y la preservación de los datos ante errores 409/422.
- Actualizar la tabla `#tabla-clientes` y sincronizar las opciones del selector `#venta-cliente` ante altas exitosas.
- Proveer suites de pruebas unitarias y de integración tanto para backend (pytest con SQLite/PostgreSQL async) como para frontend (Node test runner).

**Non-Goals:**
- Implementar la lógica de venta o creación de borradores (alcance reservado para C-06).
- Implementar eliminación o modificación de clientes (no requerido por las consignas ni por el caso G-03).
- Implementar paginación en el listado de clientes (el caso de evaluación G-03 y el seed contemplan volúmenes acotados).

## Decisions

### 1. Manejo de Unicidad de Email a Nivel Backend y Base de Datos (RN-CLI-01)
- **Decisión**: Validar la existencia previa del correo en la base de datos antes del `INSERT` mediante una consulta `select(Cliente).where(Cliente.email == email)`, y además capturar posibles colisiones concurrentes mediante `IntegrityError` en el `commit`. En ambos casos, elevar una excepción `HTTPException(status_code=409, detail="El correo electrónico ya se encuentra registrado")`.
- **Alternativas consideradas**:
  - *Depender únicamente de la excepción de base de datos*: Aunque funcional, la consulta previa permite un mensaje de diagnóstico más claro y desacoplado del driver de BD.
  - *Validar únicamente en cliente*: Inviable y peligroso; la integridad referencial y de unicidad debe garantizarse en el servidor.

### 2. Módulo Frontend `frontend/public/js/clients.js` Desacoplado
- **Decisión**: Estructurar la lógica de clientes en un archivo independiente `clients.js` que gestione su propio estado local (`estadoClientes = { clientes: [], enviando: false }`), exportando funciones puras y controladoras de DOM: `cargarClientes()`, `enviarAltaCliente()`, `consultarClientePorId()`, `renderizarTablaClientes()` e `inicializarEventosClientes()`.
- **Alternativas consideradas**:
  - *Escribir todo dentro de `app.js`*: Descartado para mantener la cohesión modular lograda en C-03 (`catalog.js`) y C-04 (`books.js`), facilitando además la ejecución de pruebas unitarias automatizadas con mocking del DOM.

### 3. Preservación del Formulario y Feedback No Destructivo (RN-CLI-01, RN-CLI-02)
- **Decisión**: Ante respuestas de error (`409 Conflict`, `422 Unprocessable Entity` o fallas de red), la función controladora de envío NO limpiará los elementos `<input>` (`#cliente-nombre`, `#cliente-email`). Solo se actualizará el elemento de estado `#clientes-feedback` con clases semánticas (`feedback-error` o `feedback-exito`) y mensaje explicativo. El formulario solo se reseteará (`form.reset()`) cuando el servidor confirme HTTP `201 Created`.
- **Alternativas consideradas**:
  - *Alertas nativas (`window.alert`)*: Descartado; degrada la accesibilidad y no cumple con las pautas de diseño visual del sistema.

### 4. Sincronización Reactiva del Selector de Ventas (`#venta-cliente`)
- **Decisión**: Al cargar inicialmente la vista de clientes y tras cada alta confirmada (`201 Created`), invocar una función helper que actualice el elemento `<select id="venta-cliente">`, agregando las opciones correspondientes a los clientes persistidos, de modo que cuando se habilite C-06 los clientes estén disponibles de inmediato.
- **Alternativas consideradas**:
  - *Delegar la recarga del selector exclusivamente a la vista de ventas*: Puede generar inconsistencias si el usuario crea un cliente y navega inmediatamente a ventas sin refrescar la página.

### 5. UI Mockups
- **Decisión**: `Decision: no (project policy)`
- **Justificación**: Conforme a la política del proyecto establecida en `.active-orchestrator-state.json` y `design-system/README.md` (`visual_design.mode: system-only`), los componentes visuales reutilizan y extienden la paleta semántica y estilos CSS nativos ya aprobados en el Sistema de Diseño, sin requerir mockups individuales por pantalla.

## Risks / Trade-offs

- **[Riesgo: Formato de Email divergente entre HTML5, Pydantic y Regex JS]** → **Mitigación**: Utilizar `EmailStr` en Pydantic v2 en el backend, y en cliente utilizar validación nativa (`input.checkValidity()`) complementada con un patrón regular estándar `^[^\s@]+@[^\s@]+\.[^\s@]+$` que garantice coherencia.
- **[Riesgo: Migración de base de datos en entornos existentes]** → **Mitigación**: Generar una nueva migración Alembic numerada (`002_create_clientes.py` o incremental) y asegurar que en pruebas con SQLite en memoria los metadatos de `Base.metadata.create_all` creen la tabla automáticamente.

## Migration Plan

1. Crear migración Alembic para la tabla `clientes`.
2. Incluir el router en `backend/src/api/router.py`.
3. Desplegar endpoints y ejecutar pruebas de regresión.
