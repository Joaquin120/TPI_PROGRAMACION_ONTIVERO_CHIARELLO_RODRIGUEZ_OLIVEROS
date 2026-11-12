# Design: C-04 Alta de Libros

## Context
Ver `proposal.md` para la motivación y `specs/frontend-book-creation/spec.md` para los requerimientos funcionales y escenarios.
Actualmente el frontend cuenta con el formulario `#form-alta-libro` en `frontend/public/index.html`, pero su envío está atado a arreglos locales en memoria (`app.js`), sin interactuar con los endpoints `POST /api/libros/`, `GET /api/editoriales/`, `GET /api/generos/` ni `GET /api/autores/{id}`.

## UI Mockups
- **Decision**: no (project policy)
- **Razón**: La política visual configurada en `.active-orchestrator-state.json` y `design-system/README.md` es `system-only`. Se reutilizan y extienden los estilos nativos existentes en `frontend/public/css/estilos.css`.

## Goals / Non-Goals

**Goals:**
- Conectar `#form-alta-libro` para poblar dinámicamente sus selectores desde `GET /api/editoriales/` y `GET /api/generos/`.
- Permitir la búsqueda y verificación de autores por ID mediante `GET /api/autores/{id}`, agregando autorías múltiples con rol y orden correlativo a una lista visual previa al envío.
- Validar en cliente: `precio > 0.00` (RN-LIB-02), `stock >= 0` (RN-LIB-03) y al menos un autor asociado (RN-LIB-04).
- Despachar `POST /api/libros/` con payload estructurado conteniendo metadatos y arreglo de autorías.
- Manejar exitosamente `201 Created` (reset de formulario, feedback y refresco reactivo del catálogo vía `cargarCatalogoApi()`).
- Manejar `409 Conflict` (ISBN duplicado, RN-LIB-01) y `422 Unprocessable Entity` mostrando el mensaje devuelto y preservando intactos los datos del formulario.
- Proveer en FastAPI los endpoints auxiliares y el endpoint transaccional de creación de libros.

**Non-Goals:**
- Implementar alta de clientes (corresponde a `C-05`).
- Implementar borrador de ventas (corresponde a `C-06`).
- Edición o borrado de libros existentes (fuera del alcance del TP).

## Decisions

### D1: Constructor Dinámico de Autorías Múltiples en Memoria Local del Formulario
- **Decisión**: El formulario mantiene un estado temporal de autorías `[{ autor_id, nombre, rol, orden }]`. Al ingresar un ID de autor, se consulta `GET /api/autores/{id}`; si existe, se muestra su nombre verificado y un botón para incorporarlo a la lista con un rol seleccionado (`autor`, `coautor`, `traductor`, `ilustrador`).
- **Razón**: Cumple estrictamente con la consigna del Ejercicio 2 («Para seleccionar autores, verificar cada ID con `GET /autores/{id}` y mostrar su nombre antes de agregarlo»).
- **Alternativas consideradas**: Select múltiple nativo tradicional. Descartado porque no permite validar existencia individual por ID ni asignar roles diferenciados por autor.

### D2: Preservación de Estado del Formulario ante Errores 409 y 422
- **Decisión**: Los bloques `catch (error)` en el cliente no invocarán `form.reset()` ni limpiarán el arreglo de autorías temporales. El mensaje devuelto por el backend (ej: «El ISBN ya se encuentra registrado») se renderiza en `#libros-feedback` con clase de error.
- **Razón**: Cumple con la regla dura #5 de `AGENTS.md` y la especificación de negocio RN-LIB-01, evitando la frustración del usuario de tener que reescribir todos los datos por un error en un único campo.

### D3: Transaccionalidad en `POST /libros/` en Backend
- **Decisión**: El endpoint backend recibe el schema `LibroCreate` con `{ titulo, isbn, precio, stock, editorial_id, genero_id, autores: [{ autor_id, rol, orden }] }`. En una única sesión asíncrona de base de datos se verifica unicidad de ISBN (o captura de `IntegrityError`), existencia de editorial, género y autores, insertando el libro y sus filas intermedias en `libros_autores`.
- **Razón**: Garantiza consistencia atómica en PostgreSQL: o se registra el libro con todas sus autorías o no se persiste nada.

### D4: Módulo de Lógica de Libros (`frontend/public/js/books.js`)
- **Decisión**: Encapsular la lógica del alta de libros, verificación de autores y validación en un módulo testeable `books.js`, conectado a `app.js` e `index.html`.
- **Razón**: Mantiene la arquitectura limpia, desacoplada y 100% testeable con `node:test`.

## Risks / Trade-offs

- **[Riesgo] El usuario intenta enviar sin autores agregados** → **Mitigación**: Validación local bloqueante antes del `fetch` que resalta la lista de autorías vacía e impide el envío HTTP innecesario.
- **[Riesgo] Errores de concurrencia con ISBN duplicado** → **Mitigación**: La base de datos posee un índice único en `libros.isbn`, por lo que ante cualquier colisión el backend atrapa la excepción y retorna un limpio `409 Conflict` con detalle comprensible.

