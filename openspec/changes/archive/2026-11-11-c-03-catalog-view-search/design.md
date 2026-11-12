# Design: C-03 Catalog View and Search

## Context
Ver `proposal.md` para la motivación y `specs/frontend-catalog-view/spec.md` para los requerimientos funcionales y escenarios.
Actualmente el proyecto cuenta con:
1. `frontend/public/index.html` con estructura HTML base del catálogo del Primer Parcial.
2. `frontend/public/js/api.js` (implementado en `C-02`) con funciones `api.get(endpoint, params)`, normalización `/api/`, trailing slash y parsing de errores.
3. `backend/src/` con FastAPI y PostgreSQL base.

## UI Mockups
- **Decision**: no (project policy)
- **Razón**: La política del proyecto configurada en `.active-orchestrator-state.json` y `design-system/README.md` es `system-only`. Se reutilizan y extienden los estilos nativos de `frontend/public/css/estilos.css` definidos en el Primer Parcial sin requerir mockups individuales por pantalla.

## Goals / Non-Goals

**Goals:**
- Conectar la tabla del catálogo (`#tabla-catalogo`) en `frontend/public/index.html` para consumir dinámicamente `api.get('/libros/', { limit, offset, titulo })`.
- Implementar los 4 estados de UI (loading spinner, lista vacía, búsqueda sin coincidencias, error de transporte).
- Implementar paginación completa con controles Anterior/Siguiente y selector de límite.
- Búsqueda en vivo o por submit con reinicio automático de `offset = 0`.
- Implementar modal/panel accesible para visualizar autores (`GET /api/libros/{id}`).
- Asegurar que el backend disponga del router y schemas de libros con filtrado insensible a mayúsculas (`ILIKE`) para responder fielmente a los contratos.

**Non-Goals:**
- Implementar el formulario de alta de libros (corresponde a `C-04`).
- Implementar alta de clientes (corresponde a `C-05`).
- Implementar el carrito o borrador de ventas (corresponde a `C-06`).

## Decisions

### D1: Integración con Vanilla JS y Manipulación Segura del DOM
- **Decisión**: Utilizar JavaScript nativo modular (`app.js` importando o consumiendo `api.js`) y creación de nodos con `document.createElement` / `textContent` o plantillas sanitizadas para prevenir inyecciones XSS.
- **Razón**: La consigna prohíbe frameworks externos (React, Vue, etc.) y exige JS nativo compatible con navegadores modernos.
- **Alternativas consideradas**: Reemplazar todo el HTML con `innerHTML`. Descartado por riesgo de seguridad y fragilidad ante caracteres especiales en títulos.

### D2: Manejo de Estados Visuales mediante Atributos `hidden` y Clases CSS
- **Decisión**: Los contenedores `#catalogo-sin-resultados`, `#catalogo-listado-vacio`, `#catalogo-cargando` y `#catalogo-error` se gestionan mediante visibilidad reactiva (`element.hidden = false / true`), asegurando que solo uno de los estados especiales o la tabla esté visible.
- **Razón**: Máxima simplicidad, accesibilidad (respetado por lectores de pantalla) y compatibilidad con el maquetado semántico existente en `index.html`.

### D3: Búsqueda con Reinicio de Desplazamiento (`offset = 0`)
- **Decisión**: Al escribir o enviar el formulario de búsqueda, se establece inmediatamente `offset = 0`. Si el input está vacío, no se envía el parámetro `titulo` para obtener el listado completo paginado.
- **Razón**: Cumplir con la regla de negocio RN-LIB-07 y la consigna del Ejercicio 1.

### D4: Consulta Perezosa (*Lazy Load*) de Autores en Detalle Modal
- **Decisión**: La lista general `GET /api/libros/` provee los metadatos principales (título, ISBN, precio, editorial, género). Al presionar el botón «Ver autores» o «Detalle», se dispara `GET /api/libros/{id}` para obtener la relación completa de autorías y presentarlas en un modal.
- **Razón**: Cumple estrictamente con la consigna del Ejercicio 1 («Para ver los autores, consultar `GET /libros/{id}`») y optimiza el ancho de banda del listado principal.

### D5: Soporte Backend en `backend/src/api/v1/endpoints/libros.py`
- **Decisión**: Exponer `GET /libros/` (con parámetros `titulo: str | None`, `limit: int = 20`, `offset: int = 0`) y `GET /libros/{id}` en FastAPI, con consulta SQLAlchemy uniendo `editoriales`, `generos` y `libros_autores`.
- **Razón**: Garantizar que el frontend disponga de un contrato real contra PostgreSQL al ejecutar pruebas locales y en Docker Compose.

## Risks / Trade-offs

- **[Riesgo] Ausencia momentánea de base de datos en entorno de testing estático** → **Mitigación**: `api.js` ya maneja errores de red gracefully; los tests unitarios del frontend emulan respuestas con mocks de `fetch`, y en entorno integrado Docker Compose levanta PostgreSQL con el seed data.
- **[Riesgo] Rebote de peticiones rápidas en el buscador** → **Mitigación**: Implementar debounce de 300ms o disparar en el evento `submit` del formulario para no saturar la API.

