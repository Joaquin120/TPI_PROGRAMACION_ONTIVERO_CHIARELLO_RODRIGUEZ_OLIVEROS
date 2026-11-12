# Proposal: C-04 Alta de Libros

## Why

Actualmente el formulario de alta de libros en la interfaz continúa utilizando arreglos estáticos en memoria del navegador y simulación local del Primer Parcial, sin consumir la API REST ni reflejar los contratos y validaciones de negocio en PostgreSQL. Es necesario implementar la integración completa del alta de libros (Ejercicio 2A / US-004) mediante `POST /api/libros/`, con carga dinámica de editoriales y géneros, validación y asignación de autores por ID con sus respectivos roles y orden, garantizando la persistencia fidedigna y el manejo robusto de respuestas `201 Created`, `409 Conflict` (ISBN duplicado) y `422 Unprocessable Entity`.

## What Changes

- **Integración de Formulario de Alta de Libros (`#form-alta-libro`)**: Conectar los campos de título, ISBN, precio, stock, editorial, género y autores en `frontend/public/index.html` y la lógica modular en JavaScript nativo.
- **Carga Dinámica de Opciones de Clasificación**: Cargar dinámicamente las editoriales desde `GET /api/editoriales/` y los géneros desde `GET /api/generos/` al montar la vista, con opción nula para géneros («Sin clasificar»).
- **Selector Dinámico y Verificación de Autores**: Componente interactivo para agregar autores buscando o validando su ID mediante `GET /api/autores/{id}`, visualizando el nombre verificado antes de incorporarlo a la lista de autorías con su rol (`autor`, `coautor`, `traductor`, `ilustrador`) y orden correlativo (RN-LIB-04, RN-LIB-05).
- **Validaciones en Cliente**: Comprobación obligatoria antes del envío: precio estrictamente positivo (`precio > 0.00`, RN-LIB-02), stock no negativo (`stock >= 0`, RN-LIB-03), al menos una autoría asignada (`autores.length >= 1`, RN-LIB-04) y datos completos.
- **Envío Transaccional `POST /api/libros/`**: Despacho de la petición vía cliente HTTP centralizado con payload JSON conteniendo datos del libro y arreglo de autorías.
- **Manejo Amigable de Respuestas y Errores**:
  - `201 Created`: Despliegue de notificación de éxito, reseteo del formulario y actualización automática del catálogo interactivo.
  - `409 Conflict`: Visualización clara del mensaje devuelto por el servidor ante ISBN duplicado (RN-LIB-01) preservando todos los campos ingresados intactos.
  - `422 Unprocessable Entity`: Mensaje de error detallado ante violaciones de contrato sin pérdida de datos.
- **Soporte de Endpoints Backend**: Garantizar que la API exponga `POST /api/v1/libros/` (con validación de ISBN único y guardado en `libros_autores`), `GET /api/v1/editoriales/`, `GET /api/v1/generos/` y `GET /api/v1/autores/{id}` con sus respectivos modelos y schemas.

## Capabilities

### New Capabilities
- `frontend-book-creation`: Interfaz interactiva y controladores para la carga dinámica de catálogos auxiliares (editoriales, géneros, autores), validación local, configuración de autorías múltiples y registro de libros mediante `POST /api/libros/` con tratamiento resiliente de errores.

### Modified Capabilities
<!-- Ninguna especificación existente cambia sus requerimientos de contrato -->

## Impact

- **Frontend**: `frontend/public/index.html` (sección `#vista-libros`), `frontend/public/js/catalog.js` / nuevo módulo `frontend/public/js/books.js`, `frontend/public/js/app.js` y `frontend/public/css/estilos.css`.
- **Backend**: Endpoints en `backend/src/api/v1/endpoints/libros.py`, `editoriales.py`, `generos.py`, `autores.py`, schemas en `backend/src/schemas/libro.py` y pruebas asociadas.
- **APIs**: Contratos `GET /api/editoriales/`, `GET /api/generos/`, `GET /api/autores/{id}`, `POST /api/libros/`.
- **Casos de Prueba**: Cumplimiento y verificación del caso **G-02** (alta exitosa de libro y rechazo 409 por ISBN duplicado).

